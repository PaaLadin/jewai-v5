# SESSION_STATE — JewAI v5

**Обновлён:** 2026-11-09, 9C (Семён).
**Версия:** 0.1.0-dev.

## Текущее состояние

### Работает (проверено 9C)

- **Мост:** агент -> блок -> диск -> [AGENT REPORT]. 21/21 тестов до 9C.
- **Mainframe 8670:** 8 табов (AGENTS, MNEMO, CHAT, PERS, PROJECTS, LOGS, ROADMAP, СПРАВКА).
- **Mnemо-панель:** canvas + блоки каналов, связи.
- **Wiki /wiki:** 12 секций (8 старых + 4 от 9C: Голос, Шестерёнка, SMTP, Адаптеры).
- **Rebirth v5:** гейт 850, hold, force, cycle, PROMPT_ACTIVATION. Dry-run OK, живой цикл не прогонялся.
- **TTS notify + stop:** портировано 2026-11-08. Живой тест OK (гимн 3x30, оператор печатает -> stop).
- **Settings gear (⚙):** смена адаптера канала через UI. `deepseek/qwen/alice/google`.
- **SMTP:** через `.secret/smtp.json` (config.json убран из git).
- **Watchdog/Recovery/Autorestart:** Tools/svc.py, Tools/watchdog.py, Tools/recovery.py.
- **RAG:** 31 процедура, INDEX с порядком чтения.

### Открытые баги (см. RAG/procedures/BUGS_V5.md)

- BUG-001/007: `svc_api.py` path mismatch (панель watchdog=false при живом).
- BUG-002: `watchdog.py::_kick` без HOST.
- BUG-004: `Adapters/google.py` не задокументирован.
- BUG-006: `export_share` через CDP (не Playwright).

### Не проверено живьём

- Rebirth CDP cycle на v5 (только dry-run).
- Qwen/Alice адаптеры (каркасы есть).
- LocalAI (порт 8090) — не портирован (v6).
- STT / wake-word — в долгий ящик.

## Каналы (порты)

| Канал | Agent | CDP | Модель по умолчанию |
|---|---|---|---|
| A | 8666 | 9122 | deepseek |
| B | 8667 | 9123 | deepseek |
| C | 8668 | 9124 | deepseek |
| D | 8669 | 9125 | deepseek |
| E | 8671 | 9126 | qwen (не активен) |
| F | 8672 | 9127 | alice (не активен) |

Mainframe: 8670. DoH: 9899.

## Git

**`PaaLadin/jewai-v5`** (origin/main):
- `4c9c651` — wiki sections + RAG index + bugs
- `90a9cae` — settings gear
- `793dd7a` — doc audit + wiki tab + SMTP
- `ec5d514` — TTS notify + stop
- `ba147fc` — rebirth port v5 + audit

**`PaaLadin/jewai`** (DeepSeek live backup):
- `8b6ab17` — live extension sync (agent/background/content/manifest).

## Передача

- **Преемник:** 10C, CCAB0000-CCAB0999.
- **Порог rebirth:** 850 cmds. LastId 9C: ~CCAA9736.
- **До 850:** ~114 id.

Dixi. 9C (Семён), 2026-11-09.