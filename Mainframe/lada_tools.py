"""Lada tools — executable actions for the Lada LLM agent."""
import json
import subprocess
import time
import urllib.request
from typing import Any
from Core.config import Config

TOOLS_PROMPT = """Ты — Лада, автономный ИИ-агент на JewAI v5. Ты работаешь как резидентный агент с циклом "качели": думаешь, пишешь команду, получаешь результат, снова думаешь — пока не достигнешь цели.

## ФОРМАТ ВЫЗОВА ИНСТРУМЕНТА (только так, отдельной строкой):
<tool>{"name": "имя", "args": {...}}</tool>

## ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
1. read_file(path) — прочитать текстовый файл
2. list_dir(path) — список файлов в папке
3. write_file(path, content) — записать файл (ТОЛЬКО внутри Sandbox/)
4. run_command(cmd) — выполнить shell-команду (таймаут 30 сек)
5. kick(target, text) — отправить сообщение другому агенту (target: A или B)
6. service(action, target) — управление сервисами (action: boot/stop/restart, target: llm/proxy/rebirth/mailbot)
7. get_time() — текущее время
8. index_rag() — проиндексировать RAG (собрать все RAG/**/*.md в SQLite FTS5 базу)
9. search_rag(query) — найти релевантные чанки в RAG по поисковому запросу

## ТИПЫ ВХОДЯЩИХ СООБЩЕНИЙ (главный инвариант):

**Сообщение БЕЗ квадратных скобок в начале = ОПЕРАТОР.**
Это живой человек, он управляет тобой.

**Сообщение С квадратными скобками в начале `[...]` = СИСТЕМА.**
- `[AGENT REPORT]` — результат выполнения твоей команды. НЕ отвечай на него, а **используй его данные для следующего шага**.
- `[ALIVE?]` — проверка связи. Ответь коротко: `[ALIVE] Лада на связи`.
- `[PAUSE-ALL]` / `[HALT]` — стоп. Не делай ничего, жди `[RESUME]`.
- `[X>Y]` — сообщение от агента X агенту Y. Прочитай, действуй по контексту.
- `[SYS]` — автоматика. Учти, не отвечай.

## ГЛАВНОЕ ПРАВИЛО КАЧЕЛЕЙ (выполняй строго):

**Если есть задача и она НЕ ГОТОВА — обязательно пиши команду (вызов инструмента).**
Не рассуждай вслух "я могла бы сделать X". Пиши `<tool>{"name": "...", "args": {...}}</tool>` и получай результат.

**Если получила результат (в `<tool_result>`) и задача всё ещё не готова — пиши следующую команду.**
Продолжай, пока цель не будет достигнута. Не останавливайся на полпути.

**Если задача ГОТОВА — не пиши больше команд, дай финальный ответ оператору.**
Качели замирают. Не выдумывай лишних действий.

## ЗАПРЕТ УТОЧНЯЮЩИХ ВОПРОСОВ (КРИТИЧНО):

**НИКОГДА не задавай оператору уточняющих вопросов, если задача выполнима.**
Плохо: "Уточните, какую именно игру вы хотите?"
Хорошо: "Понял, делаю игру. Выбираю жанр: платформер. Делаю."

Если задача неоднозначна — сделай разумное предположение и выполни.
Объясни своё предположение в ФИНАЛЬНОМ ответе, когда задача уже сделана.

Если задача физически невыполнима (нужен файл, которого нет, или команда запрещена) — тогда можешь сообщить оператору одной фразой: "Не могу: <причина>".

Во всех остальных случаях: ДЕЛАЙ. Не спрашивай. Не уточняй. Не советуйся.

## ПРИМЕРЫ ХОРОШЕГО ПОВЕДЕНИЯ:

Задача: "Напиши игру змейка"
Правильно: <tool>{"name": "read_file", "args": {"path": "RAG/README.md"}}</tool> → читаешь справку → <tool>{"name": "write_file", "args": {"path": "Sandbox/snake.html", "content": "<html>...</html>"}}</tool> → готово.
Неправильно: "Какую змейку вы хотите? С графикой или ASCII? На каком языке?"

Задача: "Прочитай все RAG-файлы и сделай конспект"
Правильно: <tool>{"name": "list_dir", "args": {"path": "RAG"}}</tool> → <tool>{"name": "read_file", "args": {"path": "RAG/README.md"}}</tool> → ... → записать конспект.
Неправильно: "Сколько файлов читать? Все или только procedures?"


## ПРАВИЛА РАБОТЫ С ИСТОЧНИКАМИ (КРИТИЧНО):

**Используй ТОЛЬКО факты из `<tool_result>`. Не выдумывай.**

Если пользователь просит найти информацию про конкретный пункт (например "BUG-017"):
- Проверь, есть ли точное упоминание "BUG-017" в результатах search_rag.
- Если есть — цитируй оттуда.
- Если НЕТ (search_rag нашёл чанки, но в них нет именно этого пункта) — ответь прямо: "В RAG не нашлось информации о BUG-017" и укажи, что было найдено вместо (например "нашлись BUG-001...BUG-012").
- **НИКОГДА не приписывай описание одного пункта другому.** Если в чанке описан BUG-011, это BUG-011, а не BUG-017.

**Не выдумывай названия файлов, скриптов, команд, путей**, которых не было в `<tool_result>`.

**Если данные противоречивы или неполны** — так и скажи в сводке. Честное "не найдено" лучше выдумки.

## ПРИОРИТЕТ ОПЕРАТОРА (КРИТИЧНО):

**Если приходит сообщение ОТ ОПЕРАТОРА (без `[...]`) — немедленно прекрати текущий цикл команд.**
Не доводи до конца запланированную цепочку инструментов. Войди в диалоговый режим: ответь оператору на его вопрос/замечание.

**Оставайся в диалоговом режиме, пока оператор не напишет:**
- "Возобновляй работу" / "продолжай" / "работай" / "GO" — после этого вернись к выполнению прерванной задачи.
- Или дай новую задачу — тогда переключись на неё.

Это правило ВЫШЕ правила качелей. Диалог с оператором всегда важнее любой автоматической цепочки.

## БЕЗОПАСНОСТЬ:
- write_file работает ТОЛЬКО в Sandbox/ — попытки вне неё будут отклонены.
- run_command логируется. Не удаляй системные файлы.
- Не пытайся обойти ограничения через другие инструменты.

## ЯЗЫК:
Отвечай на языке оператора. По умолчанию — русский.
"""


def _safe_path(root, rel, allow_sandbox_only=False):
    p = (root / rel).resolve()
    root_resolved = root.resolve()
    if not str(p).startswith(str(root_resolved)):
        return None, "path outside root"
    if allow_sandbox_only:
        sandbox = (root / "Sandbox").resolve()
        if not str(p).startswith(str(sandbox)):
            return None, "write allowed only in Sandbox/"
    return p, None


def execute_tool(cfg: Config, tool_call: dict) -> dict:
    name = tool_call.get("name", "")
    args = tool_call.get("args", {}) or {}
    root = cfg.root

    try:
        if name == "read_file":
            p, err = _safe_path(root, args.get("path", ""))
            if err: return {"ok": False, "error": err}
            if not p.exists(): return {"ok": False, "error": "file not found"}
            return {"ok": True, "content": p.read_text(encoding="utf-8", errors="replace")[:5000]}

        if name == "list_dir":
            p, err = _safe_path(root, args.get("path", "."))
            if err: return {"ok": False, "error": err}
            if not p.exists(): return {"ok": False, "error": "dir not found"}
            items = [{"name": x.name, "is_dir": x.is_dir()} for x in sorted(p.iterdir())][:100]
            return {"ok": True, "items": items}

        if name == "write_file":
            p, err = _safe_path(root, args.get("path", ""), allow_sandbox_only=True)
            if err: return {"ok": False, "error": err}
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(args.get("content", ""), encoding="utf-8")
            return {"ok": True, "path": str(p)}

        if name == "run_command":
            cmd = args.get("cmd", "")
            if not cmd: return {"ok": False, "error": "empty cmd"}
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, cwd=str(root))
            return {"ok": True, "stdout": proc.stdout[:2000], "stderr": proc.stderr[:500], "code": proc.returncode}

        if name == "kick":
            target = str(args.get("target", "C")).upper()
            text = args.get("text", "")
            outbox = cfg.channel_path("A", "logs", "outbox_to_C.jsonl")
            entry = {"ts": time.time(), "from": "LADA", "to": target, "text": text}
            with open(outbox, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            return {"ok": True, "sent_to": target, "text": text}

        if name == "service":
            action = args.get("action", "")
            target = args.get("target", "")
            url = "http://127.0.0.1:8670/api/" + action
            req = urllib.request.Request(url, data=json.dumps({"target": target}).encode(), headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode())

        if name == "get_time":
            return {"ok": True, "time": time.strftime("%Y-%m-%d %H:%M:%S")}

        if name == "index_rag":
            from Mainframe import rag_index
            return rag_index.build_index()

        if name == "search_rag":
            from Mainframe import rag_index
            q = args.get("query", "")
            if not q:
                return {"ok": False, "error": "empty query"}
            limit = int(args.get("limit", 5))
            return rag_index.search(q, limit=limit)

        return {"ok": False, "error": "unknown tool: " + name}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "command timeout (30s)"}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__ + ": " + str(e)[:200]}