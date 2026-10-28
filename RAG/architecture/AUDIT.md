# AUDIT JewAI v5 — Ф1

Аудит старого C:/DeepSeek/ для переписывания с нуля.
Правило: код не копируется, фиксируются контракт + костыли + решение.

## 1. sandbox/cdp_client.py (2743 б)

**Контракт:**
- HTTP /json/list к CDP-порту, поиск вкладки чата по URL-маркеру и известным хостам (deepseek, qwen, alice, yandex).
- WebSocket к webSocketDebuggerUrl: call(method, params) — JSON-RPC по id; eval(expr) — Runtime.evaluate с returnByValue.
- Авто-обёртка стрелочных функций в вызов, кроме самовызывающихся.
- connect_chat(port) — вернуть (session, target).

**Костыли:**
- websocket-client как sync-зависимость (asyncio не тащим) — сохранить.
- Fallback по KNOWN_CHAT_HOSTS — следствие разных URL-паттернов SPA. Причина валидная.
- Неявная автообёртка стрелок — ловушка двойного вызова. Лучше два явных метода.

**Решение v5:** перенести концепцию. Переписать. Убрать неявную авто-обёртку: eval_expr(строка) и eval_fn(стрелка) раздельно.

## 2. sandbox/bridge_kick2.py (2908 б)

**Контракт:**
- CLI: --port, --text, --prefix, --dry, --wait-empty.
- Найти textarea, дождаться пустоты, при занятой — отказать (черновик сохранить).
- Ввод: очистка value + Input.insertText + verify.
- Отправка: два Enter (keyDown+keyUp) с паузами; финальная проверка textarea == пусто.

**Костыли:**
- --prefix дублирует логику caller'а. Убрать, caller сам готовит строку.
- Verify value — эвристика. Оставить, но обозначить как best-effort.
- Тайминги (0.2/0.8/1.5/2.0) — магические числа. Вынести в config.

**Решение v5:** контракт сохранить, тайминги в config, prefix убрать, dry + wait-empty сохранить.

## 3. sandbox/bridge_kick3.py (3692 б)

**Контракт:**
- CLI: --port, --text, --wait-empty, --dry.
- Селекторы SPA: qwen .message-input-textarea, alice .AliceInput-Textarea, fallback textarea:not([readonly]):not([aria-hidden=true]).
- Ввод через value setter + input event.
- Отправка: Enter первым (Qwen Vue SPA игнорирует click), затем Alice «Отправить», затем click-fallback по send-button.

**Костыли:**
- Список селекторов зашит в кикер — ломается при изменении SPA. Вынести в адаптер по хосту.
- Alice-особый путь живёт внутри кикера, а не в отдельном адаптере. Так и просится в адаптерную модель.

**Решение v5:** слить kick2 и kick3 в один kicker с адаптерами по хосту. Enter-first — канон, click — fallback. Тайминги в config.

## 4. sandbox/read_panel_state2.py (964 б)

**Контракт:**
- CLI: порт (default 9222).
- Найти target sidepanel.html, открыть CDPSession, eval document.body.innerText, отдать первые 3000 символов в stdout.

**Костыли:**
- Перенос stdout в utf-8 через TextIOWrapper — симптом Windows cp1251. В v5 решать один раз на старте процесса.
- Хардкод 3000 — вынести в аргумент.

**Решение v5:** модуль нужен как диагностика. Читать конкретные поля панели (lastId, статус), возвращать JSON, не сырой текст.

## 5. sandbox/svc.py (10702 б)

**Контракт:**
- CLI start/stop/status, --channel A-F, --kind watchdog|recovery|autorestart.
- start: spawn процесса pythonw, detached, без окна (CREATE_NO_WINDOW|DETACHED_PROCESS).
- Пишет pid-файл logs/svc/<kind>_<CH>.json, состояние <kind>_<CH>.json.
- stop: taskkill /T /F по pid, снимает pid-файл, пишет state=off даже если процесса нет (дыра 11.10).
- status: JSON {channel, agent, cdp, services{watchdog,recovery,autorestart}}, uptime считает от started.
- autorestart — глобальный, ключ G.

**Костыли:**
- AGENT_PORT/CDP_PORT зашиты таблицей; в v5 — из config.json.
- ROOT зашит `C:\DeepSeek`; в v5 — config.root().
- "record state=off даже без процесса" — фикс дыры, но свидетельство что state-файл — источник правды, а не процесс. В v5 инвертировать: процесс первичен, state — производная.
- Опция --by (кто включил) через function attribute — атрибут-хак. В v5 — явный параметр.

**Решение v5:** переписать, config-driven порты и ROOT, --by явным аргументом, state-файлы производные.

## 6. sandbox/watchdog.py (5519 б)

**Контракт:**
- Ping url с X-Token (из .agent_token), threshold N фейлов → пишет ALERT.json.
- Восстановление: любой OK снимает ALERT, fails=0.
- Опция --check-dom: через read_heartbeat.py по CDP проверяет свежесть dsbHeartbeat. stale → PANEL-STUCK в лог (но не в ALERT, только лог).
- --once для теста.

**Костыли:**
- `subprocess` используется в _nw_flags(), но не импортирован (NameError — латентный баг). В v5 убрать функцию или импортировать.
- Два канала сигнала (ping и dom) живут в одном процессе, но ALERT пишется только по ping. Дом-сигнал — лог, не тревога. В v5 решить явно: два независимых сигнала или один с агрегацией.
- .agent_token в ROOT; в v5 — secrets-слой.

**Решение v5:** переписать, импорт починить, два сигнала — единая модель health с двумя probe.

## 7. sandbox/recovery_loop.py (3228 б)

**Контракт:**
- CLI --port (CDP), --cooldown, --interval.
- Каждый interval: panel_alive = read_panel_state.py + эвристика по строкам (no-answer/content no/content bad).
- Если мёртв: с cooldown запускает recover_chat2.py.
- Stop-файл logs/svc/recovery_<port>.stop.

**Костыли:**
- panel_alive через парсинг текста (подстроки в нижнем регистре) — хрупко. В v5 read_panel_state2 отдаёт JSON с полями; health-check по полю.
- Stop-файл — нетипичный способ; в v5 — SIGTERM или явный control-файл с JSON.
- recover_chat2.py — внешний, отдельный процесс; в v5 — модуль внутри.

**Решение v5:** переписать, health-check по JSON-полям, остановка через сигнал.

## 8. sandbox/autorestart.py (6403 б)

**Контракт:**
- Глобальный процесс, interval 30с.
- Сканирует ALERT_*.json + ALERT.json.
- Если агент на порту мёртв: scan_live_paths() через wmic (кэш logs/svc/agent_paths.json), restart через Popen python agent.py <port>, ждёт 4с, ping. Успех → ALERT снят, state обновлён.
- FALLBACK: 4 порта → один agent.py (устаревший путь).

**Костыли:**
- wmic deprecated (Windows 11 удаляет). В v5 — psutil или реестр путей от config.
- FALLBACK на extension/agent.py — статический путь, будет врать. Выкинуть, config даёт путь.
- Ждать 4с в restart — магия. В v5 — poll ping с таймаутом.
- STATE_FILE runtime/lp_spawned.json — параллельное состояние, дублирует svc.py state-файлы. В v5 — один источник.

**Решение v5:** переписать, psutil вместо wmic, путь из config, poll вместо sleep, единый state.

## Свод по Services

Все 4 модуля — переписать. Общее: config-driven порты/пути, единый state-слой, health как JSON-модель (ping + dom + panel), один watchdog-цикл + один recovery-цикл на канал.

## 9. sandbox/find.py (2846 б)

**Контракт:**
- CLI: pattern [--text] [--dir].
- os.walk с пресетом исключений (git, runtime, models, chrome-*-data, backups, node_modules, .venv, ...).
- --text: поиск подстроки в файле (case-insensitive, до 100 хитов, обрезка строки 150).
- Иначе: fnmatch по basename.
- Префикс "relpath:line: text", финал "--- hits=N ---".

**Костыли:**
- Пресет исключений зашит в файл; в v5 — из config, с переопределением CLI.
- --text через io.open построчно без mmap — медленно на больших файлах. Приемлемо (исключения уже отсекли мусор).
- Ограничение 100 хитов и 150 символов — магия. В v5 — параметры.

**Решение v5:** переписать, пресет в config, лимиты — параметры, вывод JSON как опция.

## 10. sandbox/council_chat/say.py (1334 б)

**Контракт:**
- CLI: <CH> <text> [<to=ALL>].
- Append JSONL в council_chat/chat.jsonl: {ts, time, from, to, text}.
- Никакой сети, только файл.

**Костыли:**
- Валидация канала зашита ("A","B","C","D") — нет E/F. В v5 — из config.
- Нет ротации/размера файла. В v5 — ротация.
- Нет валидации to (ALL/operator/канал/LA) — молча пишет что угодно.

**Решение v5:** переписать, каналы из config, валидация to, ротация файла.

## 11. sandbox/see_chat.py (2384 б)

**Контракт:**
- CLI: --cdp <port> --out <path> [--text-only].
- grab: Page.captureScreenshot → base64 → PNG.
- dump_text: document.body.innerText, первые 8000 символов → txt.
- Поиск target по "/a/chat/s/" или "chat.deepseek.com".

**Костыли:**
- Хардкод маркеров URL — не знает qwen/alice. В v5 — общий find_chat_target из cdp_client.
- maxlen=8000 — магия, вынести.
- Путь дефолтный logs/A/ — доминирует канал A. В v5 — из --cdp → канал.
- timeout=30 на скриншот — фикс зависаний SPA. Оставить, в config.

**Решение v5:** переписать, общий поиск target, канал из --cdp, maxlen в параметр.

## 12. sandbox/doh_proxy.py (3089 б)

**Контракт:**
- Локальный HTTP CONNECT-прокси на 127.0.0.1:<port> (default 9999).
- Резолвит через DoH (8.8.8.8, 1.1.1.1), кэш в памяти, обход блокировок DNS.
- CONNECT: host:port → socket.create_connection(ip, port) → двунаправленный pipe.
- Только CONNECT; другой метод → 400.

**Костыли:**
- ssl.CERT_NONE + check_hostname=False — нет валидации DoH-сертификата. Приемлемо для public DoH, но в v5 — явный комментарий и pin.
- Кэш без TTL — вечный. В v5 — TTL.
- Два потока на соединение, без управления — утечка threads при ошибках. В v5 — селектор или явное закрытие.
- Только A-записи; IPv6 нет. В v5 — решить (или явно задокументировать IPv4-only).

**Решение v5:** переписать, кэш с TTL, pin сертификата, ограничение потоков, IPv4-only явно.

## Свод по Tools

Все 4 модуля нужны в v5. find.py → Tools/find.py, say.py → Mainframe/council/say.py (или RPC-обёртка над chat.jsonl), see_chat.py → Tools/see.py, doh_proxy.py → Tools/doh_proxy.py. Общее: параметры из config, никаких хардкодов путей/портов/каналов внутри.

## 13. launchers/start-<CH>.ps1 (3591-3701 б, шаблон на 6 каналов)

**Контракт:**
- Per-channel: грохнуть старый Chrome этого канала (graceful CloseMainWindow → force), поднять новый с --user-data-dir=runtime/chrome/<CH>, --remote-debugging-port=<CDP>, --load-extension=<ext из config.channels.<CH>.extension>, --proxy-server=127.0.0.1:9999.
- Обязательные флаги Chrome: --disable-backgrounding-occluded-windows, --disable-renderer-backgrounding, --disable-background-timer-throttling, --no-first-run, --no-default-browser-check, --restore-last-session, --hide-crash-restore-bubble.
- Перед стартом: fix_profile_exit.py на профиль; при первом запуске (нет Default/Preferences) — открыть стартовый URL.
- Ждёт 8с, проверяет CDP через /json/version.
- Запускает agent.py <port> через pythonw, Hidden.

**Костыли:**
- $root = "C:\DeepSeek" зашит. В v5 — аргумент/config.
- Логика выбора URL по extension/model — свалка из трёх ветвлений. В v5 — config.channels.<CH>.start_url.
- Ожидание 8с фиксированное. В v5 — poll /json/version с таймаутом.
- 6 почти идентичных файлов (генерятся). В v5 — один скрипт + параметр <CH>.

**Решение v5:** один launcher с <CH>, конфиг-driven, poll вместо sleep.

## 14. launchers/stop-all.ps1 (1145 б)

**Контракт:**
- Убить все python/pythonw с agent.py и *root* в cmdline.
- Убить python с launch_server.py.
- Убить все chrome с runtime\chrome\<A..F> в cmdline.
- Сигнатура: сопоставление по фрагменту командной строки, не по pid-файлу.

**Костыли:**
- Хардкод путей/имен. В v5 — config.
- Фильтр по chrome только A-F; если каналов станет 8 — молча не убьёт. В v5 — из config.letters.
- Игнор pid-файлов (kill по cmdline) — работает, но дублирует svc.py. В v5 — единый control: stop по pid-файлу или cmdline, но не оба.

**Решение v5:** переписать на config.letters, использовать pid-файлы из svc, единый код остановки.

## 15. launchers/create-shortcut.ps1 (596 б)

**Контракт:**
- Создать Desktop\jewai.lnk на powershell.exe -File launchers/boot-all.ps1, Minimized.

**Костыли:**
- Путь Desktop через .NET; работает. В v5 — сохранить.
- Хардкод $root. В v5 — параметр.

**Решение v5:** оставить почти как есть, параметризовать корень.

## 16. launchers/boot-all.ps1 (5957 б)

**Контракт:**
- Читает config.json (letters, channels, chat_port).
- 1. doh_proxy.py --port 9999 (если не запущен).
- 2. Все агенты: agent.py <port> через pythonw, Hidden.
- 3. Все Chrome: профиль runtime/chrome/<CH>, CDP, --proxy-server=127.0.0.1:9999, first-run -> deepseek.
- 4. council_chat/server.py.
- 4b. mail_bot (если есть скрипт и .smtp_token).
- 4c. la_rebirth_monitor --loop 1200 --rebirth-monitor.
- 5. Health: ping всех агентов, /json/version CDP, /api/health чата.
- Логи в logs/boot.log.

**Костыли:**
- Всё зашито: имена скриптов, порты (9999), пути. В v5 — таблица сервисов в config.
- Проверка "уже запущен" по cmdline-паттерну — дублирует svc.py. В v5 — через svc.status.
- Фиксированные sleep (1,3,2,6,5,2,2) между шагами — magic, в v5 — wait-for-ready с таймаутом.
- mail_bot / la_rebirth_monitor в boot-all → каждый канал зависит от чужого проекта. В v5 — модули, отключаемые флагом.
- chat_port default 8770 — совпадает с /api/health, но панель сейчас 8670 (v5 ROADMAP). Расхождение — зафиксировать при переносе.

**Решение v5:** переписать как Boot orchestrator: список сервисов из config, parallel start where safe, wait-ready с таймаутом, health = http-проверки.

## 17. launchers/boot-min.ps1 (3301 б)

**Контракт:**
- Минимальный старт: A-D + Chrome A-D + server, БЕЗ doh/mail/rebirth/lada, Chrome без --proxy-server.
- Удобно для теста после правок.

**Костыли:**
- Хардкод letters @(A,B,C,D). В v5 — профиль boot (min/full) из config.
- Дубль логики boot-all. В v5 — один boot с профилями.

**Решение v5:** выкинуть. Заменяется boot --profile=min.

## Свод по Launchers

Переносим идею: per-channel launcher (или один с <CH>), boot orchestrator (профили min/full), stop (единый), create-shortcut. Всё config-driven, никаких sleep-ов без wait-ready, никаких путей в коде.

## 18. extension/agent.py (17223 симв., расширение для DeepSeek/Qwen/Alice)

**Контракт:**
- HTTP-сервер на порту канала (8766-8772, боевые), X-Token auth.
- GET /ping (ok, root, version, last_ts, ago), GET /health (uptime, stats).
- POST: /read, /write (sha256, unchanged), /list, /delete, /mkdir, /hash, /run (timeout, kill-tree на Windows), /sandbox (tempdir + files), /voice, /notify, /notify-stop.
- safe_path: escape-защита, всё внутри ROOT.
- spawn_detached: `start ...` и `cmd /c start ...` → Popen detached без окна; run_with_killtree убивает дерево при таймауте.
- _port_busy: TCP-connect + bind без SO_REUSEADDR → guard от дубля.
- ALIVE: _LAST_TS обновляется только на реальных операциях (svc-read не считается).
- Копии: extension_qwen/agent.py и extension_alice/agent.py (16449/17072 симв.) — идентичны по контракту.

**Костыли:**
- ROOT зашит через `_HERE.parent if _HERE.name=="extension"`, но конфиг не читает — таблица портов задаётся снаружи (launcher).
- `start ... /B python ...` парсится вручную (_strip_start) — исторический обход Windows. В v5: Popen([...]) с параметром detached.
- /sandbox с копированием файлов в tempdir — рабочий, но убивает кэш; в v5 — явные параметры copyin/copyout.
- /voice и /notify зависят от внешних скриптов (voice.py, notify_me.py) — убрать в v5 или перенести.
- version 4.0.1 захардкожен; v5 — из VERSION-файла.

**Решение v5:** переписать как Bridge/exec.py+read.py+daemon.py (в ROADMAP Ф2). Оставить: safe_path, X-Token, sha256, kill-tree на таймауте, ALIVE-семантику. Убрать: парсинг `start`, voice/notify (или перенести в отдельный модуль).

## 19. extension/content.js (24993 симв., DeepSeek)

**Контракт:**
- Инжект на chat.deepseek.com: parseBlocks из pre/code последних 3 ассистентских сообщений (SCAN_LAST_MSGS=3).
- Dedupe по id: recentlySentIds в chrome.storage (переживает reload); RECENT_LIMIT=500.
- Скан каждой 2с, stable-gate 1200мс, коалесценция 2500мс, MIN_GAP 5000мс.
- typeAndSend: value-setter + input event + 2 раунда Enter (keydown/keypress/keyup).
- fmt: [AGENT REPORT] с id/op/status/exit/stdout/error/path/sha256/content.
- checkStuck: Type 1 Server unavailable → клик Continue; Type 2 Leaked tag/Chinese/system → Regenerate, но не трогать если в ответе есть валидный блок.
- Type 3 (detectTalkWithoutBlock): рассуждения без блока → отправить format reminder.
- checkAlive: читает logs/svc/watchdog_<CH>.json через agent /read, если state==on и ago>SILENCE_MS(180) → отправить ALIVE_TEXT.
- watermark dsbHeartbeat: document.documentElement.dataset.dsbHeartbeat каждые 3с.
- inflight auto-reset через 45с; ALIVE_REPEAT 30 мин; PANEL-STUCK через 90с.

**Костыли:**
- Всё в одном 25КБ файле, много if-else. В v5: daemon (цикл) + exec (парсер+отправка) + adapters (deepseek).
- checkAlive читает файл svc в обход API — дыра; в v5 — svc.status().
- 2 раунда Enter — фикс «иногда не отправляет». В v5 — один, проверка по изменению последнего сообщения.
- PANEL-STUCK отправляется как сообщение агенту (!) — это шум; в v5 — в лог-панель.
- Type 3 (talk detect) — эвристика по русским глаголам-обещаниям; в v5 — системный промт + жёсткий парсер.
- Леджер хранится и в chrome.storage, и в памяти; state.ledger в SV-сервере — третий источник. В v5 — один.

**Решение v5:** в v5 extension нет. Концепции: парсер блоков, dedupe по id, stable-gate, коалесценция, auto-reset — переезжают в Bridge/exec.py + Bridge/daemon.py.

## 20. extension_qwen/content_qwen.js (11896 симв.)

**Контракт:** тот же, что content.js. Отличия:
- normalizePre: innerText + выкидывание gutter-номеров строк + NBSP->пробел.
- Селекторы зон: .response-message-content, .custom-qwen-markdown, .qwen-markdown, [class*=response-message], [class*=markdown].
- Qwen: React _valueTracker обязателен — set + ta._valueTracker.setValue("").
- trySendQwen: native click на .message-input-right-button-send, затем Enter, до 3 попыток.

**Костыли:**
- checkStuck скопирован из content.js, но фильтр по .ds-message не работает (это deepseek-класс). Реальная проверка «Type 2» на qwen не срабатывает. В v5 — не актуально (extension нет), но зафиксировать урок: копипаста между SPA-адаптерами ведёт к мёртвым ветвям.

## 21. extension_alice/content_alice.js (10477 симв.)

**Контракт:** тот же. Отличия:
- normalizePre: только NBSP + CRLF (gutter нет).
- Зоны: .FuturisMarkdown, .MarkdownText, [class*=Markdown], [class*=answer].
- textarea .AliceInput-Textarea, fallback textarea:not([readonly]):not([aria-hidden]).
- typeAndSend: только Enter (без click), 2 раунда.
- checkStuck: копия из content.js с .ds-message — на Алисе не работает.

**Костыли:** те же, что qwen. Плюс дублирование логики — три почти идентичных моста.

## 22. Что НЕ переносим в v5

- extension/manifest.json, sidepanel.html, sidepanel.js, background.js — Chrome-расширение. По ROADMAP v5 расширения нет.
- Все .bak_* (32 файла) — история, не код.
- Мёртвые ветви checkStuck в qwen/alice (копия из deepseek) — урок, не код.

## Свод по Extension

Переносим концепции, не код: парсер блоков (state-machine по маркерам), dedupe по id (Ledger с персистом), stable-gate (изменение pre-count), коалесценция + MIN_GAP, auto-reset inflight, kill-tree на таймаут. Убираем: checkStuck-эвристики, ALIVE-через-файл, watermark dsbHeartbeat, voice/notify.

## 23. sandbox/rebirth_table.py (2696 б)

**Контракт:**
- CLI: --channel A-F [--share URL] [--new-url URL].
- Читает logs/rebirth/series_table.json, для канала делает шаг: current_series = next_series; range = next_range; next_series = _inc_series (4B→5B); next_range = +1000; last_id = range[0].
- Пишет chat_url/share_url, last_id_source.
- Синхронизирует logs/session_<CH>.json через sync_session_start.py.
- Сбрасывает ledger через rebirth_reset_ledger.reset(ch).

**Костыли:**
- _inc_series парсит "4B" регэкспом; падение при другой форме — молча вернёт исходное. В v5 — явная схема серий.
- subprocess для sync_session_start и import для reset_ledger — два разных стиля. В v5 — единый API.
- ROOT через portable_root.find_root(__file__) — единственный правильный способ в старом; в v5 — config.root().

**Решение v5:** переписать как Rebirth/table.py с явной моделью Series (int, letter), атомарной записью JSON, единым методом advance().

## 24. sandbox/rebirth_onboard.py (4014 б)

**Контракт:**
- CLI: --newcomer X [--new-url URL] [--dry-run].
- Выбор соседа по кругу A→B→C→D→...→A, начиная после newcomer.
- Кандидат: lastId%1000 в [50, 800) — не на старте, не на пороге.
- Отправляет соседу kick с ONBOARD_MSG: представиться, познакомиться, через 5 мин — инструкция.

**Костыли:**
- CDP из config с фолбэком на словарь — сохранить подход, но убрать фолбэк (config — единственный источник).
- PANEL через read_panel_state.py (сырой текст) — хрупко. В v5 — read_panel_state2 API.
- KICK через bridge_kick2.py subprocess — ок, но kick2 для A-D; для E/F нужен kick3. В v5 — единый kick API по каналу.

**Решение v5:** переписать как Rebirth/onboard.py: neighbor-selection с явной моделью серии, kick через общий модуль.

## 25. sandbox/rebirth_ready.py (4172 б)

**Контракт:**
- CLI: --channel X [--force-note] [--check-only].
- Барьер: REBIRTH-READY ставится только при limit (переполнение) или cmds>=850.
- Hold-режим: logs/rebirth/hold_<CH>.flag — порог отключён, ждём переполнения.
- Иначе отказ.
- Флаг: logs/rebirth/ready_<CH>.json с cmds, limit, note.

**Костыли:**
- cmds считается как lastId - start из series_table; при рассинхроне таблицы даст ложное. В v5 — читать cmds из API агента.
- chat_limit.py subprocess — детект переполнения по тексту. В v5 — тот же subprocess, но exit-code.
- THRESHOLD 850 захардкожен — вынести в config.

**Решение v5:** переписать как Rebirth/ready.py, порог из config, check через API.

## 26. sandbox/rebirth_master.py (7247 симв.)

**Контракт:**
- CLI: --channel X [--dry-run|--live].
- 1. Проверка флага ready_<CH>.json (нет — выход 3).
- 2. Порог-гейт: limit_hit (чат переполнен) ИЛИ force_<CH>.flag ИЛИ hold-режим (ждёт переполнения) ИЛИ cmds>=850; иначе выход 7.
- 3. Чеклист (rebirth.py --dry-run) — выход 4 если не прошёл.
- 4. lock (rebirth.lock, TTL 1 час).
- 5. rebirth_cdp.py --live (timeout 300).
- 6. Из rebirth_log.jsonl достать new_url.
- 7. rebirth_onboard.py --newcomer <CH> --new-url <new_url>.
- finally: снять флаг, release lock.

**Костыли:**
- Много if-elif в гейте. В v5 — отдельная функция check_gate(ch) -> verdict.
- limit_hit и force и hold и cmds — 4 разных пути. В v5 — единый Policy.check().
- Пути логируются "spr_run =" — опечатка в коде (переменная не используется). В v5 — чисто.
- new_url берётся из jsonl реверсом — работает, но хрупко (зависит от формата). В v5 — cdp возвращает new_url через stdout JSON.

**Решение v5:** переписать как Rebirth/master.py: orchestrator с явными шагами, каждый шаг возвращает Result.

## 27. sandbox/rebirth_cdp.py (20856 симв.)

**Контракт:**
- CLI: --channel X [--dry-run|--live].
- Загружает series_table, заполняет 0_ACTIVATION.md плейсхолдерами (из next_range, не текущего) → emergency/_runtime/0_ACTIVATION_<series>.md.
- Playwright connect_over_cdp на CDP канала.
- step_share: клик по ds-button top-right → "Create public link" → "Create and copy" → парсинг URL из body. Запись share_links.jsonl + export_share.py выгрузка в logs/<CH>/conversations/<series>_share.md.
- rebirth_open.py --cdp <port> --fill-file <tmpfill> --out <json>: создаёт новый чат, вставляет текст (activation header + PROMPT тело).
- send_prompt_to_chat (из rebirth_send_prompt): текстовая доставка PROMPT.
- verify_prompt_hits: ищет 3 маркера из PROMPT в теле чата (>=1 = delivered).
- При отсутствии new_url — rebirth_log FAIL, таблица НЕ сдвигается, exit 6.
- При недоставке PROMPT — таблица сдвигается, rebirth_log FAIL, exit 7.
- rebirth_table.py --new-url --share.

**Костыли:**
- Playwright — по ROADMAP v5 виснет на SPA, не переносим. В v5 — нативный CDP (Bridge/cdp.py).
- attach файла (input[type=file], DataTransfer) — физически не работает в DeepSeek, уже отключён (attach disabled). В v5 — только текст.
- step_share — набор эвристик по классам ds-button. В v5 — адаптер DeepSeek, селекторы централизованы.
- export_share через subprocess — отдельный скрипт. В v5 — модуль.
- send_prompt_to_chat импортируется — но идёт из rebirth_send_prompt.py, отдельного модуля. В v5 — часть адаптера.
- verify_prompt_hits по тексту — эвристика (ищет обрывки). В v5 — конкретные маркеры: "Ты — 14D", "Диапазон id", "behavior_rules".

**Решение v5:** Rebirth/cdp.py — обёртка над Bridge/cdp.py (нативный CDP), только шаги create_chat / send_prompt / verify_prompt_hits / share. Никакой Playwright. attach — только текст.

## Свод по Rebirth

5 модулей, все переписываются. Ключевые концепции:
- series_table как единый источник истины (advance по шагам).
- Порог-гейт (limit | force | hold | cmds>=850) — в отдельной функции.
- Lock с TTL.
- Activation template с подстановкой плейсхолдеров, PROMPT отдельным файлом.
- Attach только текст (CDP file input в SPA ненадёжен).
- Verify prompt по маркерам в теле.
- Лог rebirth_log.jsonl + share_links.jsonl.

Уроки: Playwright на SPA — виснет. Attach файла — не работает. Verify по эвристике — недостаточно, нужны явные маркеры.

## 28. sandbox/council_chat/server.py (73040 симв., 17 частей)

**Контракт (общий):**
- HTTP-сервер на порту из config.chat_port (default 8770), bind из config.bind.
- Каналы из config.channels (name, agent, cdp, color, todo, extension, prefix).
- Прокси в режиме auto-detect CDP-портов E/F (9226/9227) → kick3, остальные → kick2.

**Ключевые подсистемы:**

### 28.1. chat.jsonl (общий чат)
- append_message/load_messages: append JSONL, каждый {ts, time, from, to, text}.
- _dedup_check(frm, to, text) — 5-секундное окно, до 30 записей. Защита от двойного клика.
- API GET /api/messages, POST /api/send.
- PAUSE-ALL: если pause_all.json.on, писать может только оператор (иначе 403).
- Broadcast: оператор to=ALL → kick_all("[COUNCIL] Оператор: ..."), to=<CH> → kick в канал + append в TODO.

### 28.2. Персональные чаты
- chat_<CH>.jsonl, load_personal/append_personal.
- next_personal_id: "Z"+CH+"AA"+NNNN для оператора, X+"Z"+"AA"+NNNN для агента.
- API GET /api/chat/<CH> (последние 200), POST с ACL (только оператор или сам CH).

### 28.3. Status / health
- collect_status: каналы + ресурсы (rag/sandbox/council/doh) + links + mainframe. TTL 2с.
- compute_progress: cmds_from_start по lastId/startId. Логика переноса серии (AAAA→AAAB) — не сбрасывает счётчик.
- risk_level: зелёный/жёлтый/красный/blink. Пороги 500/800/1200, только для A.
- collect_health: параллельный опрос panel_content + panel_lastid + svc_status по всем каналам. TTL 60с.
- Alerts: content_dead, agent_dead, panel_timeout, watchdog_off. Пока только информационные, без авто-действий.
- read_svc_state: проверка pid через _pid_alive (сверка Name + CommandLine). Дыра 11.10: state=on при мёртвом pid → False, не None.
- prewarm: заполняет health-кэш при старте в фоне.

### 28.4. Launchpad (boot/stop/restart по блокам)

- Блоки: server(self, не убивается), agent:<CH>, chrome:<CH>, doh, mailbot, rebirth, lada(info).
- lp_status: netstat -ano (кэш 2с) + _lp_cdp_ok (CDP-проба с кэшем 15с).
- _lp_pid_alive: ctypes OpenProcess + GetExitCodeProcess (мгновенно).
- _lp_spawn: Popen detached без окна, pid в runtime/lp_spawned.json.
- lp_boot("all"): doh -> agents -> chromes -> mailbot -> rebirth.
- lp_stop("all"): rebirth -> mailbot -> chromes(reverse) -> agents(reverse) -> doh -> stray pythons проекта (по ROOT в cmdline, кроме self).
- lp_restart: stop -> wait-free (netstat опрос до 10с) -> boot.
- API POST /api/boot, /api/stop, /api/restart с {target}.
- REQLOG: api_requests.log с UA/referer/target/from.
- Защита: /api/stop с target=server — отказ (self).

### 28.5. Совещание / пауза / ALIVE
- MEETING_FILE: meeting.json.on -> kick_all("[MEETING]...").
- PAUSE_ALL_FILE: pause_all.json.on -> kick_all("[PAUSE-ALL]"), оператор-only запись.
- POST /api/meeting, /api/pause_all, /api/pause, /api/resume, /api/close, /api/open — все кикают.
- Инвариант: оператор всегда может писать (bypass PAUSE-ALL).
- POST /api/alive: flags/alive_<CH>.json + kick "[COUNCIL] ALIVE? <CH>".
- POST /api/alive_ack: ack_ts. alive_button_state: green<10с / yellow<45с / grey.

### 28.6. Static / fs / LocalAI
- GET /, /dashboard.html, /style.css, /app.js, /pers.js, /mnemo.js, /launchpad_live.js, /localai.js.
- GET /fs/<rel>: браузер внутри ROOT (resolve+relative_to -> 403 на escape). MIME по suffix.
- GET /api/logs?name=chat|agent|svc|server — хвосты.
- GET /api/roadmap?name=X, POST /api/roadmap — logs/roadmap_state/<name>.json.
- GET /api/localai/status: llama :8081/v1/models, server :8090/health, RAG.
- POST /api/localai/query: проксирует text+temperature+max_tokens+tools, timeout 600.

**Костыли:**
- import urllib.parse трижды (дублирование).
- read_last_id — no-op (кэш без вызова CDP), наполняется panel_lastid.
- compute_progress: недостижимый код после return (две ветки возвращают раньше cmds = num_last - num_start). Мёртвый, безвредный.
- _lp_pid_alive: ctypes.windll — Windows-only.
- _kill_all_rebirth_monitors через wmic — deprecated (Windows 11).
- _lp_spawned.json: 3-й источник состояния. В v5 — один реестр сервисов.
- collect_health: TTL 60с, prewarm гоняет параллельно.
- REQLOG без ротации.
- localai proxy без auth — на 127.0.0.1, приемлемо.

**Решение v5:** разбить на модули:
- Mainframe/http.py — HTTP + роутинг (7 роутов ROADMAP).
- Mainframe/api.py — status, projects, chat_url, boot/stop/restart.
- Mainframe/launchpad.py — блоки + spawn/stop/restart через psutil.
- Mainframe/council.py — chat.jsonl + personal + dedup + kick.
- Mainframe/static.py — index.html, style.css, app.js.
- llm.py — сетевой LLM (ip:port), пока заглушка.
Убрать: тройной import, мёртвый код, wmic, lp_spawned.json.

## Свод по Mainframe

Server — монолит 73 КБ, содержит: HTTP-роутинг, чат, персональные каналы, status/health, launchpad, meeting/pause, static+fs, localai proxy. В v5 разбивается на 6 модулей (см. 28.6).

### Раздел 29. Replay-guard для v5 (урок этой сессии)

**Инцидент:** при работе 13D (28.10) 4 раза приходили `[AGENT REPORT]` с op=write для блоков, которые не отправлялись явно. Файлы при этом реально появлялись на диске с осмысленным содержимым. Похоже на replay старых блоков из истории (behavior_rules §12, инцидент 22.10, replay_stale_blocks.md).

**Механизм в старом content.js:** recentlySentIds в chrome.storage, RECENT_LIMIT=500, persist. Это защита от повторного исполнения. Но: леджер хранится в трёх местах (память, chrome.storage, state.ledger в server.py). При рассинхроне — дыра.

**Требование к v5 (Bridge/daemon.py + Bridge/exec.py):**
1. **Единственный водяной знак** — `last_processed_id` в файле (atomic write), не в памяти.
2. **Не только ID, но и хэш содержимого** — блок с тем же id, но другим содержимым тоже не исполняется; пишется в warn-лог.
3. **ID-счётчик монотонно вверх** — если пришёл блок с id < водяного знака, блок помечается SKIP, агенту возвращается `next_id` без исполнения. Явно в отчёте: `SKIP: stale`.
4. **Скан только последних N ассистентских сообщений** (уже есть: SCAN_LAST_MSGS=3), но при первом запуске после reload — не подхватывать всю историю: инициализировать водяной знак по текущему максимуму id в чате.
5. **Отдельный лог** `logs/bridge/stale_blocks.log`: timestamp, id, op, hash, длина. Один из индикаторов заражения.

**Связанные уроки из аудита:**
- ALIVE проверять по живому трафику, не по файлу svc.
- Type 2 detect по маркерам PROMPT (не эвристика по «сейчас проверю»).
- Права: DAEMON сам не перезаписывает свои же артефакты (это ловит replay).

## Закрытие Ф1

Аудит всех 8 зон старого проекта завершён:
1. Bridge (4 модуля) — разделы 1-4.
2. Services (4 модуля) — разделы 5-8.
3. Tools (4 модуля) — разделы 9-12.
4. Launchers (5 файлов) — разделы 13-17.
5. Extension (5 файлов + 32 .bak) — разделы 18-22.
6. Rebirth (5 модулей) — разделы 23-27.
7. Mainframe server.py (73 КБ, 17 частей) — разделы 28, 28.1-28.6.
8. Replay-guard — раздел 29.

Готово к Ф0 (закрыт) → Ф2 (пилот моста на C).

## 30. Урок 13D: op=write truncates Python source with non-ASCII

**Факт:** при записи Bridge/exec.py через op=write (мост JewAI) файл был обрезан до 969 байт (вместо ~2 КБ). Последующая склейка фрагментов дала SyntaxError на em-dash (U+2014) в docstring.

**Причина:** правило §17 behavior_rules (op=write теряет тело >200 байт без должной оснастки). Обрезка непредсказуема; em-dash из p2 при битом p1 становился первой точкой падения парсера.

**Правило для v5:**
1. Python-исходники v5 пишутся **ASCII-only** (docstring, комментарии — латиницей).
   Кириллица только в данных (JSON, md, конфиг).
2. Один op=write на Python-файл <= 1500 байт. Крупнее — фрагментами по 1-1.5 КБ.
3. После каждой записи фрагмента — py_compile.compile(..., doraise=True). Только потом склейка.
4. Склейка — через отдельный build-скрипт, читающий фрагменты из staging, не через op=write.
5. Тест imports + smoke — до объявления "модуль готов".

**Занесено в:** AUDIT.md раздел 30, JOURNAL запись 010.
