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

### FEAT-NEW: handicap для любого источника текста (Mora 04.11) — FIXED

Симптом (по Mora 04.11): после [AGENT REPORT] мост должен ставить паузу 7-10с,
не писать в textarea, чтобы агент успел подумать. Действует для любого источника
(блок, кик, system message).

Уточнение 10C:
- Базовая пауза УЖЕ была в Bridge/daemon.py: self.handicap_ms из config, default 7000,
  проверка в tick() перед стабильностью. Ставилась только после [AGENT REPORT].
- Дырка: kick_buffer и outbox в _drain_* отправляли в обход, handicap не продлевался.
  Следующий [AGENT REPORT] мог уйти сразу за киком.

Fix 10C (2026-11-09):
- Bridge/daemon.py::_note_send() - helper: _last_send_at + _handicap_until = now + handicap_ms.
- Вызывается в 3 местах: _send_or_buffer, _drain_outbox, _drain_kick_buffer.
- Значит handicap действует для ЛЮБОГО успешного send_text в чат.

Проверено: Tools/tests/test_daemon.py fails=0, test_daemon_timing.py fails=0.

Git: PaaLadin/jewai-v5 (этот коммит).

### BUG3a: find_chat fallback -> неверный таб (DeepSeek redirect) — FIXED

Симптом (7C, 2026-11-02): DeepSeek после логина редиректит `chat.deepseek.com` ->
`www.deepseek.com/en`. `find_chat` fallback возвращает ПЕРВЫЙ page-таб с host,
на одном CDP могут жить DeepSeek + Qwen/Alice - прицеп к чужому табу.

Решение оператора: вариант (в) - fallback только при ровно одном page-табе.

Fix 10C (2026-11-09):
- `Bridge/cdp.py::find_chat`:
  1. Сначала точный match (host + marker `/a/chat/s/`).
  2. Иначе - смотрим все page-табы с этим host. Ровно один -> его.
  3. Ноль или несколько -> None (пусть оператор решит: закрыть лишние вкладки
     или открыть нужный чат).

Проверено: `Tools/tests/test_cdp_find_chat.py` 5/5 (exact, fallback one, fallback many,
zero, exact wins over fallback).

Git: PaaLadin/jewai-v5 (этот коммит).

### BUG-008: installer не ставит CfT, молча падает на системный Chrome — FIXED

Симптом (оператор, HERETIC): после install.bat в chrome://extensions пусто,
тост "Extension loaded" мелькает и исчезает. Profiles/<L>/extension при этом
содержит файлы (копирование работает), но Chrome 137+ их не грузит.

Корень:
- CfT (Chrome for Testing) весит 448 МБ и НЕ лежит в git (.gitignore).
- Installer искал его только в `<source>/tools/chrome-for-testing/`.
- При git clone этого пути нет. Installer писал "CfT not found, using regular
  Chrome" и продолжал с системным Chrome.
- Системный Chrome 137+ игнорирует --load-extension для unpacked ext (B-44).

Fix 10C:
- Новый `Tools/get_cft.py`: качает официальный chrome-win64.zip с
  googlechromelabs.github.io/chrome-for-testing/, распаковывает в
  tools/chrome-for-testing/. Поддерживает --check, --version, --dest, --force,
  --dry-run. Exit codes: 0 ok/present, 1 miss, 2 fail.
- Installer ищет CfT в ROOT/tools, target/tools, config.chrome_path.
  Если не нашёл - АВТОМАТИЧЕСКИ вызывает get_cft.py (1-3 мин, ~448 МБ).
  Только после провала скачивания - raise с понятным сообщением.

### BUG-009: CfT копировался ПОСЛЕ init профилей — FIXED

Симптом: тот же (Chrome не грузит расширение). Плюс системный Chrome
запускался для init профиля до того, как CfT оказывался в target.

Fix 10C:
- Поиск + автоскачивание CfT перенесены ДО `for L in letters: init profile`.
- `chrome_path` пишется в target config.json сразу, до init профилей.
- В `chrome_paths` CfT теперь ПЕРВЫЙ кандидат, системный - fallback.

Проверено:
- get_cft.py --check: OK при наличии, exit 1 при отсутствии.
- get_cft.py --dry-run: metadata fetch + URL (157.0.8103.50, win64).
- py_compile server.py OK.
- Полный install на HERETIC (operator, 2026-11-10 утро).

Git: PaaLadin/jewai-v5 (этот коммит).

### BUG-010: на HERETIC нет websocket-client -> launcher FAILED, Bridge A не стартует — FIXED

Симптом (HERETIC, установка 2026-11-09):
- install.log: "[launcher] push_storage FAILED after 3 targets: ws error: No module named 'websocket'"
- sidepanel: UNKNOWN, autodetect не находит агента
- Bridge A не стартует: нет ledger_A.json, нет активатора в чате
- Mnemo показывает agent=green (агент отвечает /ping), но lastId=-, cmds=-

Корень: installer не проверяет Python-зависимости. launcher.py и Bridge/cdp.py
импортируют `websocket` (websocket-client). На Monolith случайно стоял, на HERETIC - нет.

Fix 10C (ночь 2026-11-10):
- `requirements.txt` создан (websocket-client>=1.7.0).
- `Tools/installer/server.py::run_install`: проверка `import websocket` ДО копирования.
  Если нет - авто `pip install -r requirements.txt`. Если pip не помог - raise.

### BUG-011: sidepanel autodetect 8666..8675, installer base_port 8680 — FIXED

Симптом: агент на 8680 (новый default v5), а sidepanel ищет в старых 8666..8675.
Результат: "Поиск агента (autodetect 8666..8675)... Агент не найден. Вводи URL вручную."

Fix 10C:
- `Templates/extension/app.js`: autodetect 8660..8720 (61 порт).
- Если найдено ровно 1 - сохраняем agentUrl/channel/name в chrome.storage.local.
- Fallback: если autodetect пуст - запрос к Mainframe `/api/status` (8670),
  берём первый канал с живым агентом.

Проверено:
- get_cft.py --check, --dry-run.
- py_compile server.py OK.
- Синхронизировано на HERETIC (source + target) через SMB.
- Утром: перезагрузка HERETIC -> Startup->_10c_fix.bat -> pip install + install.bat.

### BUG-012: мнемосхема — кнопки работают (НЕ баг)

Проверено аудитом: в `Mainframe/static/index.html` inline-скрипт (16.5 КБ)
дёргает `/api/boot`, `/api/stop`, `/api/restart` по клику. Кнопки настоящие.
Не реагируют, потому что Bridge A мёртв (BUG-010). После фикса BUG-010 - работают.

### BUG-013: .agent_token в Profiles/A/extension — НЕ баг

Проверено: `agent.py::_find_token_file` walk-up от HERE находит `C:/JewAI_v5/.agent_token`
(root, install-wide). Per-channel токен не нужен. Ложная тревога.

Git: PaaLadin/jewai-v5 (этот коммит).

### BUG-020: PROMPT не находится из emergency/ (v5 vs DeepSeek) — FIXED

Симптом: оператор кладёт PROMPT_<series>.md в emergency/ (как в DeepSeek),
v5 его не находит. Rebirth/cycle.py::load_prompt искал только:
  logs/<CH>/, logs/rebirth/, RAG/procedures/

Корень:
- В DeepSeek канон - emergency/PROMPT_<s>.md + emergency/0_ACTIVATION.md.
- В v5 папки emergency/ вообще не было (ни в source, ни в target).
- load_prompt её не проверял.
- installer ignore_patterns содержал "emergency" в старых версиях (неявно через копию)
  - но так как папки не было, copytree её не создавал.

Fix 10C:
- Создана `C:/jewai/emergency/` в source (README + 36 файлов из DeepSeek/emergency).
- installer добавил emergency/ в core dirs loop.
- Rebirth/cycle.py::load_prompt расширен:
  1. logs/<CH>/PROMPT_<s>.md (v5 канон)
  2. emergency/PROMPT_<s>.md (DeepSeek канон, NEW)
  3. logs/rebirth/PROMPT_<s>.md (v5 backup)
  4. RAG/procedures/PROMPT_<s>.md (v5 backup)

Проверено:
- py_compile cycle.py OK, server.py OK.
- emergency/ создан, 36 файлов (0_ACTIVATION, HANDOVER, OPERATOR_GUIDE, PROMPT_*).
- installer core dirs содержит emergency.

Git: PaaLadin/jewai-v5 (этот коммит).

### BUG-018: rebirth.py (DeepSeek чеклист) искал PROMPT только в emergency/ — FIXED

Симптом (Борис, 2026-11-10):
- rebirth_master --channel B --live падает rc=4.
- В чеклисте: "PROMPT_14B.md: MISSING", хотя файл есть в logs/B/PROMPT_14B.md (2680 б).
- 13B применил обход: _manual_rebirth_14B.py - series_table 13B->14B вручную,
  тот же чат, last_id=BBAB3990, без отправки PROMPT в новый чат.

Корень:
- sandbox/rebirth.py::check_ready, строка 62:
  "PROMPT_%s.md" % ns: os.path.join(ROOT, "emergency", "PROMPT_%s.md" % ns)
- Чеклист видел PROMPT ТОЛЬКО в emergency/, а не в logs/B/ (где реально лежит
  per-channel PROMPT и где канон v5).

Fix 10C (патч DeepSeek/sandbox/rebirth.py):
- Добавлен _find_prompt(ns) - multi-path как в v5 Rebirth/cycle.py::load_prompt:
  1. logs/<CH>/PROMPT_<s>.md
  2. emergency/PROMPT_<s>.md
  3. logs/rebirth/PROMPT_<s>.md
  4. RAG/procedures/PROMPT_<s>.md
- Бэкап: C:/DeepSeek/sandbox/rebirth.py.bak_10c_20261110_promptpath.

Проверено:
- rebirth.py --channel B --dry-run rc=0 с временным ready_B.json.
- Чеклист: PROMPT_15B.md OK (было MISSING).
- v5 Rebirth/cycle.py уже имел emergency/ (BUG-020, тот же паттерн).

Осталось:
- 13B->14B Бориса - manual bypass, в том же чате. Реальный переход = 14B->15B
  (по 850 cmds), уже с починенным чеклистом.

---

## BUG-017: Bridge hangs forever on background processes (ИСПРАВЛЕНО 2026-11-10)

**Симптом:** `op: run` с командой `start "" /B python <long-running-server>` вешает Bridge навсегда. В `stale_A.log` нет записи, `ledger` не двигается, Recovery не срабатывает.

**Причина:** `subprocess.Popen()` в `Bridge/exec.py` передавал потомку пайпы `stdout/stderr`. Фоновый процесс (сервер) не закрывает их, `communicate()`/`wait()` ждет EOF бесконечно. Таймаут на уровне моста не убивал дочернее дерево процессов.

**Исправление (11C, Семён):**
1. `Bridge/exec.py` пишет stdout/stderr во временные файлы (`tempfile.NamedTemporaryFile`), а не в пайпы.
2. `creationflags = CREATE_NO_WINDOW | DETACHED_PROCESS` — отвязывает фоновый процесс от родителя.
3. При таймауте — `taskkill /F /T /PID <pid>` убивает всё дерево процессов (cmd.exe + python + внуки).

**Файл:** `Bridge/exec.py`, функция `op_run()`, комментарий "BUG-017 fix (11C)".

**Проверка:** запуск `start "" /B python Tools/lada_proxy.py` больше не вешает мост, `[AGENT REPORT]` приходит с `exit: 0` за 0.1-0.5 сек.
