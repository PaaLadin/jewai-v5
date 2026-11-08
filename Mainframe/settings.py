"""Mainframe/settings.py - adapter/model settings per channel.

9C (2026-11-09): gear in panel -> select adapter for each channel.
Writes model field in config.json channels.<L>.model.
Valid adapters: deepseek, qwen, alice, google.

API:
- get_all(cfg) -> {adapters: [...], channels: {A: model, B: model, ...}}
- set_adapter(cfg, channel, model) -> {ok, channel, model, restart_required}
- reload_adapters() -> [deepseek, qwen, alice, google]
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from Core.config import Config

VALID_ADAPTERS = ("deepseek", "qwen", "alice", "google")


def reload_adapters() -> list[str]:
    return list(VALID_ADAPTERS)


def _cfg_path(cfg: Config) -> Path:
    return cfg.path("config.json")


def _read_cfg(cfg: Config) -> dict:
    p = _cfg_path(cfg)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_cfg(cfg: Config, data: dict) -> None:
    p = _cfg_path(cfg)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def get_all(cfg: Config) -> dict:
    data = _read_cfg(cfg)
    chans = data.get("channels") or {}
    models = {L: (chans.get(L) or {}).get("model", "deepseek") for L in cfg.letters}
    return {
        "ok": True,
        "adapters": reload_adapters(),
        "channels": models,
    }


def set_adapter(cfg: Config, channel: str, model: str) -> dict:
    ch = (channel or "").upper()
    md = (model or "").lower()
    if ch not in cfg.letters:
        return {"ok": False, "error": "bad channel", "channel": ch}
    if md not in VALID_ADAPTERS:
        return {"ok": False, "error": "bad adapter", "adapter": md,
                "allowed": list(VALID_ADAPTERS)}
    data = _read_cfg(cfg)
    chans = data.setdefault("channels", {})
    chan = chans.setdefault(ch, {})
    old = chan.get("model", "deepseek")
    chan["model"] = md
    _write_cfg(cfg, data)
    return {"ok": True, "channel": ch, "old": old, "new": md,
            "restart_required": old != md,
            "note": "restart Bridge/run.py --channel " + ch if old != md else ""}