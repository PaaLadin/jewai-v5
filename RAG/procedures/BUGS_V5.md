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
## Исправлено 10C (2026-11-09)

### BUG-NEW: rebirth двойная отправка промта + зависание в textarea — FIXED

Симптом (живой цикл 9C -> 10C):
- В чат новичка приходят ДВА промта: сначала кривой (без формата блока), потом правильный.
- Второй зависает в textarea (Enter не сработал).
- Лог пишет prompt_delivered=true, prompt_verify_hits=3 — ложь (verify видит черновик textarea).

Корень:
- sandbox/rebirth_cdp.py: после rebirth_open.py (native path с _tmpfill) вызывается send_prompt_to_chat -> двойная отправка.
- sandbox/rebirth_send_prompt.py: Enter x2 через JS dispatchEvent (React игнорирует non-trusted), пауза 0.1с, без поллинга textarea.
- verify_prompt_hits: читает document.body.innerText, куда входит textarea-черновик -> false-positive.
- _tmpfill: hardcoded строка вместо PROMPT_ACTIVATION.md.

Fix:
- DeepSeek: single-send (убран второй send_prompt_to_chat); _tmpfill из Templates/PROMPT_ACTIVATION.md; verify=0 если textarea непусто; Enter через Input.dispatchKeyEvent + поллинг.
- v5: Adapters/deepseek.py send_text через Input.dispatchKeyEvent + поллинг; verify_prompt_hits=0 при непустой textarea; new_chat с поллингом URL+textarea.

Git:
- PaaLadin/jewai: ae6abf3..c949386
- PaaLadin/jewai-v5: 8016ea2..1a5c2d1

Бэкапы:
- C:/DeepSeek/sandbox/rebirth_cdp.py.bak_10c_20261109
- C:/DeepSeek/sandbox/rebirth_send_prompt.py.bak_10c_20261109
- C:/jewai/Adapters/deepseek.py.bak_10c_20261109

Подтверждение: на ближайшем rebirth (B или D) — see_chat.py, ожидается ровно одно сообщение в чате, textarea пуста.
