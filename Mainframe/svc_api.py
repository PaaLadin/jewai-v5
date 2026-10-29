"""Mainframe/svc_api.py - /api/svc endpoint.

Contract (from AUDIT section 28.5):
- POST {channel, kind, action} where kind in (watchdog, recovery), action in (start, stop).
- Delegates to svc.py (start/stop) in C:/DeepSeek/sandbox/svc.py.
- Returns {ok, channel, kind, action, rc, out, err, watchdog, recovery}.

Note: uses subprocess.run, not import. svc.py is the legacy service controller.
For v5, if svc.py is unavailable, returns error (no fake success).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from Core.config import Config

# 11B: Services not yet ported to v5. Use local Tools/svc.py when available.
_SVC = Path(__file__).resolve().parent.parent / "Tools" / "svc.py"


def _nw() -> int:
    if sys.platform != "win32":
        return 0
    return subprocess.CREATE_NO_WINDOW


def _read_state(cfg: Config, ch: str, kind: str) -> bool:
    p = cfg.path("logs", "svc", ("%s_%s.json" % (kind, ch)))
    if not p.exists():
        return False
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d.get("state") == "on"
    except Exception:
        return False


def handle(cfg: Config, channel: str, kind: str, action: str, extra: dict | None = None) -> dict[str, Any]:
    ch = (channel or "").upper()
    kd = (kind or "").lower()
    ac = (action or "").lower()
    if ch not in cfg.channels:
        return {"ok": False, "error": "bad channel", "channel": ch}
    if kd not in ("watchdog", "recovery"):
        return {"ok": False, "error": "bad kind", "kind": kd}
    if ac not in ("start", "stop"):
        return {"ok": False, "error": "bad action", "action": ac}
    if not _SVC.exists():
        return {"ok": False, "error": "svc.py not found", "path": str(_SVC)}

    args = [sys.executable, str(_SVC), ac, "--channel", ch, "--kind", kd]
    if ac == "start":
        ex = extra or {}
        if kd == "watchdog":
            args += ["--interval", str(int(ex.get("interval", 300))),
                     "--threshold", str(int(ex.get("threshold", 3)))]
        else:
            args += ["--cooldown", str(int(ex.get("cooldown", 300)))]

    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30,
                           encoding="utf-8", errors="replace", creationflags=_nw())
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
    except Exception as e:
        return {"ok": False, "error": type(e).__name__ + ": " + str(e)[:200]}

    wd = _read_state(cfg, ch, "watchdog")
    rec = _read_state(cfg, ch, "recovery")
    return {
        "ok": r.returncode == 0,
        "channel": ch, "kind": kd, "action": ac,
        "rc": r.returncode,
        "out": out[-400:], "err": err[-400:],
        "watchdog": wd, "recovery": rec,
    }