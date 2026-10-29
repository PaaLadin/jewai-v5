"""svc.py - service controller for v5 (watchdog, recovery, autorestart).

Per-channel services: watchdog (personal ALIVE), recovery (panel F5 guard).
Global service: autorestart (checks flags+ledger+operator activity, reboots hung).

State files: Profiles/<L>/logs/svc_<kind>_<L>.json
Pid files:   Profiles/<L>/logs/svc_<kind>_<L>.pid

Usage:
  python Tools/svc.py start --channel A --kind watchdog --interval 300 --threshold 3
  python Tools/svc.py stop  --channel A --kind watchdog
  python Tools/svc.py status --channel A
  python Tools/svc.py start --kind autorestart --interval 600
  python Tools/svc.py status
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

KINDS_PER_CHANNEL = ("watchdog", "recovery")
KINDS_GLOBAL = ("autorestart",)
ALL_KINDS = KINDS_PER_CHANNEL + KINDS_GLOBAL

SCRIPT_BY_KIND = {
    "watchdog": "Tools/watchdog.py",
    "recovery": "Tools/recovery.py",
    "autorestart": "Tools/autorestart.py",
}


def _state_path(cfg, kind: str, channel: str | None) -> Path:
    if channel:
        return cfg.channel_path(channel, "logs", "svc_%s_%s.json" % (kind, channel))
    return cfg.path("logs", "svc", "svc_%s.json" % kind)


def _pid_path(cfg, kind: str, channel: str | None) -> Path:
    if channel:
        return cfg.channel_path(channel, "logs", "svc_%s_%s.pid" % (kind, channel))
    return cfg.path("logs", "svc", "svc_%s.pid" % kind)


def _read_json(p: Path, default):
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(p: Path, d) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)


def _pid_alive(pid: int) -> bool:
    if not pid:
        return False
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process -Id %d -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id" % pid],
            capture_output=True, text=True, timeout=10,
        )
        return bool(r.stdout.strip())
    except Exception:
        return False


def _pythonw() -> str:
    py = sys.executable
    if py.lower().endswith("python.exe"):
        cand = py[:-10] + "pythonw.exe"
        if os.path.exists(cand):
            return cand
    return py


def _spawn(cfg, kind: str, channel: str | None, extra_args: list[str]) -> int:
    script = ROOT / SCRIPT_BY_KIND[kind]
    if not script.exists():
        raise FileNotFoundError("script not found: %s" % script)
    args = [_pythonw(), str(script)]
    if channel:
        args += ["--channel", channel]
    args += extra_args
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
    env = os.environ.copy()
    env["JEWAI_CONFIG"] = str(cfg.root / "config.json")
    p = subprocess.Popen(args, cwd=str(cfg.root), env=env, creationflags=flags,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return p.pid


def cmd_start(args) -> int:
    cfg = load_config()
    kind = args.kind.lower()
    ch = (args.channel or "").upper() if args.channel else None
    if kind in KINDS_PER_CHANNEL and not ch:
        print(json.dumps({"ok": False, "error": "channel required for " + kind}))
        return 2
    if kind in KINDS_GLOBAL and ch:
        print(json.dumps({"ok": False, "error": "channel not allowed for " + kind}))
        return 2

    pid_file = _pid_path(cfg, kind, ch)
    st_file = _state_path(cfg, kind, ch)
    existing = _read_json(pid_file, {})
    if existing and _pid_alive(int(existing.get("pid", 0))):
        print(json.dumps({"ok": True, "already": True, "pid": existing["pid"]}))
        return 0

    extra = []
    if kind == "watchdog":
        extra += ["--interval", str(int(args.interval or 300)),
                  "--threshold", str(int(args.threshold or 3))]
    elif kind == "recovery":
        extra += ["--cooldown", str(int(args.cooldown or 300)),
                  "--interval", str(int(args.interval or 60))]
    elif kind == "autorestart":
        extra += ["--interval", str(int(args.interval or 600))]

    pid = _spawn(cfg, kind, ch, extra)
    _write_json(pid_file, {"pid": pid, "kind": kind, "channel": ch,
                           "started": time.time(), "by": "svc.start"})
    _write_json(st_file, {"state": "on", "pid": pid, "by": "svc.start",
                          "at": time.time()})
    print(json.dumps({"ok": True, "pid": pid, "kind": kind, "channel": ch}))
    return 0


def cmd_stop(args) -> int:
    cfg = load_config()
    kind = args.kind.lower()
    ch = (args.channel or "").upper() if args.channel else None
    pid_file = _pid_path(cfg, kind, ch)
    st_file = _state_path(cfg, kind, ch)
    existing = _read_json(pid_file, {})
    pid = int(existing.get("pid", 0)) if existing else 0
    alive = _pid_alive(pid)
    if alive:
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Stop-Process -Id %d -Force -ErrorAction SilentlyContinue" % pid],
                           capture_output=True, text=True, timeout=10)
        except Exception:
            pass
    if pid_file.exists():
        pid_file.unlink(missing_ok=True)
    _write_json(st_file, {"state": "off", "by": "svc.stop", "at": time.time(),
                          "reason": "killed" if alive else "no_proc"})
    print(json.dumps({"ok": True, "was_running": alive, "pid": pid}))
    return 0


def cmd_status(args) -> int:
    cfg = load_config()
    out = {"channel": args.channel, "services": {}}
    letters = [args.channel.upper()] if args.channel else list(cfg.letters)
    for L in letters:
        if not L:
            continue
        for kind in KINDS_PER_CHANNEL:
            pid_file = _pid_path(cfg, kind, L)
            st_file = _state_path(cfg, kind, L)
            pid_d = _read_json(pid_file, {})
            st_d = _read_json(st_file, {})
            pid = int(pid_d.get("pid", 0)) if pid_d else 0
            alive = _pid_alive(pid)
            out["services"].setdefault(L, {})[kind] = {
                "state": "on" if alive else ("off" if not st_d else st_d.get("state", "off")),
                "pid": pid if alive else None,
                "alive": alive,
            }
    for kind in KINDS_GLOBAL:
        pid_file = _pid_path(cfg, kind, None)
        pid_d = _read_json(pid_file, {})
        pid = int(pid_d.get("pid", 0)) if pid_d else 0
        out["services"][kind] = {"state": "on" if _pid_alive(pid) else "off",
                                 "pid": pid if _pid_alive(pid) else None}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["start", "stop", "status"])
    ap.add_argument("--channel", default=None)
    ap.add_argument("--kind", default="watchdog", choices=list(ALL_KINDS))
    ap.add_argument("--interval", type=int, default=None)
    ap.add_argument("--threshold", type=int, default=None)
    ap.add_argument("--cooldown", type=int, default=None)
    a = ap.parse_args()
    if a.cmd == "start":
        return cmd_start(a)
    if a.cmd == "stop":
        return cmd_stop(a)
    return cmd_status(a)


if __name__ == "__main__":
    sys.exit(main())