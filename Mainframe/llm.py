import json, re, urllib.request, urllib.error
from typing import Any
from Core.config import Config
from Mainframe import lada_chats, lada_tools

def _llm_cfg(cfg: Config) -> dict[str, Any]:
    try:
        data = json.loads(cfg.path("config.json").read_text(encoding="utf-8"))
    except Exception:
        return {}
    return dict(data.get("llm") or {})

def status(cfg: Config) -> dict:
    c = _llm_cfg(cfg)
    host = c.get("host")
    port = c.get("port")
    configured = bool(host and port)
    return {"ok": True, "configured": configured, "host": host, "port": port, "model": c.get("model", ""), "reason": "" if configured else "not_configured"}

def _call_llm(host, port, model, messages, timeout=600):
    url = f"http://{host}:{port}/v1/chat/completions"
    body = {"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 2048}
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            parsed = json.loads(r.read().decode("utf-8", "replace"))
            return {"ok": True, "response": parsed}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _parse_tool_call(text):
    """Find first <tool>{...}</tool> block."""
    m = re.search(r'<tool>\s*(\{.*?\})\s*</tool>', text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None

def query(cfg: Config, text: str, chat_id: str = "", **kw) -> dict:
    c = _llm_cfg(cfg)
    host, port = c.get("host"), c.get("port")
    if not (host and port):
        return {"ok": False, "error": "llm not configured"}
    model = c.get("model", "default")
    timeout = kw.get("timeout", 600)
    max_iter = kw.get("max_iterations", 100)

    if not chat_id:
        chat_id = lada_chats.create_chat(text[:40])

    history = lada_chats.get_chat(chat_id)
    messages = [{"role": "system", "content": lada_tools.TOOLS_PROMPT}]
    # Ограничиваем историю: только последние 4 сообщения (2 пары user/assistant)
    recent_history = history[-4:] if len(history) > 4 else history
    for m in recent_history:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": text})
    lada_chats.append_message(chat_id, "user", text)

    tool_log = []
    final_text = ""
    import time as _time
    _task_start = _time.time()
    _safety_timeout = kw.get("task_timeout", 600)
    
    # Sliding window: base = [system, original user task]
    _base_messages = messages[:2]  # system + first user
    _react_messages = []  # tool_call/tool_result pairs
    
    for iteration in range(max_iter):
        if _time.time() - _task_start > _safety_timeout:
            final_text = "Задача прервана: превышен таймаут 10 минут. Успела сделать: " + str(len(tool_log)) + " шагов."
            break
        
        # Собираем контекст: base + сводка старых шагов + последние 3 пары
        KEEP_LAST = 3
        if len(_react_messages) > KEEP_LAST * 2:
            # Старые шаги сжимаем в сводку
            old_pairs = _react_messages[:-KEEP_LAST * 2]
            tool_names = []
            for i in range(0, len(old_pairs), 2):
                if i < len(old_pairs):
                    msg = old_pairs[i]
                    content = msg.get("content", "")
                    import re as _re
                    m = _re.search(r'"name":\s*"([^"]+)"', content)
                    if m:
                        tool_names.append(m.group(1))
            summary = f"[Предыдущие шаги: {len(tool_names)} вызовов инструментов — {', '.join(tool_names[-10:])}]"
            messages = _base_messages + [{"role": "user", "content": summary}] + _react_messages[-KEEP_LAST * 2:]
        else:
            messages = _base_messages + _react_messages
        
        res = _call_llm(host, port, model, messages, timeout)
        if not res["ok"]:
            return {"ok": False, "error": res["error"], "chat_id": chat_id, "tool_log": tool_log}

        try:
            resp_text = res["response"]["choices"][0]["message"]["content"]
        except Exception as e:
            return {"ok": False, "error": "parse error: " + str(e), "chat_id": chat_id}

        tool_call = _parse_tool_call(resp_text)
        if not tool_call:
            final_text = resp_text
            break

        tool_result = lada_tools.execute_tool(cfg, tool_call)
        tool_log.append({"call": tool_call, "result": tool_result})
        _react_messages.append({"role": "assistant", "content": resp_text})
        result_str = json.dumps(tool_result, ensure_ascii=False)[:600]
        _react_messages.append({"role": "user", "content": f"<tool_result>{result_str}</tool_result>\n\nПродолжай."})

    if not final_text:
        final_text = resp_text if 'resp_text' in dir() else "Достигнут лимит итераций."

    lada_chats.append_message(chat_id, "assistant", final_text)
    return {"ok": True, "text": final_text, "chat_id": chat_id, "tool_log": tool_log}