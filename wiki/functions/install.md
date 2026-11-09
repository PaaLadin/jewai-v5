---
title: Установка и запуск
tags: [установка, install, запуск]
related: [functions/channels]
updated: 2026-11-09
---

# Установка и запуск

JewAI v5 ставится из `install.bat` в корне репозитория.

## Порядок

1. Скопировать `C:\jewai` в целевую папку (или запустить `install.bat`).
2. Installer спросит имя, каналы, порты.
3. Создаст `config.json`, `Profiles/<L>/`, скачает Chrome for Testing.
4. Запустит launcher — откроются окна Chrome с расширением.
5. Логин в чаты через каждое окно.

## Запуск после установки

- `launchers\start-all.ps1` — все каналы
- `launchers\start-A.ps1` — только A
- Mainframe поднимается сам на 8670

## Остановка

- `launchers\stop-all.ps1` — мягко
- Mainframe → AGENTS → STOP для одного канала

## См. также

- [[functions/keys]]
- [[functions/panel]]