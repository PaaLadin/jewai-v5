---
title: CDP не отвечает (Chrome упал)
tags: [cdp, chrome, падение]
related: [functions/channels]
updated: 2026-11-09
---

# CDP не отвечает

Симптом: `/api/status` показывает CDP=false, панель красная.

## Причины

- Chrome канала упал (закрыт руками, краш).
- Порт CDP занят другим процессом.
- Профиль Chrome повреждён.

## Лечение

1. Mainframe → AGENTS → STOP на канале.
2. START — Chrome перезапустится.
3. Если не помогает — `launchers\start-<L>.ps1` вручную.
4. Профиль повреждён: переименовать `Profiles/<L>/chrome/` → `chrome.bak`,
   запустить заново, залогиниться.

## См. также

- [[functions/channels]]
- [[troubleshooting/panel_stuck]]