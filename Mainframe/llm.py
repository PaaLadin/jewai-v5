"""Mainframe/llm.py - network LLM client + params + tools (v5, 11C).

Contract:
- config.json llm section: {host, port, path, model, params: {...}, tools: {...}}
- status(cfg) -> {ok, configured, host, port, model, params, tools}
- query(cfg, text, **kw) -> POST OpenAI-compat chat/completions with all params.
  kw['chat_id'] (optional) -> per-chat history via Mainframe.lada_chats (if present);
  fallback -> logs/lada_history.jsonl (see _append_history).
- get_params(cfg), set_params(cfg, params)
- get_tools(cfg), set_tool(cfg, name, on)
- history(cfg, n) - last n messages from logs/lada_history.jsonl (persisted)
- clear_history(cfg)

Tools (v5 defaults, executor stubs — implement incrementally):
- get_time, get_weather, check_email, ask_agent, query_rag,
  generate_image, generate_audio.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
import urllib.error
from typing import Any

from Core.config import Config


DEFAULT_PARAMS = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "max_tokens": 1024,
    "repeat_penalty": 1.1,
    "seed": -1,
}

DEFAULT_TOOLS = {
    "get_time": True,
    "get_weather": True,
    "check_email": False,
    "ask_agent": False,
    "query_rag": True,
    "generate_image": False,
    "generate_audio": False,
}


def _read_config(cfg: Config) -> dict:
    try:
        return json.loads(cfg.path("config.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_config(cfg: Config, data: dict) -> None:
    p = cfg.path("config.json")
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


def _llm_cfg(cfg: Config) -> dict[str, Any]:
    data = _read_config(cfg)
    return dict(data.get("llm") or {})


def _history_path(cfg: Config):
    return cfg.path("logs", "lada_history.jsonl")


def status(cfg: Config) -> dict:
    c = _llm_cfg(cfg)
    host, port = c.get("host"), c.get("port")
    configured = bool(host and port)
    params = dict(DEFAULT_PARAMS)
    params.update(c.get("params") or {})
    tools = dict(DEFAULT_TOOLS)
    tools.update(c.get("tools") or {})
    return {
        "ok": True, "configured": configured,
        "host": host, "port": port,
        "model": c.get("model", "local"),
        "params": params, "tools": tools,
        "reason": "" if configured else "not_configured (set config.llm)",
    }


def get_params(cfg: Config) -> dict:
    return {"ok": True, "params": status(cfg)["params"]}


def set_params(cfg: Config, params: dict) -> dict:
    data = _read_config(cfg)
    llm = dict(data.get("llm") or {})
    cur = dict(DEFAULT_PARAMS)
    cur.update(llm.get("params") or {})
    for k, v in (params or {}).items():
        if k in DEFAULT_PARAMS:
            try:
                cur[k] = float(v) if k != "top_k" and k != "max_tokens" and k != "seed" else int(v)
            except Exception:
                pass
    llm["params"] = cur
    data["llm"] = llm
    _write_config(cfg, data)
    return {"ok": True, "params": cur}


def get_tools(cfg: Config) -> dict:
    return {"ok": True, "tools": status(cfg)["tools"]}


def set_tool(cfg: Config, name: str, on: bool) -> dict:
    if name not in DEFAULT_TOOLS:
        return {"ok": False, "error": "unknown tool", "name": name}
    data = _read_config(cfg)
    llm = dict(data.get("llm") or {})
    cur = dict(DEFAULT_TOOLS)
    cur.update(llm.get("tools") or {})
    cur[name] = bool(on)
    llm["tools"] = cur
    data["llm"] = llm
    _write_config(cfg, data)
    return {"ok": True, "tools": cur}


def _exec_tool(name: str, args: dict) -> dict:
    if name == "get_time":
        return {"ok": True, "time": time.strftime("%Y-%m-%d %H:%M:%S")}
    if name == "get_weather":
        return {"ok": False, "error": "not implemented"}
    if name == "check_email":
        return {"ok": False, "error": "not implemented"}
    if name == "ask_agent":
        return {"ok": False, "error": "not implemented"}
    if name == "query_rag":
        return {"ok": False, "error": "not implemented"}
    if name == "generate_image":
        return {"ok": False, "error": "not implemented"}
    if name == "generate_audio":
        return {"ok": False, "error": "not implemented"}
    return {"ok": False, "error": "unknown tool", "name": name}


def _append_history(cfg: Config, role: str, text: str) -> None:
    try:
        p = _history_path(cfg)
        p.parent.mkdir(parents=True, exist_ok=True)
        rec = {"ts": time.time(), "role": role, "text": text}
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def history(cfg: Config, n: int = 50) -> dict:
    p = _history_path(cfg)
    if not p.exists():
        return {"ok": True, "messages": []}
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except Exception:
        return {"ok": True, "messages": []}
    out = []
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return {"ok": True, "messages": out}


def clear_history(cfg: Config) -> dict:
    try:
        p = _history_path(cfg)
        if p.exists():
            p.unlink()
    except Exception as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True}


def query(cfg: Config, text: str, **kw: Any) -> dict:
    c = _llm_cfg(cfg)
    host, port = c.get("host"), c.get("port")
    if not (host and port):
        return {"ok": False, "error": "llm not configured",
                "reason": "set config.llm {host, port}"}
    path = c.get("path", "/v1/chat/completions")
    model = kw.get("model") or c.get("model", "default")
    timeout = int(kw.get("timeout", 600))
    params = dict(DEFAULT_PARAMS)
    params.update(c.get("params") or {})
    for k in DEFAULT_PARAMS:
        if k in kw:
            params[k] = kw[k]

    # per-chat history (Arkady patch): опционально, если есть lada_chats и передан chat_id
    chat_id = kw.get("chat_id") or ""
    messages = []
    lada_chats = None
    if chat_id:
        try:
            from Mainframe import lada_chats as _lc
            lada_chats = _lc
        except Exception:
            lada_chats = None
    if lada_chats is not None:
        try:
            history = lada_chats.get_chat(chat_id) or []
            for m in history:
                r = m.get("role") if isinstance(m, dict) else None
                ct = m.get("content") if isinstance(m, dict) else None
                if r and ct:
                    messages.append({"role": r, "content": ct})
        except Exception:
            messages = []
    messages.append({"role": "user", "content": text})

    body = {
        "model": model,
        "messages": messages,
        "temperature": params["temperature"],
        "top_p": params["top_p"],
        "max_tokens": params["max_tokens"],
        "repeat_penalty": params["repeat_penalty"],
        "seed": params["seed"],
    }
    if params.get("top_k"):
        body["top_k"] = params["top_k"]
    data = json.dumps(body).encode("utf-8")
    url = "http://%s:%s%s" % (host, port, path)
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")

    # 1) пользовательское сообщение в историю
    if lada_chats is not None:
        try:
            lada_chats.append_message(chat_id, "user", text)
        except Exception:
            pass
    else:
        _append_history(cfg, "user", text)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(raw)
            reply = ""
            if isinstance(parsed, dict):
                ch = parsed.get("choices") or []
                if ch and isinstance(ch[0], dict):
                    msg = ch[0].get("message") or {}
                    reply = msg.get("content") or ch[0].get("text") or ""
            if reply:
                if lada_chats is not None:
                    try:
                        lada_chats.append_message(chat_id, "assistant", reply)
                    except Exception:
                        pass
                else:
                    _append_history(cfg, "assistant", reply)
        except Exception:
            parsed = {"raw": raw}
            reply = ""
        out = {"ok": True, "response": parsed, "reply": reply}
        if chat_id:
            out["chat_id"] = chat_id
        return out
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": "HTTP %d" % e.code,
                "body": (e.read() or b"").decode("utf-8", "replace")[:500],
                "chat_id": chat_id or None}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__ + ": " + str(e),
                "chat_id": chat_id or None}


