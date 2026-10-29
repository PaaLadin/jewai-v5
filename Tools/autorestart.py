"""autorestart.py - global service: detects hung agents and restarts them.

Contract:
- Loop every --interval seconds (default 600).
- For each channel with flag "enabled" (config or Profiles/<L>/enabled.flag):
  1. Check agent /ping (HTTP 8666+i).
  2. Check CDP (9122+i).
  3. Check ledger movement: mtime of Profiles/<L>/logs/ledger_<L>.json.
  4. If no movement for --ledger-stale seconds AND agent isn't replying:
     a. check operator typing in that channel (avoid reboot mid-conversation).
     b. if idle: restart via Bridge/run.py --channel L (stop then start).
- Log every action to logs/svc/autorestart.log.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from Core.config import load as load_config  # noqa: E402


def _log(p: Path, msg: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write("[%s] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))


def _agent_alive(port: int, token: str, timeout: float = 2.0) -> bool:
    try:
        import urllib.request
        req = urllib.request.Request("http://127.0.0.1:%d/ping" % port,
                                     headers={"X-Token": token})
        urllib.request.urlopen(req, timeout=timeout).read()
        return True
    except Exception:
        return False


def _cdp_alive(port: int) -> bool:
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:%d/json/version" % port, timeout=2).read()
        return True
    except Exception:
        return False


def _ledger_mtime(cfg, L: str) -> float:
    p = cfg.channel_path(L, "logs", "ledger_%s.json" % L)
    if not p.exists():
        return 0.0
    return p.stat().st_mtime


def _operator_typing(cdp_port: int) -> bool:
    try:
        from Bridge.cdp import connect
        cdp = connect(cdp_port)
        try:
            expr = ("(() => { const ts = document.querySelectorAll('textarea');"
                    "for (const t of ts) { if (t.value && t.value.trim().length > 0 && !t.readOnly) return 'busy'; }"
                    "return 'idle'; })()")
            return cdp.eval_expr(expr) == "busy"
        finally:
            try: cdp.close()
            except Exception: pass
    except Exception:
        return False


def _spawn_agent(cfg, L: str) -> int:
    env = os.environ.copy()
    env["JEWAI_CONFIG"] = str(cfg.root / "config.json")
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
    py = sys.executable
    if py.lower().endswith("python.exe"):
        cand = py[:-10] + "pythonw.exe"
        if os.path.exists(cand):
            py = cand
    run_py = cfg.path("Bridge", "run.py")
    p = subprocess.Popen([py, str(run_py), "--channel", L],
                         cwd=str(cfg.root), env=env, creationflags=flags,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return p.pid


def _kill_agent(cfg, L: str) -> None:
    try:
        ps = ("Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe'\" | "
              "Where-Object { $_.CommandLine -like '*Bridge\\run.py*--channel %s*' } | "
              "Select-Object -ExpandProperty ProcessId" % L)
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=15)
        for pid in (r.stdout or "").split():
            if pid.isdigit():
                subprocess.run(["powershell", "-NoProfile", "-Command",
                                "Stop-Process -Id %s -Force -ErrorAction SilentlyContinue" % pid],
                               capture_output=True, text=True, timeout=10)
    except Exception:
        pass


def _channel_enabled(cfg, L: str) -> bool:
    flag = cfg.channel_path(L, "enabled.flag")
    if flag.exists():
        try:
            return flag.read_text(encoding="utf-8").strip().lower() not in ("0", "off", "false", "")
        except Exception:
            return True
    return True  # default: enabled


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=600)
    ap.add_argument("--ledger-stale", type=int, default=600)
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()

    cfg = load_config()
    token = ""
    tok_file = cfg.path(".agent_token")
    if tok_file.exists():
        token = tok_file.read_text(encoding="utf-8").strip()
    log_path = cfg.path("logs", "svc", "autorestart.log")

    _log(log_path, "autorestart start interval=%ds stale=%ds" % (a.interval, a.ledger_stale))

    while True:
        now = time.time()
        for L in cfg.letters:
            if not _channel_enabled(cfg, L):
                continue
            ch = cfg.channel(L)
            agent_ok = _agent_alive(ch.agent_port, token)
            cdp_ok = _cdp_alive(ch.cdp_port)
            lm = _ledger_mtime(cfg, L)
            age = now - lm if lm else -1

            if agent_ok and cdp_ok and (age < 0 or age < a.ledger_stale):
                continue  # healthy

            if age >= 0 and age < a.ledger_stale and agent_ok:
                continue  # ledger has movement recently

            _log(log_path, "%s: agent_ok=%s cdp_ok=%s ledger_age=%s" %
                 (L, agent_ok, cdp_ok, ("%.0fs" % age) if age >= 0 else "never"))

            # typing guard
            if cdp_ok and _operator_typing(ch.cdp_port):
                _log(log_path, "%s: operator typing, skip restart" % L)
                continue

            # restart
            _log(log_path, "%s: restarting agent" % L)
            _kill_agent(cfg, L)
            time.sleep(2)
            pid = _spawn_agent(cfg, L)
            _log(log_path, "%s: agent restarted pid=%d" % (L, pid))
            time.sleep(3)

        if a.once:
            return 0
        time.sleep(max(60, a.interval))


if __name__ == "__main__":
    sys.exit(main())