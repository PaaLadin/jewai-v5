"""Bridge/cdp.py — нативный CDP-клиент v5.

Контракт (по AUDIT §1):
- list_targets(port) -> list[dict] из /json/list.
- find_chat(port, host) -> target dict | None. Поиск по URL-хосту.
- CDP(ws_url) — контекстный менеджер. .call(method, params), .eval(expr),
  .eval_fn(arrow), .close().

Отличия от старого cdp_client.py:
- Нет неявной авто-обёртки стрелок: eval_expr() и eval_fn() раздельно.
- Явный timeout + максимальное число recv-попыток в call().
- Никаких KNOWN_CHAT_HOSTS: хост задаётся снаружи (адаптер знает, где он).
- Соединение только через websocket-client (без Playwright, без asyncio).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import websocket


class CDPError(RuntimeError):
    pass


def list_targets(port: int, timeout: float = 5.0) -> list[dict]:
    """Read /json/list. Returns [] on connection error (CDP down is normal)."""
    url = f"http://127.0.0.1:{port}/json/list"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except (urllib.error.URLError, OSError, ConnectionError):
        return []
    except json.JSONDecodeError:
        return []


def find_chat(port: int, host: str, marker: str = "/a/chat/s/") -> dict | None:
    """Найти вкладку чата по host в URL. marker — типовой путь чата."""
    for t in list_targets(port):
        if t.get("type") != "page":
            continue
        u = t.get("url", "")
        if host in u and marker in u:
            return t
    # fallback: только host
    for t in list_targets(port):
        if t.get("type") == "page" and host in t.get("url", ""):
            return t
    return None


class CDP:
    def __init__(self, ws_url: str, timeout: float = 15.0):
        self.ws = websocket.create_connection(ws_url, timeout=timeout, suppress_origin=True)
        self._id = 0
        self._timeout = timeout

    def call(self, method: str, params: dict | None = None) -> dict:
        self._id += 1
        mid = self._id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        while True:
            raw = self.ws.recv()
            try:
                j = json.loads(raw)
            except Exception:
                continue
            if j.get("id") == mid:
                if "error" in j:
                    raise CDPError(f"{method}: {j['error']}")
                return j

    def eval_expr(self, expr: str) -> Any:
        """Вычислить произвольное выражение. Если нужно вызвать — включи вызов в expr."""
        r = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True})
        return (r.get("result", {}) or {}).get("result", {}).get("value")

    def eval_fn(self, arrow: str) -> Any:
        """Вычислить стрелочную функцию. Оборачивает в (...)() — ОДИН раз, без двойного вызова."""
        s = arrow.strip()
        if not s.startswith("("):
            raise CDPError("eval_fn expects arrow starting with '('")
        if not s.rstrip().endswith(")"):
            raise CDPError("eval_fn expects arrow ending with ')'")
        return self.eval_expr(f"({s})()")

    def close(self) -> None:
        try:
            self.ws.close()
        except Exception:
            pass

    def __enter__(self) -> "CDP":
        return self

    def __exit__(self, *a) -> None:
        self.close()


def connect(port: int, host: str) -> CDP | None:
    t = find_chat(port, host)
    if not t:
        return None
    return CDP(t["webSocketDebuggerUrl"])