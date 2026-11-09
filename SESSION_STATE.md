# SESSION_STATE - JewAI v5

**Обновлён:** 2026-11-09, 10C (Семён).
**Версия:** 0.1.0-dev.

## Текущее состояние

### Работает (проверено)

- **Мост:** агент -> блок -> диск -> [AGENT REPORT]. 24/24 набора в `run_all_tests.py` (25-й `test_export_share` + `test_cdp_find_chat` добавлены 10C, ещё не прогнаны вместе).
- **Mainframe 8670:** 8 табов (AGENTS, MNEMO, CHAT, PERS, PROJECTS, LOGS, ROADMAP, СПРАВКА).
- **Rebirth v5:** гейт 850, hold, force, cycle, PROMPT_ACTIVATION. Double-send fix (c949386/1a5c2d1). no_last_id fix (06587a9). export_share (2fda60f).
- **TTS notify + stop:** портировано 2026-11-08 (9C).
- **Settings gear (⚙):** смена адаптера канала через UI. `deepseek/qwen/alice/google`.
- **SMTP:** через `.secret/smtp.json` (config.json убран из git, 9C).
- **Watchdog/Recovery/Autorestart:** Tools/svc.py, Tools/watchdog.py, Tools/recovery.py. BUG-002 fix (host в _operator_typing, cffb605).
- **RAG:** 33 процедуры (ADAPTERS.md новый), INDEX синхронизирован.
- **Handicap:** для любого send_text (kick/outbox/report), aa5e762.
- **find_chat:** fallback только при 1 табе (BUG3a, be997e0).

### Открытые баги

См. `RAG/procedures/BUGS_V5.md`. Все P0 закрыты. Открыто: подтверждение rebirth fix на живом B/D.

### Не проверено живьём

- Rebirth CDP cycle с fixes (double-send / verify / export_share) - ждёт B или D.
- export_share на реальном share - CDP A-D сейчас down.
- Qwen/Alice/google live (google один раз, 15D).
- Onboarding вкладки (B-07 в TODO, не реализовано).

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

Записи 10C (2026-11-09):
- `c949386` (jewai) - rebirth single-send + PROMPT_ACTIVATION + verify ignores draft
- `1a5c2d1` - Adapters/deepseek: trusted Enter, verify, new_chat poll
- `bff51a8` - docs: rebirth fix in BUGS_V5 + TODO
- `06587a9` - rebirth_monitor lastId fallback via ledger (no_last_id)
- `db19fc4` - svc_api single path (BUG-007)
- `38e0205` - TODO архив + rewrite
- `cffb605` - watchdog _operator_typing host (BUG-002)
- `5af3d24` - ADAPTERS.md (BUG-004)
- `a5bb4f7` - BEHAVIOR.md §9/§10 из Jeho
- `2fda60f` - Tools/export_share.py (BUG-006)
- `aa5e762` - handicap для любого send_text
- `be997e0` - find_chat fallback (BUG3a, вариант в)

**`PaaLadin/jewai`** (DeepSeek live backup):
- `c949386` - rebirth single-send (10C)

## Передача

- **Преемник:** 11C, CCAB1000-CCAB1999 (префикс тот же CCAB).
- **Порог rebirth:** 850 cmds. LastId 10C: CCAB0206.
- **До 850:** ~644 id.
- **Готовить передачу к:** CCAB0850 (за 150 id до конца серии CCAB0999).

## Что 10C сделал за сессию

См. `logs/JOURNAL.md` записи 2026-11-09 + `RAG/procedures/BUGS_V5.md` секции "Исправлено 10C".

Кратко: 12 закрытых багов/фич (rebirth double-send, no_last_id, BUG-001/002/003/004/005/006/007, handicap, BUG3a, BEHAVIOR §9/§10, TODO архив). P0 пуст.

## Что осталось

См. `logs/TODO.md` - 16 открытых (было 173):

- P0: подтверждение rebirth на B/D.
- P2: B-06...B-12, B-30, checkStuck живьём, TEST OUT paths.
- P3/v6: LocalAI, STT «Джошуа».

Dixi. 10C (Семён), 2026-11-09.
