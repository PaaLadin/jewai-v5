"""Mainframe/llm.py - network LLM client (Ф5).

Contract:
- Config keys (in config.json, optional llm section):
    llm: {"host": "127.0.0.1", "port": 8080, "path": "/v1/chat/completions", "model": "..."}
- status(cfg) -> {ok, configured, host, port}
- query(cfg, text, **kw) -> POST JSON {"model", "messages": [{"role":"user","content":text}]}
  returns parsed JSON or {ok:false, error}.
- No external deps (urllib). Timeout 600s.
- If not configured: {ok:false, configured:false, reason:"not_configured"}.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any

from Core.config import Config


def _llm_cfg(cfg: Config) -> dict[str, Any]:
    # Config has no 'llm' field yet; read from raw file to stay forward-compatible.
    import json as _j
    try:
        data = _j.loads(cfg.path("config.json").read_text(encoding="utf-8"))
    except Exception:
        return {}
    return dict(data.get("llm") or {})


def status(cfg: Config) -> dict:
    c = _llm_cfg(cfg)
    host = c.get("host")
    port = c.get("port")
    configured = bool(host and port)
    return {"ok": True, "configured": configured,
            "host": host, "port": port,
            "model": c.get("model", ""),
            "reason": "" if configured else "not_configured (set config.llm)"}


def query(cfg: Config, text: str, **kw: Any) -> dict:
    c = _llm_cfg(cfg)
    host = c.get("host")
    port = c.get("port")
    if not (host and port):
        return {"ok": False, "error": "llm not configured",
                "reason": "set config.llm {host, port}"}
    path = c.get("path", "/v1/chat/completions")
    model = kw.get("model") or c.get("model", "default")
    timeout = int(kw.get("timeout", 600))
    body = {
        "model": model,
        "messages": [{"role": "user", "content": text}],
        "temperature": kw.get("temperature", 0.2),
        "max_tokens": kw.get("max_tokens", 1024),
    }
    data = json.dumps(body).encode("utf-8")
    url = "http://%s:%s%s" % (host, port, path)
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"raw": raw}
        return {"ok": True, "response": parsed}
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": "HTTP %d" % e.code,
                "body": (e.read() or b"").decode("utf-8", "replace")[:500]}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__ + ": " + str(e)}