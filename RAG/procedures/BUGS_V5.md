# BUGS_V5 - известные проблемы v5

Актуально 2026-11-09 (9C).

## Открытые

### BUG-001: svc_api.py читает неправильный путь
- svc_api.py: cfg.path(logs, svc, watchdog_A.json) -> logs/svc/watchdog_A.json
- svc.py пишет: Profiles/A/logs/svc_watchdog_A.json
- Следствие: панель показывает watchdog=false при работающем сервисе.
- TODO 10C: унифицировать на Profiles.

### BUG-002: ALIVE watchdog стартует но не отвечает
- watchdog.py: _kick использует Bridge.cdp.connect(port) без host.
- find_chat ищет deepseek по HOST, но host не передан.
- Следствие: ALIVE может не дойти до чата.
- TODO: передать HOST из адаптера.

### BUG-003: SystemMessages.md не описывает формат [AGENT REPORT]
- Агент получает report с полями id/op/status/stdout/stderr/next_id.
- В доке только общее описание.
- TODO: дописать секцию.

### BUG-004: Adapters/google.py есть, но не описан
- 5607 б, Google AI Studio.
- Bridge/run.py знает model=google, но документация не упоминает.
- TODO: описать в RAG.

### BUG-005: current_state.md устарел
- Указывает 21/21 тестов.
- По факту: см. последний run_all_tests.
- TODO: обновить после прогона.

## Исправлено 9C (2026-11-08/09)

- KICK_PROTOCOL.md: bridge_kick2/3 -> Tools/kick.py + POST /api/send.
- agent_layout.md: Extension ABSENT -> РЕАЛЬНО ЕСТЬ в Agents/<L>/extension.
- PANEL.md: Pip-Boy -> 15D (8 табов, мнемосхема, wiki).
- voice stop: путь stop-файла, fire-and-forget, фильтр [, __pycache__.
- rebirth: single-guard, cooldown, TABLE STALE, PROMPT_ACTIVATION.

### BUG-006: Экспорт старых чатов (share) не портирован

- В DeepSeek: `sandbox/export_share.py` через Playwright.
- В v5: Playwright НЕ переносим. Нужен аналог через Bridge/cdp.py.
- Приоритет: средний (нужен перед rebirth — сохранить старый диалог).
- TODO 10C: `Tools/export_share.py` на CDP (изолированный контекст, scroll-loop, дедуп).

### BUG-007: Mainframe/svc_api.py: путаница путей watchdog/recovery

- svc_api.py: `_read_state(cfg, ch, kind)` читает `logs/svc/<kind>_<ch>.json`
- Tools/svc.py пишет: `Profiles/<L>/logs/svc_<kind>_<L>.json`
- Симптом: панель показывает watchdog=false, хотя процесс жив
- Причина: два разных места хранения состояния
- Решение: svc_api.py должен читать из `cfg.channel_path(ch, logs, svc_<kind>_<ch>.json)`
- Приоритет: средний (ложные красные лампы)
### BUG-004 (детали): Adapters/google.py есть, не задокументирован

- Файл: `Adapters/google.py` (5607 б, Google AI Studio).
- Класс: `Google`, host: `aistudio.google.com` (или AI Studio URL).
- Bridge/run.py: `ADAPTERS[google] = (Adapters.google, Google)`.
- В RAG не описан. В wiki нет.
- Состояние: каркас, live-тест не прогонялся.
- TODO: описать в RAG/procedures/ADAPTERS.md (новый файл).