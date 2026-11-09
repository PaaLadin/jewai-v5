---
title: Панель залипла (PANEL-STUCK)
tags: [panel-stuck, lastid, зависание]
related: [functions/panel]
updated: 2026-11-09
---

# Панель залипла (PANEL-STUCK)

Симптом: команды не исполняются, lastId стоит, в логах «Panel-stuck: N команд висят >90s».

## Диагностика

1. `GET http://127.0.0.1:8670/api/status` — какой lastId видит сервер.
2. Открыть Chrome канала через CDP (`chrome://inspect`), посмотреть textarea.
3. Если textarea непустой — возможно, оператор пишет.

## Лечение

1. Reload extension: `chrome://extensions/` → JewAI → Reload.
2. Перезапустить bridge канала через Mainframe (STOP → START).
3. Повтор с новым id.

## Частые причины

- Двойной сервер на 8670 (netstat покажет два LISTEN).
- Stale recentlySentIds в chrome.storage — нужен reload extension.
- Перегрузка сервера при поллинге.

## См. также

- [[functions/panel]]
- [[functions/channels]]