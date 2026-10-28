# Mainframe: gap old vs v5 (13D, 2026-10-28)

Аудит старого council_chat/server.py (36 точных + 11 префиксных роутов).
Наш v5 Mainframe - 10 роутов. Функциональный разрыв описан ниже.

## Что есть у старого, нет у нас

### Чат (общий + персональные)

- GET  /api/messages -> все сообщения общего chat.jsonl.
- POST /api/send -> {from, to, text}, дедуп 5с, broadcast при to=ALL.
- GET  /api/say/<CH>?text=&to= -> быстрый send через URL.
- GET  /api/chat/<CH> -> персональный чат канала, последние 200.
- POST /api/chat/<CH> -> запись с ACL (только оператор или сам канал).
- GET  /api/chat_index -> counts по каналам.
Файлы: sandbox/council_chat/chat.jsonl + chat_<CH>.jsonl.

### Управление сервисами (launchpad)

- GET  /api/launchpad/status -> блоки: server, agent:<CH>, chrome:<CH>, doh, mailbot, rebirth, lada.
- POST /api/boot {target}, /api/stop {target}, /api/restart {target}.
- Блоки: agent, chrome, doh, mailbot, rebirth, lada(info).
- server self-защита (нельзя boot/stop/restart себя).

### Совещание и пауза

- GET/POST /api/meeting {on}, /api/pause_all {on}.
- /api/pause, /api/resume, /api/close, /api/open - все кикают агентов.
- PAUSE-ALL: писать в чат может только оператор.

### ALIVE

- GET  /api/alive -> flags/alive_<CH>.json exists.
- POST /api/alive {ch} -> флаг + kick "[COUNCIL] ALIVE? <CH>".
- POST /api/alive_ack {ch} -> ack_ts.

### Status / health

- GET /api/status: channels с {name, prefix, model, cdp, agent, cdp_alive, agent_alive}.
  Наш v5 - {name, agent_port, cdp_port, agent_alive, cdp_alive} (другие имена полей).
- GET /api/health: matrix {content, agent, watchdog, recovery, lastId, cmds, alive_button}.
  Наш v5 - только {ok, ts, uptime, version}.

### Прослойки

- GET /fs/<rel> -> файловый браузер (только внутри ROOT, 403 на escape).
- GET /api/logs?name=chat|agent|svc|server -> хвост лога.
- GET /api/roadmap?name=X, POST /api/roadmap -> state из logs/roadmap_state/<name>.json.
- GET /roadmap/<name> и /roadmap/<name>.html -> отдать PROJECT/ROADMAP.html.
- GET /api/projects -> скан Projects/ и project/ на ROADMAP.html.
- GET /api/svc POST {channel, kind, action} -> svc.py start/stop.
- GET /api/localai/status, POST /api/localai/query -> local_ai :8090.

### Статика

- /, /index.html, /style.css, /app.js, /pers.js, /mnemo.js, /launchpad_live.js, /localai.js.
  dashboard.html - 404 в живом сосуде (файла нет).

## План переноса в v5 (по приоритетам)

P0 - без чего v5 не работает как рабочий инструмент:
1. chat.jsonl + chat_<CH>.jsonl + /api/messages, /api/send, /api/chat/<CH>, /api/say/<CH>.
2. /api/status с полной схемой (prefix, model, cdp, agent, cdp_alive, agent_alive).
3. /api/health с матрицей (content, agent, watchdog, recovery, lastId, cmds).
4. /api/svc POST -> svc control.

P1 - рабочий комфорт:
5. /api/launchpad/status, /api/boot, /api/stop, /api/restart.
6. /api/meeting, /api/pause_all, /api/pause, /api/resume.
7. /fs/<rel>, /api/logs.
8. /api/roadmap GET+POST, /roadmap/<name>.

P2 - надстройки:
9. /api/alive, /api/alive_ack.
10. /api/localai/status, /api/localai/query (в v5 - сетевая LLM по ip:port).
11. /pers.js, /mnemo.js, /launchpad_live.js - если нужны мнемосхемы.

## Что НЕ переносим

- /api/reload - заглушка 501 в старом.
- /dashboard.html - файла нет, 404.
- Хардкод C:/DeepSeek в старом.
- PAUSE-ALL через флаг meeting.json - в v5 через state файл.

Источник: RAG/architecture/AUDIT.md раздел 28.
