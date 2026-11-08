# Current state (2026-11-09)

## Что работает

- Мост: агент -> блок -> диск -> [AGENT REPORT].
- Панель 8670 (15D): 8 табов, мнемосхема, чат, персональные, проекты, логи, roadmap, справка.
- Rebirth v5: гейт 850, hold, force, cycle, PROMPT_ACTIVATION. Live-тест не прогонялся.
- TTS notify + stop: портировано 2026-11-08, живой тест OK.
- Watchdog/Recovery/Autorestart: есть, гейт оператора (не перебивают печать).
- RAG: 30 процедур, INDEX обновлён.

## Что не проверено живьём

- Rebirth CDP cycle на v5.
- Qwen/Alice адаптеры (каркасы есть).
- LocalAI (порт 8090) - не портирован.
- SMTP - см. BUGS_V5.

## Известные баги

См. RAG/procedures/BUGS_V5.md.
