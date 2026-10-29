"""cleanup_test.py - kill processes started from a test install folder.

Only kills processes whose command line contains the exact --root path
(Python agents/bridge/mainframe, Chrome profiles under root).
Refuses to touch the source project or DeepSeek.

Usage:
  python Tools/cleanup_test.py --root C:\\JewAI_test_20261029 --dry-run
  python Tools/cleanup_test.py --root C:\\JewAI_test_20261029 --yes

Exit codes:
  0 - ok (killed or nothing to kill)
  2 - refused (protected root or no config.json)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import time

PROTECTED_ROOTS = [
    r"C:\jewai",
    r"C:\DeepSeek",
    r"C:\JewAI",
]


def _list_procs() -> list[dict]:
    ps = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.Name -eq 'python.exe' -or $_.Name -eq 'pythonw.exe' -or $_.Name -eq 'chrome.exe' } | "
        "Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    )
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=30,
                           encoding="utf-8", errors="replace")
    except Exception as e:
        print("ERR powershell:", e)
        return []
    txt = (r.stdout or "").strip()
    if not txt:
        return []
    try:
        data = json.loads(txt)
    except Exception:
        return []
    if isinstance(data, dict):
        data = [data]
    return [d for d in data if isinstance(d, dict)]


def _norm(p: str) -> str:
    return p.replace("/", "\\").rstrip("\\").lower()


def _find_by_root(procs: list[dict], root: str) -> tuple[list, list]:
    root_n = _norm(root)
    agents = []
    chromes = []
    for p in procs:
        cl = (p.get("CommandLine") or "")
        cl_n = _norm(cl)
        if root_n not in cl_n:
            continue
        name = (p.get("Name") or "").lower()
        pid = int(p.get("ProcessId") or 0)
        if not pid:
            continue
        # skip self and any other cleanup_test.py to avoid suicide
        if "cleanup_test.py" in cl:
            continue
        rec = {"pid": pid, "name": name, "cmd": cl[:200]}
        if name == "chrome.exe":
            chromes.append(rec)
        else:
            agents.append(rec)
    return agents, chromes


def _find_by_port(port: int) -> list[int]:
    try:
        r = subprocess.run(["netstat", "-ano", "-p", "TCP"],
                           capture_output=True, text=True, timeout=15,
                           encoding="utf-8", errors="replace")
    except Exception:
        return []
    pids = []
    needle = ":%d" % port
    for line in (r.stdout or "").splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        if parts[3] != "LISTENING":
            continue
        if not parts[1].endswith(needle):
            continue
        try:
            pids.append(int(parts[4]))
        except Exception:
            pass
    return pids


def _kill(pid: int) -> bool:
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Stop-Process -Id %d -Force -ErrorAction SilentlyContinue" % pid],
                       capture_output=True, text=True, timeout=10)
        return True
    except Exception:
        return False


def _alive(pid: int) -> bool:
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Get-Process -Id %d -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id" % pid],
                           capture_output=True, text=True, timeout=10)
        return bool((r.stdout or "").strip())
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()

    try:
        root = str(pathlib.Path(a.root).resolve())
    except Exception as e:
        print("ERR bad --root:", e)
        return 2

    # safety
    for prot in PROTECTED_ROOTS:
        try:
            if pathlib.Path(prot).resolve() == pathlib.Path(root):
                print("REFUSE: %s is a protected source project (not a test copy)." % root)
                return 2
        except Exception:
            pass

    if not (pathlib.Path(root) / "config.json").exists():
        print("REFUSE: no config.json in %s - not a JewAI install?" % root)
        return 2

    try:
        cfg = json.loads((pathlib.Path(root) / "config.json").read_text(encoding="utf-8"))
    except Exception as e:
        print("REFUSE: config.json unreadable:", e)
        return 2
    chat_port = cfg.get("chat_port")

    print("Root:      %s" % root)
    print("Chat port: %s" % chat_port)
    print()

    procs = _list_procs()
    agents, chromes = _find_by_root(procs, root)

    mainframe_pids = set()
    if chat_port:
        mainframe_pids = set(_find_by_port(int(chat_port)))

    print("=== Mainframe (port %s) ===" % chat_port)
    if mainframe_pids:
        for pid in sorted(mainframe_pids):
            print("  pid %d (listening on %d)" % (pid, chat_port))
    else:
        print("  (none)")

    print()
    print("=== Agents / bridge / tools (%d) ===" % len(agents))
    for rec in agents:
        print("  pid %d %s" % (rec["pid"], rec["cmd"]))

    print()
    print("=== Chrome under %s ===" % root)
    if chromes:
        for rec in chromes:
            print("  pid %d %s" % (rec["pid"], rec["cmd"]))
    else:
        print("  (none)")

    to_kill = []
    if mainframe_pids:
        to_kill += sorted(mainframe_pids)
    to_kill += [r["pid"] for r in agents]
    to_kill += [r["pid"] for r in chromes]
    to_kill = list(dict.fromkeys(to_kill))

    if not to_kill:
        print()
        print("Nothing to kill. Folder can be deleted.")
        return 0

    print()
    print("Total to kill: %d process(es)" % len(to_kill))

    if a.dry_run:
        print("DRY-RUN: not killing.")
        return 0

    if not a.yes:
        ans = input("Kill these processes? [y/N]: ").strip().lower()
        if ans not in ("y", "yes", "д", "да"):
            print("Aborted.")
            return 0

    print()
    killed = 0
    for pid in to_kill:
        ok = _kill(pid)
        alive = _alive(pid)
        if ok and not alive:
            killed += 1
            print("  killed pid %d" % pid)
        elif alive:
            print("  FAIL pid %d still alive" % pid)

    time.sleep(1)
    survivors = [r for r in agents + chromes if _alive(r["pid"])]
    print()
    print("Killed: %d / %d" % (killed, len(to_kill)))
    if survivors:
        print("Survivors (retry or kill manually):")
        for r in survivors:
            print("  pid %d %s" % (r["pid"], r["cmd"]))
        return 1
    print("All clean. Folder %s can be deleted." % root)
    return 0


if __name__ == "__main__":
    sys.exit(main())