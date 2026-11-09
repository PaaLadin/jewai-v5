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

### BUG-NEW: rebirth_monitor no_last_id (все каналы) — FIXED

Симптом: Monitor.last_id_of() делает GET http://127.0.0.1:<agent_port>/status,
но v5 agent.py отдаёт /ping, /svc_status, /live, а /status отсутствует.
Итог: lastId всегда None -> rebirth по порогу 850 не срабатывает в v5.
Это REBIRTH.md §11.8 (9C описал, не починил).

Fix 10C (вариант Б, оператор):
- Tools/rebirth_monitor.py::last_id_of - добавлен fallback на файл
  Profiles/<L>/logs/ledger_<L>.json (поле watermark, пишет Bridge/exec.py::Ledger).
- Порядок: HTTP /status (legacy, если агент расширен) -> ledger_<L>.json -> None.

Проверено:
- песочница: 5/5 (HTTP down + ledger=AAAA0042 -> AAAA0042; ledger empty -> None;
  ledger miss -> None; check_channel start AAAA0001+watermark AAAA0042 -> cmds=41;
  watermark AAAA0701 -> cmds=700 level=warn).
- Tools/tests/test_rebirth_monitor.py: 12/12 pass.
- Tools/tests/test_cycle.py: fails=0.

Git:
- PaaLadin/jewai-v5: (этот коммит)

RAG: RAG/procedures/REBIRTH.md §11.8 переписан.

### BUG-007: svc_api.py path mismatch (watchdog=false при живом) — FIXED

Симптом: панель показывает watchdog=false/recovery=false, хотя процесс жив.

Уточнение истории:
- Коммит 8016ea2 (9C) уже частично закрыл баг - svc_api читал сначала Profiles/<L>/.
- Но остался тернарный fallback на legacy logs/svc/<kind>_<ch>.json, если в Profiles
  файла нет. Значит при "legacy-only" состоянии svc_api -> True, health.py -> False.
  То есть рассинхрон возможен в граничном случае.

Fix 10C (2026-11-09):
- Mainframe/svc_api.py::_read_state - убран fallback, единый путь
  cfg.channel_path(ch, "logs", "svc_<kind>_<ch>.json").
- Теперь svc.py (write), svc_api.py (read) и health.py (read) смотрят в одно место -
  Profiles/<L>/logs/. Рассинхрон невозможен по построению.

Проверено (logs/runtime/sandbox_test_svc_10c.py, 5/5):
- Profiles only -> health=True, svc_api=True
- legacy only -> health=False, svc_api=False (было True - баг)
- state=off -> обе False
- файл отсутствует -> обе False
- svc._state_path == Profiles/<L>/logs/svc_<kind>_<ch>.json

Регрессии: Tools/tests/test_mainframe_ext.py fails=0.

Git: PaaLadin/jewai-v5 (этот коммит).

### BUG-002: watchdog.py::_kick без HOST (ALIVE не доходит) — FIXED

Симптом (по описанию 9C): watchdog._kick вызывает Bridge.cdp.connect(port) без host,
find_chat ищет deepseek по HOST, не находит, ALIVE не доставляется.

Уточнение 10C:
- К моменту проверки _kick уже передавал host (видимо починили в 11B/7C).
- Но _operator_typing(port) в том же файле вызывал connect(port) БЕЗ host ->
  TypeError -> except: return False. Значит watchdog НЕ ВИДЕЛ, что оператор
  печатает, и вставлял ALIVE поверх набора.
- Плюс мусорная строка "from Tools.launcher import _push_storage  # not used here".

Fix 10C:
- _operator_typing(port, host="chat.deepseek.com"), connect(port, host).
- main() вычисляет _h (адаптер канала) ДО вызова _operator_typing и передаёт в него.
- Убрана мусорная строка в _kick.

Проверено: Tools/tests/test_guard.py exit 0 (известный фиктивный ALERT-путь, не регрессия).
Tools/tests/test_rebirth_monitor.py 12/12 pass.

Git: PaaLadin/jewai-v5 (этот коммит).

### BUG-004: Adapters/google.py не описан — FIXED

Симптом: файл `Adapters/google.py` (5465 б) существует и подключён в Bridge/run.py,
но в RAG не было процедуры, описывающей его контракт, механику, статус.

Fix 10C (2026-11-09):
- Создан `RAG/procedures/ADAPTERS.md` (4880 б): контракт адаптера, все 4 адаптера
  (deepseek/qwen/alice/google), механика google (AI-Swing-Bridge, execCommand + CDP Enter,
  без клика по send), переключение через UI/API, история.
- INDEX.md обновлён.

Git: PaaLadin/jewai-v5 (этот коммит).

### BUG-006: export_share через CDP (не Playwright) — FIXED

Симптом: в DeepSeek sandbox/export_share.py работает через Playwright, в v5 не портирован.
Без него rebirth теряет историю старого чата (сохранение диалога до перерождения).

Fix 10C (2026-11-09):
- Создан `Tools/export_share.py` (~7000 б) на чистом CDP (websocket-client, без Playwright):
  - `Target.createBrowserContext` -> `Target.createTarget` -> attach -> `Page.navigate`.
    Изолированный browser context: cookies не передаются, share публичный.
  - Scroll-loop: самый большой скроллируемый контейнер, innerText постранично,
    дедуп по строкам, скролл на --step, до упора или --max_steps.
  - NDA: блоки [NDA]...[/NDA] -> [NDA-REDACTED].
  - Header: source, final_url, title, exported, bytes.
  - Cleanup: Target.closeTarget + Target.disposeBrowserContext.
- Добавлен в `Tools/run_all_tests.py`: `test_export_share.py` (14/14 pass, без живого CDP).

Usage: `python Tools/export_share.py --url <share_url> --out <path.md> --port 9223`

Живой тест на реальном share: не проведён (CDP A-D сейчас не запущены).
При следующем rebirth C/D (после see_chat) - проверить на живом share.

Git: PaaLadin/jewai-v5 (этот коммит).
