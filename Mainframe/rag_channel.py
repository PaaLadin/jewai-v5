"""Mainframe/rag_channel.py - RAG channel for Alice (Ф5, каркас).

Contract:
- RAG channel: механизм доставки задач/знаний агенту F (Алиса) через файлы.
- Config: rag_channel: {"path": "logs/rag_channel"} (default).
- push(channel_from, target, text) -> appends JSONL entry.
- pull(target, since_ts) -> list of entries where to==target or to==ALL, ts>since_ts.
- Purpose: Алиса и другие агенты без прямого CDP могут читать RAG-канал.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from Core.config import Config


def _dir(cfg: Config) -> Path:
    p = cfg.path("logs", "rag_channel")
    p.mkdir(parents=True, exist_ok=True)
    return p


def _file(cfg: Config) -> Path:
    return _dir(cfg) / "channel.jsonl"


def push(cfg: Config, frm: str, to: str, text: str) -> dict:
    entry = {"ts": time.time(), "from": frm, "to": to, "text": text}
    p = _file(cfg)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return {"ok": True, "entry": entry}


def pull(cfg: Config, target: str, since_ts: float = 0.0) -> dict:
    p = _file(cfg)
    if not p.exists():
        return {"ok": True, "entries": [], "count": 0}
    out = []
    for raw in p.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            e = json.loads(raw)
        except Exception:
            continue
        if e.get("ts", 0) <= since_ts:
            continue
        if e.get("to") in (target, "ALL"):
            out.append(e)
    return {"ok": True, "entries": out[-200:], "count": len(out)}