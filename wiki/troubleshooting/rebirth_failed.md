---
title: Rebirth не создал новый чат
tags: [rebirth, ошибка]
related: [functions/rebirth]
updated: 2026-11-09
---

# Rebirth не создал новый чат

Симптом: монитор видит флаг, но новый чат не появился.

## Проверки

1. `logs/rebirth_log.jsonl` — последние записи, `result` и `new_url`.
2. Таблица серий (`Rebirth/table.py` показывает текущее состояние).
3. PROMPT — `Templates/PROMPT_<следующая>.md` существует.

## Guard

Если `new_url` пуст — rebirth НЕ должен сдвигать таблицу. Иначе следующий
агент получит неправильный диапазон и не запустится.

## Ручной запуск

Через Mainframe → AGENTS → кнопка REBIRTH на канале.

## См. также

- [[functions/rebirth]]