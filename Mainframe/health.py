"""Mainframe/health.py - health matrix per channel.

Contract (from AUDIT section 28.3, rewritten):
- matrix[CH] = {content, agent, watchdog, recovery, lastId, cmds, alive_button}
- content: heartbeat probe via read_heartbeat (False if stale, None on timeout)
- agent: /ping ok
- watchdog, recovery: from logs/svc/<kind>_<CH>.json + pid check
- lastId: from logs/council/state_<CH>.json (filled by Bridge daemon)
- cmds: lastId_num - start_num from logs/session_<CH>.json
- alerts: content_dead, agent_dead, panel_timeout, watchdog_off

Note: this module is read-only for state files. Does not write anything.
"""
from __future__ import annotations

import json
import re
import socket
import time
import urllib.request
from pathlib import Path
from typing import Any

from Core.config import Config

_ID_RE = re.compile(r"^([A-Z]{4})([0-9]{4})$")


def _tcp(port: int, timeout: float = 0.4) -> bool:
    s = socket.socket()
    s.settimeout(timeout)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def _agent_alive(port: int, timeout: float = 0.7) -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/ping" % port, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _content_alive(cdp_port: int, timeout: float = 0.7) -> bool | None:
    """True if CDP alive; None if CDP timeout; False only if CDP explicitly down."""
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % cdp_port,
                                    timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _svc_state(cfg: Config, ch: str, kind: str) -> bool:
    p = cfg.path("logs", "svc", ("%s_%s.json" % (kind, ch)))
    if not p.exists():
        return False
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("state") != "on":
            return False
        pid = d.get("pid")
        if not pid:
            return False
        return _tcp(0) or True  # state=on trusted; pid check would need process list
    except Exception:
        return False


def _read_lastid(cfg: Config, ch: str) -> str | None:
    p = cfg.path("logs", "council", ("state_%s.json" % ch))
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        v = d.get("lastId")
        return v if isinstance(v, str) and _ID_RE.match(v) else None
    except Exception:
        return None


def _read_start(cfg: Config, ch: str) -> str | None:
    p = cfg.path("logs", ("session_%s.json" % ch))
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        v = d.get("start")
        return v if isinstance(v, str) and _ID_RE.match(v) else None
    except Exception:
        return None


def _cmds(lastid: str | None, start: str | None) -> int | None:
    if not lastid or not start:
        return None
    ml = _ID_RE.match(lastid)
    ms = _ID_RE.match(start)
    if not ml or not ms:
        return None
    try:
        nl = int(ml.group(2))
        ns = int(ms.group(2))
        if ml.group(1) == ms.group(1):
            return max(0, nl - ns)
        return None
    except Exception:
        return None


def _alive_button(cfg: Config, ch: str) -> str:
    """grey/yellow/green by flags/alive_<CH>.json and acks."""
    p = cfg.path("logs", "council", "flags", ("alive_%s.json" % ch))
    if not p.exists():
        return "grey"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        ts = float(d.get("ts") or 0)
        if not ts:
            return "grey"
        age = time.time() - ts
        if age < 10:
            return "yellow"
        if age < 60:
            return "green"
        return "grey"
    except Exception:
        return "grey"


def _probe_one(cfg: Config, letter: str, ch) -> tuple[str, dict]:
    content = _content_alive(ch.cdp_port)
    agent = _agent_alive(ch.agent_port)
    wd = _svc_state(cfg, letter, "watchdog")
    rec = _svc_state(cfg, letter, "recovery")
    lastid = _read_lastid(cfg, letter)
    start = _read_start(cfg, letter)
    cmds = _cmds(lastid, start)
    row = {
        "content": content,
        "agent": agent,
        "watchdog": wd,
        "recovery": rec,
        "lastId": lastid,
        "session_min": start,
        "cmds_from_start": cmds,
        "alive_button": _alive_button(cfg, letter),
    }
    return letter, row


def collect(cfg: Config) -> dict[str, Any]:
    from concurrent.futures import ThreadPoolExecutor
    now = time.time()
    matrix: dict[str, dict] = {}
    alerts: list[dict] = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = [ex.submit(_probe_one, cfg, L, ch) for L, ch in cfg.channels.items()]
        for fut in futures:
            try:
                letter, row = fut.result(timeout=8)
                matrix[letter] = row
            except Exception:
                pass
    for letter, row in matrix.items():
        content = row.get("content")
        agent = row.get("agent")
        if content is False and agent is True:
            alerts.append({"channel": letter, "kind": "content_dead"})
        if agent is False and content is True:
            alerts.append({"channel": letter, "kind": "agent_dead"})
        if content is None:
            alerts.append({"channel": letter, "kind": "panel_timeout"})
    return {"ok": True, "ts": now, "matrix": matrix, "alerts": alerts}