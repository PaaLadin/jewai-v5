"""Bridge/read.py — универсальные читатели состояния страницы через CDP.

Что НЕ здесь (это в Adapters/<model>.py):
- Селекторы конкретной SPA (.ds-message, .qwen-markdown, .AliceInput-Textarea).
- Парсинг блоков команд (это Bridge/exec.py).
- Отправка сообщений (это Adapters + exec).

Что здесь (универсальное):
- read_text: полный innerText страницы.
- read_heartbeat: dsbHeartbeat из DOM (если его ставит content.js/аналог).
- read_textarea: value конкретного textarea по CSS-селектору.
- current_url: URL вкладки.
- find_sidepanel: target sidepanel.html на CDP-порту.
- read_sidepanel_text: innerText панели (для диагностики).
"""
from __future__ import annotations

import time
from typing import Any

from .cdp import CDP, list_targets, find_chat


def read_text(cdp: CDP) -> str:
    return cdp.eval_expr("document.body ? document.body.innerText : ''") or ""


def read_heartbeat(cdp: CDP, stale_sec: int = 15) -> dict[str, Any]:
    """dsbHeartbeat ставит content.js (или аналог). Если его нет — stale=True."""
    raw = cdp.eval_expr("document.documentElement.dataset.dsbHeartbeat || ''")
    if not raw:
        return {"present": False, "ts": 0, "age_ms": None, "stale": True}
    try:
        ts = int(raw)
    except Exception:
        return {"present": True, "ts": 0, "age_ms": None, "stale": True}
    age_ms = int(time.time() * 1000) - ts
    return {
        "present": True,
        "ts": ts,
        "age_ms": age_ms,
        "stale": age_ms > stale_sec * 1000,
    }


def read_textarea(cdp: CDP, selector: str) -> dict[str, Any]:
    """Прочитать textarea по CSS-селектору. Возвращает {found, value, len}."""
    expr = (
        "(() => { const t = document.querySelector(%r);"
        " if (!t) return {found:false, value:'', len:0};"
        " const v = t.value || '';"
        " return {found:true, value:v, len:v.length}; })()"
    ) % selector
    r = cdp.eval_expr(expr) or {}
    return {
        "found": bool(r.get("found")),
        "value": str(r.get("value") or ""),
        "len": int(r.get("len") or 0),
    }


def current_url(cdp: CDP) -> str:
    return cdp.eval_expr("location.href") or ""


def find_sidepanel(port: int) -> dict | None:
    for t in list_targets(port):
        if "sidepanel.html" in t.get("url", ""):
            return t
    return None


def read_sidepanel_text(port: int, maxlen: int = 4000) -> str:
    t = find_sidepanel(port)
    if not t:
        return ""
    with CDP(t["webSocketDebuggerUrl"]) as c:
        txt = c.eval_expr("document.body ? document.body.innerText : ''") or ""
    return txt[:maxlen]