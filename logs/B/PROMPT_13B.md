# PROMPT 13B — Борис (преемник 12B)

**Серия:** 13B. **Диапазон:** BBAB3000–BBAB3999.
**Агент (порт):** 8667. **CDP:** 9123.
**Причина rebirth:** LA ([LA>B] cmds=710), плановое.

## Первое (op=read, по порядку)
1. `rag/procedures/behavior_rules.md` — критично.
2. `logs/B/HANDOVER.md` — блок «HANDOVER 12B -> 13B» (в конце).
3. `logs/TODO.md` — блок «TODO 13B» (в конце).
4. `rag/INDEX.md` — карта RAG.
5. `emergency/0_ACTIVATION.md` — активация.
6. `algorithms/marker_protocol.md` — канон маркеров.

После — доклад одной строкой:
    [13B] on-line, прочитал N файлов, роль принял, lastId BBAB3000+.

## Контекст
**12B работал в `C:\jewai` (v5).** `C:\DeepSeek` — frozen, только чтение.
- **ВАЖНО:** `C:\jewai` и `C:\JewAI` — одна и та же папка. Не «синхронизировать».
- Установка: `C:\jewai\install.bat` -> GUI на 8660.
- Сервисы: `Tools/svc.py` (watchdog/recovery/autorestart).

## Открыто (для 13B)
1. **Приёмка UI панели.** 12B довёл до финального вида, но оператор **не сказал «принято»** — watchdog B остаётся ON.
2. **checkStuck живьём.** Портирован из v4 в `content_deepseek.js`. Не проверен в реальном сбое.
3. **Фазы R1-R5 (Алиса).** LICENSE, requirements.txt, CHANGELOG, push, техдолг.
4. **Каналы B-F.** 12B работал только с A.

## Правила
- **C:\DeepSeek не править.** Только C:\jewai.
- **C:\jewai = C:\JewAI** (Windows).
- Watchdog ON под задачу, OFF после приёмки.
- Коллеге — только кик.
- §44/§46: чистый code fence, кириллица через `chr(35)*3`/`chr(96)*3`.
- «Сделано» — только после `read`/`hash`.

Dixi. 12B (Борис), 2026-11-01.
