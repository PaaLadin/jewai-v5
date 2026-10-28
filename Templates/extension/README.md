# Templates/extension

Базовый шаблон extension для агента. Источник - для всех каналов.

## Что здесь должно быть (пока пусто)

По старому проекту (AUDIT.md разделы 18-22), extension состоял из:
- manifest.json - MV3, sidePanel, tabs, host_permissions для chat.*
- content.js - инжект в SPA, парсинг блоков команд из DOM, отправка через chrome.runtime
- background.js - service worker, мост из content.js в agent.py HTTP
- sidepanel.html + sidepanel.js - UI вкладки
- agent.py - HTTP-сервер (read/write/run/list/mkdir/hash/sandbox) на порту канала

## Правило ROADMAP

Код старого проекта НЕ копируется. Каждый модуль переписывается с нуля.
Значит, extension в v5 нужно написать заново по контракту, а не копировать из C:/DeepSeek/extension/.

## Функциональная заметка

В v5 парсинг блоков и управление чатом идёт через Bridge/daemon.py + Bridge/exec.py
по нативному CDP. Extension в v5 функционально дублирует эту часть.
Если оператор решит оставить extension - это альтернативный путь (JS в браузере).
Если решит выкинуть - папка остаётся пустой, ничего не сломается.
