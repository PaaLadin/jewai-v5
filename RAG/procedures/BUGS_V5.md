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
