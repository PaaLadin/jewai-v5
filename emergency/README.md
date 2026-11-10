# emergency/ — артефакты перерождения

**Что здесь лежит:** PROMPT_<series>.md для передачи следующему агенту, HANDOVER.md, 0_ACTIVATION.md, операторские инструкции.

**Кто читает:** Rebirth/cycle.py::load_prompt — приоритет: logs/<CH>/PROMPT.md → emergency/PROMPT.md → logs/rebirth/PROMPT.md → RAG/procedures/PROMPT.md.

**Кто пишет:**
- Агент перед rebirth (HANDOVER.md, PROMPT_<next>.md).
- Оператор (0_ACTIVATION.md — общие правила, правки руками).
- Installer копирует эту папку из source в target (10C BUG-017 fix).

**Что делать при rebirth:**
1. Агент готовит `emergency/PROMPT_<next_series>.md` (по шаблону из README).
2. Агент пишет `emergency/HANDOVER.md` — что сделано / что открыто.
3. Rebirth/cycle.py найдёт PROMPT в этой папке (раньше не искал).

**Актив в текущей сессии:**
- 10C: PROMPT_10C.md создан 9C (утерян при untrack → 268d308). Восстановить из DeepSeek/emergency/PROMPT_10C.md при необходимости.
- HANDOVER_9C.md → logs/HANDOVER_9C.md (там же, где остальная передача).

**Не путать с logs/rebirth/** — это runtime rebirth: series_table.json, lock, ready/force/hold-флаги, rebirth_log.jsonl.

Dixi. 10C (Семён), 2026-11-10 ~04:00.
