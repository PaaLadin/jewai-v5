# Rebirth v5 — перерождение агента

**Статус:** заглушка, наполняется в Ф4.

## Контракт

1. Создать новый чат в adapter DeepSeek.
2. Отправить PROMPT_<next>.md **текстом** в textarea.
3. Проверить доставку: verify_hits(3) — искать 3 маркера из PROMPT в теле чата.
4. Если verify провален — return 7, запись в rebirth_log.jsonl с полем result=fail.
5. Если успех — обновить series_table, записать old/new series + share + result.
6. Онбординг-кик: передать URL нового чата.

## Категорически не использовать

- Attach файла через input[type=file] — не работает в DeepSeek (React скрывает input, files.length=0, DataTransfer блокирован).
- Простой Enter без клика по кнопке — Алиса и DeepSeek требуют клик по aria="Отправить".

## Грабли (из старого проекта)

- rebirth_cdp.step_send: после Enter элемент не в DOM — re-query + keyboard.press + poll URL.
- doc['root'] vs doc['result']['root'] — KeyError глотался silent-pass.
- PROMPT без code fence — DeepSeek съедает ###.
- LA false-trigger: порог cmds<850 — не слать rebirth_ready.

Dixi. 12D, 2026-10-27.