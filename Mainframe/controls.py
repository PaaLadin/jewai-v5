"""controls.py - meeting/pause_all + fs + logs + roadmap state.

Contract (AUDIT §28.5-28.7, rewritten):
- meeting: file logs/runtime/meeting.json {on: bool}. POST {on}.
- pause_all: file logs/runtime/pause_all.json {on: bool}. POST {on}.
- fs: GET /fs/<rel> -> file inside ROOT (403 on escape). Dir -> index.html.
- logs: GET /api/logs?name=chat|server -> tail last 200 lines.
- roadmap: GET /api/roadmap?name=X, POST /api/roadmap {name, state} -> logs/roadmap_state/<name>.json
"""
from __future__ import annotations

import json
import time
import urllib.parse as _up
from pathlib import Path
from typing import Any

from Core.config import Config


def _state_path(cfg: Config, name: str) -> Path:
    p = cfg.path("logs", "runtime", name + ".json")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _read_json(p: Path, default: Any) -> Any:
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(p: Path, d: Any) -> None:
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def _get_flag(cfg: Config, name: str) -> dict:
    d = _read_json(_state_path(cfg, name), {})
    return {"ok": True, name: bool(d.get("on")), "ts": d.get("ts")}


def _set_flag(cfg: Config, name: str, on: bool) -> dict:
    d = {"on": bool(on), "ts": time.time()}
    _write_json(_state_path(cfg, name), d)
    return {"ok": True, name: bool(on), "ts": d["ts"]}


def meeting_get(cfg: Config) -> dict:
    return _get_flag(cfg, "meeting")


def meeting_set(cfg: Config, body: dict) -> dict:
    return _set_flag(cfg, "meeting", bool(body.get("on")))


def pause_all_get(cfg: Config) -> dict:
    return _get_flag(cfg, "pause_all")


def pause_all_set(cfg: Config, body: dict) -> dict:
    return _set_flag(cfg, "pause_all", bool(body.get("on")))


def fs_read(cfg: Config, path: str) -> tuple[int, bytes, str]:
    """Returns (code, body_bytes, ctype). 403 on escape, 404 if missing."""
    rel = _up.unquote(path[4:]).replace("\\", "/").lstrip("/")
    try:
        target = (cfg.root / rel).resolve()
        target.relative_to(cfg.root.resolve())
    except Exception:
        return 403, json.dumps({"error": "forbidden"}).encode(), "application/json"
    if target.is_dir():
        target = target / "index.html"
    if not target.exists() or not target.is_file():
        return 404, json.dumps({"error": "not found", "path": rel}).encode(), "application/json"
    ext = target.suffix.lower()
    ct = {
        ".html": "text/html; charset=utf-8", ".htm": "text/html; charset=utf-8",
        ".js": "application/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
        ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml",
        ".png": "image/png", ".jpg": "image/jpeg", ".gif": "image/gif",
        ".md": "text/plain; charset=utf-8", ".txt": "text/plain; charset=utf-8",
    }.get(ext, "application/octet-stream")
    try:
        return 200, target.read_bytes(), ct
    except Exception as e:
        return 500, json.dumps({"error": str(e)[:120]}).encode(), "application/json"


def logs_tail(cfg: Config, name: str) -> dict:
    cands = {
        "chat": cfg.path("logs", "council", "chat.jsonl"),
        "server": cfg.path("logs", "runtime", "server.log"),
        "agent": cfg.path("logs", "runtime", "agent.log"),
        "svc": cfg.path("logs", "runtime", "svc.log"),
    }
    p = cands.get(name or "chat")
    if not p:
        return {"ok": False, "error": "unknown log", "name": name}
    if not p.exists():
        return {"ok": True, "name": name, "content": "(empty)"}
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        return {"ok": True, "name": name, "content": "\n".join(lines[-200:])}
    except Exception as e:
        return {"ok": False, "name": name, "error": str(e)[:120]}


def roadmap_get(cfg: Config, name: str) -> dict:
    p = cfg.path("logs", "roadmap_state", (name or "game") + ".json")
    return _read_json(p, {})


def roadmap_set(cfg: Config, body: dict) -> dict:
    name = body.get("name", "game")
    state = body.get("state", {})
    p = cfg.path("logs", "roadmap_state", name + ".json")
    p.parent.mkdir(parents=True, exist_ok=True)
    _write_json(p, state)
    return {"ok": True, "file": str(p), "keys": len(state)}