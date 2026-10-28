"""Mainframe/council.py - chat.jsonl + per-channel chat + /api/send routing.

Contract (from AUDIT section 28.1-28.2, rewritten from scratch):
- chat.jsonl: append-only JSONL {ts, time, from, to, text}.
- chat_<CH>.jsonl: per-channel, {ts, time, id, from, to, text}.
- Dedup: same (from, to, text) within 5 seconds -> skip (avoids double-click / echo).
- next_personal_id: from "operator" -> Z<CH>AA<NNNN>, from "<CH>" -> <CH>ZAA<NNNN>.
- ACL: POST /api/chat/<CH> allowed only if from == operator or from == CH.
- Broadcast: to=ALL appends and kicks all channels (kick happens in http.py).
"""
from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path
from typing import Any

from Core.config import Config

_LOCK = threading.Lock()
_DEDUP: dict[tuple, float] = {}
_DEDUP_WINDOW = 5.0
_DEDUP_MAX = 30


def _chat_path(cfg: Config) -> Path:
    p = cfg.path("logs", "council", "chat.jsonl")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _personal_path(cfg: Config, letter: str) -> Path:
    p = cfg.path("logs", "council", ("chat_%s.jsonl" % letter.upper()))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _now() -> tuple[float, str]:
    return time.time(), time.strftime("%H:%M:%S")


def _dedup_ok(frm: str, to: str, text: str) -> bool:
    now = time.time()
    key = (frm, to, text)
    last = _DEDUP.get(key)
    if last is not None and (now - last) < _DEDUP_WINDOW:
        return False
    _DEDUP[key] = now
    if len(_DEDUP) > _DEDUP_MAX:
        for k in list(_DEDUP):
            if now - _DEDUP[k] > _DEDUP_WINDOW:
                del _DEDUP[k]
    return True


def append_message(cfg: Config, frm: str, to: str, text: str) -> dict:
    ts, timestr = _now()
    msg = {"ts": ts, "time": timestr, "from": frm, "to": to, "text": text}
    with _LOCK:
        with _chat_path(cfg).open("a", encoding="utf-8") as f:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
    return msg


def load_messages(cfg: Config, limit: int = 0) -> list[dict]:
    p = _chat_path(cfg)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out[-limit:] if limit > 0 else out


def send(cfg: Config, frm: str, to: str, text: str) -> dict:
    """Dedup + append. Returns {ok, msg, dedup?}."""
    if not text or not text.strip():
        return {"ok": False, "error": "empty text"}
    if not _dedup_ok(frm, to, text):
        return {"ok": True, "dedup": True, "msg": {"from": frm, "to": to, "text": text}}
    msg = append_message(cfg, frm, to, text)
    return {"ok": True, "msg": msg}


def load_personal(cfg: Config, letter: str, limit: int = 200) -> list[dict]:
    p = _personal_path(cfg, letter)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out[-limit:]


def _next_personal_id(cfg: Config, letter: str, frm: str) -> str:
    """operator -> Z<CH>AA<NNNN>. agent<CH> -> <CH>ZAA<NNNN>."""
    ch = letter.upper()
    if frm == "operator":
        pref = "Z" + ch + "AA"
    else:
        pref = ch + "ZAA"
    nums = []
    for m in load_personal(cfg, ch, limit=0):
        mid = m.get("id", "")
        if not isinstance(mid, str) or not mid.startswith(pref):
            continue
        tail = mid[len(pref):]
        if tail.isdigit():
            nums.append(int(tail))
    n = (max(nums) + 1) if nums else 1
    return "%s%04d" % (pref, n)


def send_personal(cfg: Config, letter: str, frm: str, text: str) -> dict:
    ch = letter.upper()
    if ch not in cfg.channels:
        return {"ok": False, "error": "unknown channel", "channel": ch}
    if frm != "operator" and frm.upper() != ch:
        return {"ok": False, "error": "forbidden_from", "channel": ch, "from": frm}
    if not text or not text.strip():
        return {"ok": False, "error": "empty text"}
    ts, timestr = _now()
    mid = _next_personal_id(cfg, ch, frm)
    msg = {
        "ts": ts, "time": timestr, "id": mid, "from": frm,
        "to": "operator" if frm != "operator" else ch,
        "text": text,
    }
    with _LOCK:
        with _personal_path(cfg, ch).open("a", encoding="utf-8") as f:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
    return {"ok": True, "id": mid, "channel": ch, "ts": ts}