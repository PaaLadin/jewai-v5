"""Tools/guard.py - Mutual rescue timer for critical operations.

### WHAT THIS SCRIPT DOES
When an agent is about to perform a dangerous operation (e.g., editing Bridge/daemon.py
or reloading the Chrome extension), it can get stuck or lose connection.
To prevent this, the agent arms a "guard" (a timer).
If the operation succeeds, the agent calls `guard.py done`, which disarms the timer.
If the operation takes longer than the timeout and no `done` signal arrives,
the guard wakes up and sends a [GUARD-ALERT] message to a partner agent.
The partner agent is then responsible for rescuing the stuck agent.

### HOW IT WORKS
1. `guard.py start` writes the armed state to a file and spawns a detached child process.
2. The child process (`guard.py check`) sleeps for `timeout` seconds.
3. After sleeping, the child checks if `guard.py done` was called (by looking for a signal file).
4. If the signal is missing, the child kicks the partner agent and logs the alert.

### PARTNER SELECTION
A -> B, B -> A, C -> A, D -> A.
(E and F are excluded because they do not participate in rebirth).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Resolve ROOT dynamically to work both in Sandbox and in jewai.
def _find_root(start: Path) -> Path:
    p = start.resolve()
    for _ in range(8):
        if (p / "Core" / "config.py").is_file():
            return p
        if p.parent == p:
            break
        p = p.parent
    return start.parent

HERE = Path(__file__).resolve().parent
ROOT = _find_root(HERE)
sys.path.insert(0, str(ROOT))

from Core.config import load as load_config

# Global paths for state files.
GUARD_DIR = ROOT / "logs" / "guard"
SIGNAL = GUARD_DIR / "guard_signal.txt"
ARMED = GUARD_DIR / "guard_armed.json"

# --- COMMANDS: START and DONE ---

def _ensure_dir() -> None:
    """Ensure the guard logs directory exists."""
    GUARD_DIR.mkdir(parents=True, exist_ok=True)

def cmd_start(target: int, timeout: int, label: str) -> int:
    """Arms the guard timer.
    1. Saves the current state to ARMED file.
    2. Deletes any old SIGNAL file.
    3. Spawns a detached `guard.py check` process to wait in the background.
    """
    _ensure_dir()
    
    # Save state
    data = {"target": target, "timeout": timeout, "label": label,
            "armed_at": time.time(), "iso": time.strftime("%Y-%m-%d %H:%M:%S")}
    ARMED.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # Clear old signal
    if SIGNAL.exists():
        try:
            SIGNAL.unlink()
        except Exception:
            pass
            
    # Spawn detached checker
    args = [sys.executable, str(Path(__file__).resolve()),
            "check", "--target", str(target), "--timeout", str(timeout),
            "--label", label]
            
    flags = 0
    if os.name == "nt":
        flags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        
    subprocess.Popen(args, cwd=str(ROOT), creationflags=flags,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("armed target=%d timeout=%d label=%s" % (target, timeout, label))
    return 0

def cmd_done() -> int:
    """Signals successful completion. The background checker will see this and exit quietly."""
    _ensure_dir()
    SIGNAL.write_text(json.dumps({"ts": time.time(),
                                  "iso": time.strftime("%Y-%m-%d %H:%M:%S")}),
                      encoding="utf-8")
    print("done")
    return 0

# --- COMMAND: CHECK (Executed in background) ---

def _partner_for(cfg, target: int) -> str | None:
    """Determines which partner agent to kick based on the target CDP port.
    A -> B, B -> A, C -> A, D -> A.
    E/F are excluded (no rebirth)."""
    ch = cfg.channel_by_cdp(target)
    if not ch:
        return None
    L = ch.letter
    if L == "A":
        return "B" if "B" in cfg.channels else None
    if L in ("B", "C", "D"):
        return "A" if "A" in cfg.channels else None
    return None

def cmd_check(target: int, timeout: int, label: str) -> int:
    """Waits for the timeout and sends an alert if the operation didn't finish.
    1. Sleeps for `timeout` seconds.
    2. Checks if the SIGNAL file exists and is recent.
    3. If no signal, finds the partner agent and sends a kick.
    4. Logs the alert to guard_alerts.jsonl.
    """
    # Wait for the operation to finish
    time.sleep(timeout)
    
    # Check for completion signal
    if SIGNAL.exists():
        try:
            j = json.loads(SIGNAL.read_text(encoding="utf-8"))
            # If signal was created within the last 5 seconds, consider it valid
            if j.get("ts", 0) >= time.time() - timeout - 5:
                print("signal ok")
                return 0
        except Exception:
            pass
            
    # Signal missing or too old -> need to alert
    cfg = load_config()
    partner = _partner_for(cfg, target)
    
    msg = ("[GUARD-ALERT] timeout=%d target=%d label=%s no-done-signal. "
           "Run RESCUE: ping agent, read panel, recover_chat if content dead." %
           (timeout, target, label))
           
    # Send kick to partner if we found one
    if partner:
        kick = ROOT / "Tools" / "kick.py"
        try:
            subprocess.run([sys.executable, str(kick), "--to", partner,
                            "--from", "SYS", "--text", msg],
                           capture_output=True, text=True, timeout=30, cwd=str(ROOT))
        except Exception as e:
            print("kick err: %r" % e)
            
    # Log the alert for history
    GUARD_DIR.mkdir(parents=True, exist_ok=True)
    with (GUARD_DIR / "guard_alerts.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "target": target, "label": label,
                            "partner": partner}, ensure_ascii=False) + "\n")
    print("alert sent partner=%s" % partner)
    return 0

# --- MAIN ENTRY POINT ---
# This script is used to arm a 'watchdog' for dangerous operations.
# When you do 'guard.py start', it spawns a detached child process ('guard.py check').
# The child process sleeps for the specified timeout. If 'guard.py done' is not called
# before the timeout expires, the child process kicks the partner agent with a
# [GUARD-ALERT] message, asking them to perform a rescue.

def main() -> int:
    ap = argparse.ArgumentParser(description="Mutual rescue timer")
    subparsers = ap.add_subparsers(dest="command", required=True)

    # 1. Command to arm the timer
    p_start = subparsers.add_parser("start", help="Arm the guard timer")
    p_start.add_argument("--target", type=int, required=True, help="CDP port to watch")
    p_start.add_argument("--timeout", type=int, default=180, help="Seconds before alert")
    p_start.add_argument("--label", default="dangerous-op", help="Description of operation")

    # 2. Command to disarm the timer (operation succeeded)
    subparsers.add_parser("done", help="Signal successful completion")

    # 3. Command executed by the detached child process
    p_check = subparsers.add_parser("check", help="Internal: background wait and alert")
    p_check.add_argument("--target", type=int, required=True)
    p_check.add_argument("--timeout", type=int, required=True)
    p_check.add_argument("--label", default="dangerous-op")

    a = ap.parse_args()

    if a.command == "start":
        return cmd_start(a.target, a.timeout, a.label)
    elif a.command == "done":
        return cmd_done()
    elif a.command == "check":
        return cmd_check(a.target, a.timeout, a.label)
    return 1

if __name__ == "__main__":
    sys.exit(main())

