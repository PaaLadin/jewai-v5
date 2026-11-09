---
title: Mainframe — панель оператора (8670)
tags: [панель, mainframe, 8670]
related: [functions/channels]
updated: 2026-11-09
---

# Mainframe

Адрес: `http://127.0.0.1:8670/`

## Вкладки

| Вкладка | Что |
|---|---|
| AGENTS | Каналы: агенты, статусы, пауза/резюм, self-test |
| MNEMO | Живая схема связей |
| CHAT | Общий чат |
| PERS | Персональные чаты оператор↔агент |
| PROJECTS | Список проектов |
| LOGS | Хвосты логов |
| ROADMAP | План проекта |
| WIKI | Эта вики |

## API

- `GET /api/status` — состояние каналов
- `GET /api/svc` — состояние сервисов (watchdog, recovery)
- `POST /api/chat/<CH>` — персональный чат
- `GET /api/wiki` — данные вики (JSON)

## См. также

- [[functions/channels]]
- [[functions/bridge]]