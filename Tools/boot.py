"""Tools/boot.py - orchestrate v5 stack: Mainframe + Chrome + Bridge per channel.

Usage:
  python C:/JewAI/Tools/boot.py --channel C          # boot Chrome C + bridge C
  python C:/JewAI/Tools/boot.py --channel C --no-chrome
  python C:/JewAI/Tools/boot.py --server              # boot Mainframe (8670)
  python C:/JewAI/Tools/boot.py --all --dry-run

Safety:
- Never kills foreign processes. Only reports what is running.
- Mainframe: if 8670 already busy -> skip (report who).
- Chrome: uses Tools/launcher (idempotent: if CDP up, skip).
- Bridge: spawns Bridge/run.py --channel <CH> detached (pythonw, no window).
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from Core.config import load as load_config
from Tools.launcher import launch, wait_cdp, _cdp_up


def _tcp(port: int, timeout: float = 0.4) -> bool:
    s = socket.socket(); s.settimeout(timeout)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def _pythonw() -> str:
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        cand = exe[:-len("python.exe")] + "pythonw.exe"
        if Path(cand).exists():
            return cand
    return exe


def _detached_flags() -> int:
    if sys.platform != "win32":
        return 0
    return subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP


def _port_pid(port: int) -> int | None:
    try:
        r = subprocess.run(["netstat", "-ano", "-p", "tcp"],
                           capture_output=True, text=True, timeout=8,
                           encoding="utf-8", errors="replace",
                           creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        for ln in (r.stdout or "").splitlines():
            if f":{port}" in ln and "LISTENING" in ln:
                parts = ln.split()
                if parts and parts[-1].isdigit():
                    return int(parts[-1])
    except Exception:
        pass
    return None


def boot_server(cfg, dry: bool) -> dict:
    busy = _tcp(cfg.chat_port)
    out = {"target": "server", "port": cfg.chat_port, "busy_before": busy}
    if busy:
        pid = _port_pid(cfg.chat_port)
        out.update({"ok": False, "reason": "port busy", "pid": pid})
        return out
    if dry:
        out.update({"ok": True, "dry": True})
        return out
    args = [_pythonw(), str(ROOT / "Mainframe" / "server.py")]
    p = subprocess.Popen(args, cwd=str(ROOT), stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=_detached_flags())
    # wait for bind
    for _ in range(40):
        time.sleep(0.25)
        if _tcp(cfg.chat_port):
            out.update({"ok": True, "pid": p.pid})
            return out
    out.update({"ok": False, "pid": p.pid, "reason": "port not opened in 10s"})
    return out


def boot_chrome(cfg, letter: str, dry: bool) -> dict:
    ch = cfg.channel(letter)
    if _cdp_up(ch.cdp_port):
        return {"target": "chrome:" + letter, "cdp": ch.cdp_port, "ok": True, "already": True}
    if dry:
        return {"target": "chrome:" + letter, "cdp": ch.cdp_port, "ok": True, "dry": True}
    r = launch(cfg, letter, no_proxy=True, dry=False)
    return {"target": "chrome:" + letter, "cdp": ch.cdp_port, "ok": bool(r.get("ok")), "pid": r.get("pid")}


def boot_bridge(cfg, letter: str, dry: bool) -> dict:
    ch = cfg.channel(letter)
    if not _cdp_up(ch.cdp_port):
        return {"target": "bridge:" + letter, "ok": False, "reason": "no cdp"}
    if dry:
        return {"target": "bridge:" + letter, "ok": True, "dry": True}
    args = [_pythonw(), str(ROOT / "Bridge" / "run.py"), "--channel", letter]
    p = subprocess.Popen(args, cwd=str(ROOT), stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=_detached_flags())
    return {"target": "bridge:" + letter, "ok": True, "pid": p.pid}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", choices=["A", "B", "C", "D", "E", "F"])
    ap.add_argument("--server", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--no-chrome", action="store_true")
    ap.add_argument("--no-bridge", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cfg = load_config()

    results = []
    if a.server or a.all:
        results.append(boot_server(cfg, a.dry_run))
    channels = []
    if a.channel:
        channels = [a.channel]
    elif a.all:
        channels = list(cfg.channels.keys())
    for L in channels:
        if not a.no_chrome:
            results.append(boot_chrome(cfg, L, a.dry_run))
        if not a.no_bridge:
            results.append(boot_bridge(cfg, L, a.dry_run))

    print(json.dumps({"results": results}, ensure_ascii=False, indent=1))
    return 0 if all(r.get("ok") for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())