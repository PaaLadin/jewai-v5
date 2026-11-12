"""Lada Daemon — резидентный цикл качелей для Лады.

Читает:
- Profiles/A/logs/lada_inbox.jsonl (входящие сообщения)
- Profiles/A/logs/kick_buffer.jsonl (кики от других агентов)
- Profiles/A/logs/paused.json (пауза)

Пишет:
- Profiles/A/logs/lada_outbox.jsonl (ответы для UI/агентов)

Логика:
1. Если paused — стоп.
2. Читает новые записи из inbox/kick_buffer.
3. Для каждой: если системный маркер — простой ответ без LLM. Иначе — query() с ReAct.
4. Пишет ответ в outbox.
5. Если задача не завершена (были tool_calls но нет финального text) — при следующем тике продолжает.
"""
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from Core.config import load as load_config
from Mainframe import llm, lada_chats

POLL_SEC = 5
INBOX = ROOT / "Profiles" / "A" / "logs" / "lada_inbox.jsonl"
OUTBOX = ROOT / "Profiles" / "A" / "logs" / "lada_outbox.jsonl"
KICK_BUFFER = ROOT / "Profiles" / "A" / "logs" / "kick_buffer.jsonl"
PAUSED = ROOT / "Profiles" / "A" / "logs" / "paused.json"
STATE = ROOT / "Profiles" / "A" / "logs" / "lada_daemon_state.json"


def _read_jsonl(path, since_ts=0.0):
    if not path.exists():
        return []
    out = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                if obj.get("ts", 0) > since_ts:
                    out.append(obj)
            except Exception:
                pass
    except Exception:
        pass
    return out


def _append_jsonl(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _is_paused():
    if not PAUSED.exists():
        return False
    try:
        return bool(json.loads(PAUSED.read_text(encoding="utf-8")).get("paused"))
    except Exception:
        return False


def _load_state():
    if not STATE.exists():
        return {"inbox_ts": 0.0, "kick_ts": 0.0, "chat_id": "", "unfinished_task": False}
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        return {"inbox_ts": 0.0, "kick_ts": 0.0, "chat_id": "", "unfinished_task": False}


def _save_state(st):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, STATE)


def _handle_system_marker(text):
    """Return response if this is a system marker (no LLM call needed), else None."""
    t = text.strip()
    if t.startswith("[ALIVE?]"):
        return "[ALIVE] Лада на связи"
    if t.startswith("[PAUSE-ALL]") or t.startswith("[HALT]"):
        return "[ACK] пауза принята"
    if t.startswith("[SYS]"):
        return None  # учитываем, не отвечаем
    return None


def main():
    cfg = load_config()
    print("Lada Daemon started. Inbox:", INBOX, flush=True)
    st = _load_state()

    while True:
        try:
            if _is_paused():
                time.sleep(POLL_SEC)
                continue

            # 1. Собираем новые сообщения из inbox и kick_buffer
            inbox_msgs = _read_jsonl(INBOX, st["inbox_ts"])
            kick_msgs = _read_jsonl(KICK_BUFFER, st["kick_ts"])

            # Плюс новые сообщения от оператора из UI (lada_inbox)
            pending = []
            for m in inbox_msgs:
                pending.append({"src": "inbox", "text": m.get("text", ""), "ts": m.get("ts", 0)})
            for m in kick_msgs:
                pending.append({"src": "kick", "text": m.get("text", ""), "ts": m.get("ts", 0)})

            pending.sort(key=lambda x: x["ts"])

            for m in pending:
                text = m["text"]
                if not text:
                    continue

                # Системные маркеры — без LLM
                sys_reply = _handle_system_marker(text)
                if sys_reply is not None:
                    _append_jsonl(OUTBOX, {
                        "ts": time.time(),
                        "from": "LADA",
                        "reply": sys_reply,
                        "src": m["src"],
                    })
                    continue

                # Иначе — полноценный ReAct-цикл
                res = llm.query(cfg, text, chat_id=st.get("chat_id", ""))
                reply = res.get("text", "") or res.get("error", "no reply")
                if res.get("chat_id"):
                    st["chat_id"] = res["chat_id"]
                _append_jsonl(OUTBOX, {
                    "ts": time.time(),
                    "from": "LADA",
                    "reply": reply,
                    "src": m["src"],
                    "tool_log_len": len(res.get("tool_log", [])),
                })
                # Если ответ — таймаут/лимит, ставим флаг продолжения
                if "превышен таймаут" in reply or "лимит итераций" in reply:
                    st["unfinished_task"] = True


            # 3. Продолжение незавершенной задачи
            if st.get("unfinished_task"):
                res = llm.query(cfg, "Продолжай с того места, где остановилась. Не задавай вопросов, просто делай.", chat_id=st["chat_id"])
                reply = res.get("text", "") or ""
                if res.get("chat_id"):
                    st["chat_id"] = res["chat_id"]
                # Если все еще не завершено — оставляем флаг
                if "превышен таймаут" in reply or "лимит итераций" in reply:
                    pass  # оставляем unfinished_task для следующего цикла
                else:
                    st["unfinished_task"] = False
                _append_jsonl(OUTBOX, {
                    "ts": time.time(),
                    "from": "LADA",
                    "reply": reply,
                    "src": "continuation",
                    "tool_log_len": len(res.get("tool_log", [])),
                })

            # Обновляем водяные знаки
            if inbox_msgs:
                st["inbox_ts"] = max(m["ts"] for m in inbox_msgs)
            if kick_msgs:
                st["kick_ts"] = max(m["ts"] for m in kick_msgs)
            _save_state(st)

        except Exception as e:
            _append_jsonl(OUTBOX, {"ts": time.time(), "from": "LADA", "error": str(e)[:200]})
        time.sleep(POLL_SEC)


if __name__ == "__main__":
    main()