"""Mainframe/api.py - API endpoints: status, projects, chat_url, health.

Contract:
- status -> per-channel agent ping + cdp probe.
- projects -> scan Projects/ and project/ for ROADMAP.html.
- chat_url -> logs/session_<CH>.json url field.
- health -> simple uptime.
"""
from __future__ import annotations

import json
import socket
import time
import urllib.request
from typing import Any

from Core.config import Config

_START_TS = time.time()


def _agent_ping(port: int, timeout: float = 0.7) -> dict | None:
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/ping" % port, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def _cdp_up(port: int, timeout: float = 0.7) -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % port, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _probe_channel(ch) -> dict:
    ping = _agent_ping(ch.agent_port)
    return {
        "name": ch.name,
        "prefix": ch.prefix,
        "model": ch.model,
        "cdp": ch.cdp_port,
        "agent": ch.agent_port,
        "agent_port": ch.agent_port,
        "cdp_port": ch.cdp_port,
        "agent_alive": bool(ping),
        "cdp_alive": _cdp_up(ch.cdp_port),
    }


def status(cfg: Config, path: str, body: dict) -> dict:
    from Mainframe import health
    h = health.collect(cfg)
    matrix = h["matrix"]
    channels = {}
    for L, row in matrix.items():
        merged = dict(row) if isinstance(row, dict) else {}
        ch = cfg.channels.get(L)
        if ch is not None:
            merged.update({
                "name": ch.name, "prefix": ch.prefix, "model": ch.model,
                "cdp": ch.cdp_port, "agent": ch.agent_port,
                "agent_port": ch.agent_port, "cdp_port": ch.cdp_port,
            })
        # 7C: expose boolean flags for tests and UI (True/False, not None)
        merged["agent_alive"] = bool(merged.get("agent"))
        merged["cdp_alive"] = bool(merged.get("content"))
        # 8C B-09: auth_status + chat_url for login button
        merged["auth_status"] = merged.get("auth_status") or "unknown"
        merged["chat_url"] = "https://chat.deepseek.com/" if ch and ch.model == "deepseek" else "https://chat.qwen.ai/"
        # 8C B-09: auth_status + chat_url for login button
        merged["auth_status"] = merged.get("auth_status") or "unknown"
        merged["chat_url"] = "https://chat.deepseek.com/" if ch and ch.model == "deepseek" else "https://chat.qwen.ai/"
        # 8C B-09: auth_status + chat_url for login button
        merged["auth_status"] = merged.get("auth_status") or "unknown"
        merged["chat_url"] = "https://chat.deepseek.com/" if ch and ch.model == "deepseek" else "https://chat.qwen.ai/"
        channels[L] = merged
    return {"ok": True, "ts": time.time(), "channels": channels,
            "alerts": h.get("alerts", []),
            "root": str(cfg.root), "version": cfg.version}


def projects(cfg: Config, path: str, body: dict) -> dict:
    out = []
    for base_rel in ("Projects", "project"):
        base = cfg.path(base_rel)
        if not base.exists():
            continue
        for d in sorted(base.iterdir()):
            if not d.is_dir():
                continue
            rm = d / "ROADMAP.html"
            if rm.exists():
                try:
                    st = rm.stat()
                    out.append({"name": d.name, "base": base_rel,
                                "url": "/roadmap/" + d.name,
                                "mtime": st.st_mtime, "size": st.st_size})
                except Exception:
                    pass
    return {"ok": True, "projects": out}


def chat_url(cfg: Config, path: str, body: dict) -> dict:
    parts = path.rstrip("/").split("/")
    letter = parts[-1].upper() if parts else ""
    if letter not in cfg.channels:
        return {"ok": False, "error": "unknown channel", "channel": letter}
    p = cfg.path("logs", "session_%s.json" % letter)
    if not p.exists():
        return {"ok": False, "error": "no session file", "channel": letter}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"ok": False, "error": "bad json", "detail": str(e)}
    return {"ok": True, "channel": letter,
            "url": d.get("chat_url") or d.get("url") or "",
            "start": d.get("start", "")}


def health(cfg: Config, path: str, body: dict) -> dict:
    return {"ok": True, "ts": time.time(),
            "uptime": round(time.time() - _START_TS, 1),
            "version": cfg.version}

def telemetry(cfg: Config, path: str, body: dict) -> dict:
    """Phase 4: telemetry for mnemo — last entry + count per channel from live.json.

    Client polls this every 2s, detects count delta, and animates a link
    from agent to the target block on each new op.
    """
    out = {}
    for L in cfg.letters:
        live = cfg.channel_path(L, "logs", "live.json")
        if not live.exists():
            out[L] = {"count": 0, "last": None}
            continue
        try:
            data = json.loads(live.read_text(encoding="utf-8"))
        except Exception:
            out[L] = {"count": 0, "last": None}
            continue
        entries = data.get("entries") or []
        out[L] = {
            "count": len(entries),
            "last": entries[-1] if entries else None,
            "updated": data.get("updated"),
            "paused": data.get("paused", False),
        }
    return {"ok": True, "channels": out, "now": time.time()}
