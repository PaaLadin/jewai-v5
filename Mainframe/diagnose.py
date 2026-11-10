"""Mainframe/diagnose.py - real health check (replaces stub).

Contract:
- for each channel: agent /ping, cdp /json/version, Bridge alive (spawned.json),
  ledger watermark age, live.json age, lastId age.
- returns {"ok": bool_overall, "channels": {L: {...}}, "ts": ...}

Why: BUG-019 (11C). Stub said OK even when Bridge worker was dead.
"""
from __future__ import annotations

import json
import socket
import time
import urllib.request
from typing import Any

from Core.config import Config


def _tcp(port: int, timeout: float = 0.4) -> bool:
    s = socket.socket()
    s.settimeout(timeout)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def _ping(port: int, timeout: float = 0.7) -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/ping" % port, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _json_up(port: int, timeout: float = 0.7) -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % port, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _file_age(path) -> float | None:
    try:
        if not path.exists():
            return None
        return round(time.time() - path.stat().st_mtime, 1)
    except Exception:
        return None


def _bridge_alive(cfg: Config, L: str) -> dict:
    # registry из launchpad / logs/runtime/spawned.json
    p = cfg.path("logs", "runtime", "spawned.json")
    try:
        d = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception:
        d = {}
    info = d.get("bridge:" + L) or {}
    pid = info.get("pid")
    if not pid:
        return {"alive": False, "pid": None, "source": "registry"}
    # process alive?
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, int(pid))
        if not h:
            return {"alive": False, "pid": pid, "source": "registry"}
        try:
            code = ctypes.c_ulong()
            ok = k.GetExitCodeProcess(h, ctypes.byref(code))
            alive = bool(ok) and code.value == 259
            return {"alive": alive, "pid": pid, "source": "registry"}
        finally:
            k.CloseHandle(h)
    except Exception:
        return {"alive": False, "pid": pid, "source": "registry"}


def _ledger_age(cfg: Config, L: str) -> dict:
    p = cfg.channel_path(L, "logs", "ledger_%s.json" % L)
    age = _file_age(p)
    wm = None
    try:
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            wm = d.get("watermark")
    except Exception:
        pass
    return {"path": str(p), "age_s": age, "watermark": wm}


def collect(cfg: Config) -> dict:
    out = {}
    ok_overall = True
    for L in cfg.letters:
        ch = cfg.channels.get(L)
        if ch is None:
            continue
        agent = _ping(ch.agent_port)
        cdp = _json_up(ch.cdp_port)
        br = _bridge_alive(cfg, L)
        led = _ledger_age(cfg, L)
        live = _file_age(cfg.channel_path(L, "logs", "live.json"))
        ch_ok = agent and cdp and br.get("alive", False)
        if not ch_ok:
            ok_overall = False
        out[L] = {
            "ok": ch_ok,
            "agent": agent,
            "cdp": cdp,
            "bridge": br,
            "ledger": led,
            "live_age_s": live,
        }
    return {"ok": ok_overall, "ts": time.time(), "channels": out,
            "note": "real health check (11C), replaces stub"}
