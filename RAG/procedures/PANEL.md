# PANEL (v5 15D)

Актуально на 2026-11-09.

## Структура

Mainframe на 8670, 8 табов:
- AGENTS — сетка карточек (лампы, cmds, кнопки PAUSE/RESUME/REBOOT/LOGIN)
- MNEMO — мнемосхема каналов (canvas + блоки, связи)
- CHAT — общий чат + пульт (Совещание, Пауза всем, Продолжить)
- PERS — персональные чаты (оператор <-> канал)
- PROJECTS — список проектов с ROADMAP.html
- LOGS — табы chat/server/agent/svc
- ROADMAP — просмотр ROADMAP проектов
- СПРАВКА — wiki через iframe (/wiki)

## API (основные)

- GET /api/status — каналы (agent_alive, cdp_alive, lastId, auth_status)
- GET /api/health — матрица (content, agent, watchdog, recovery)
- GET /api/launchpad/status — блоки (server, agent:A, chrome:A, doh)
- POST /api/pause {channel, on}, POST /api/restart {target}
- GET/POST /api/meeting, /api/pause_all
- GET /api/messages, POST /api/send {from, to, text}
- GET/POST /api/chat/<CH>
- GET /api/logs?name=, GET /api/roadmap?name=
- GET /api/projects, GET /wiki

## Что ушло от Pip-Boy

Старый Pip-Boy был: CRT-рамка, лампы AG/CH/WD/RC, светофор WALK/DONT WALK, кнопка SELF-TEST, литера канала 48pt.

15D: мнемосхема с блоками каналов (canvas-анимация), мнемоника агентов, 8 табов, iframe-справка. Старая ламповая панель сохранена в Archive/9C_crt_mainframe/.

## Известные баги v5

См. RAG/procedures/BUGS_V5.md.
