---
title: Перерождение (rebirth)
tags: [rebirth, серии, handover]
related: [functions/channels]
updated: 2026-11-09
---

# Перерождение

Когда чат агента переполняется (порог **850 команд** в серии), JewAI открывает
новый чат, отправляет промт активации, обновляет таблицу серий.

## Порядок

1. Агент видит, что пора (метрика `cmds_from_start`).
2. Готовит артефакты: `HANDOVER.md`, `TODO.md`, `PROMPT_<следующая>.md`, дневник.
3. Ставит флаг.
4. `rebirth_monitor` видит флаг, запускает rebirth-цикл.
5. Таблица серий сдвигается.
6. Новый агент читает PROMPT и стартует.

## Только A/B/C/D

E и F (Qwen, Алиса) не перерождаются. Правило оператора 26.10.

## Подробнее

См. `RAG/procedures/REBIRTH.md` и `RAG/procedures/rebirth_scope.md`.

## См. также

- [[functions/channels]]