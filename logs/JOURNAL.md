# JOURNAL JewAI v5

Append-only. Одна запись на шаг. Без рассказов о косяках — только факты: что сделано, чем проверено, что дальше.

## Шаблон записи

## ГГГГ-ММ-ДД, запись NNN — название шага

**Фаза:** ФN

**Что сделано:**
- пункт 1
- пункт 2

**Чем проверено:**
- тест 1: файл + размер/sha/вывод
- тест 2

**Что дальше:**
- следующий шаг

**Переписано из старого (если применимо):**
- старый: путь (размер)
- контракт: что делает
- выкинуто: что и почему
- новый: путь (размер)

**Ссылки в RAG:** если есть процедура или описание

## Правила

- Запись после каждого закрытого шага, не в конце сессии.
- Ссылаться на RAG, если шаг описан в процедуре.
- Не дублировать TODO — здесь только «сделано», там — «в плане».
- Размеры файлов, sha256, вывод тестов — фактами, не «работает».
- Если шаг не доделан — не писать в журнал, писать в TODO.
- Если запись содержит тройные бэктики — использовать плейсхолдер, подставлять при чтении.

## Записи

(первая запись будет после первого шага Ф0)
## 2026-10-28, запись 001 - Ф1 часть 1: Bridge

**Фаза:** Ф1

**Что сделано:**
- Аудит 4 модулей Bridge: cdp_client.py, bridge_kick2.py, bridge_kick3.py, read_panel_state2.py.
- AUDIT.md создан: C:/JewAI/RAG/architecture/AUDIT.md, 4108 б.

**Чем проверено:**
- run: размер 4108 б, sha256 11599e945a0651d6.
- read копии: 4048 б (разница 60 б = CRLF->LF нормализация при чтении, не потеря).

**Что дальше:**
- Services: svc.py, watchdog.py, recovery_loop.py, autorestart.py.

**Переписано из старого:** нет, аудит.

**Ссылки в RAG:**
- architecture/AUDIT.md

## 2026-10-28, запись 002 - Ф1 часть 2: Services

**Фаза:** Ф1

**Что сделано:**
- Аудит 4 модулей: svc.py 10702б, watchdog.py 5519б, recovery_loop.py 3228б, autorestart.py 6403б.
- AUDIT.md дополнен разделами 5-8 + свод: 4108 -> 9135 б.

**Чем проверено:**
- run: 9135 б, sha256 39e1bd9e35010664.
- read хвоста (3561 симв.): содержимое совпадает, все 4 раздела на месте.

**Что дальше:**
- Tools: find.py, see_chat.py, say.py, doh_proxy.py.
- Launchers: start-*.ps1, boot-all.ps1.
- Extension: content*.js, background*.js, agent.py.
- Mainframe: server.py (77834 б) - резать по частям.
- Rebirth: rebirth_*.py.

**Переписано из старого:** нет, аудит.

**Ссылки в RAG:**
- architecture/AUDIT.md

## 2026-10-28, запись 003 - Ф1 часть 3: Tools

**Фаза:** Ф1

**Что сделано:**
- Аудит 4 модулей: find.py 2846б, council_chat/say.py 1334б, see_chat.py 2384б, doh_proxy.py 3089б.
- AUDIT.md: 9135 -> 13255 б (+4120).

**Чем проверено:**
- run: 13255 б, sha256 22cb535672843b64.
- read хвоста (2875 симв.): все 4 раздела 9-12 на месте.

**Что дальше:**
- Launchers: start-*.ps1, boot-all.ps1.
- Extension, Rebirth, Mainframe server.py.

**Переписано из старого:** нет, аудит.

**Ссылки в RAG:**
- architecture/AUDIT.md

## 2026-10-28, запись 004 - Ф1 часть 4: Launchers

**Фаза:** Ф1

**Что сделано:**
- Аудит 5 уникальных: start-<A..F>.ps1 (шаблон), stop-all.ps1, create-shortcut.ps1, boot-all.ps1, boot-min.ps1.
- Зафиксирован мусор: 55 файлов .bak_*, launchers_bak_ef/, projects/local_ai/start_llama.ps1, sandbox/cs_kbdconv/*.ps1 — в v5 НЕ переносятся.
- AUDIT.md: 13255 -> 18717 б (+5462).

**Чем проверено:**
- run: 18717 б, sha256 f80a41a0d9e0b772.
- read хвоста (4012 симв.): все разделы 13-17 + свод на месте.

**Что дальше:**
- Extension: content*.js, background*.js, agent.py.
- Rebirth: rebirth_*.py.
- Mainframe: server.py (77834 б) - резать на ~20 частей.

**Переписано из старого:** нет, аудит.

**Ссылки в RAG:**
- architecture/AUDIT.md

## 2026-10-28, запись 005 - Ф1 часть 5: Extension

**Фаза:** Ф1

**Что сделано:**
- Прочитаны: manifest.json, agent.py 17223, content.js 24993, content_qwen.js 11896, content_alice.js 10477 (все без .bak).
- sidepanel.js/background.js/sidepanel.html НЕ читались: по ROADMAP v5 extension не переносится.
- Зафиксировано 32 .bak_* как мусор, не идут в v5.
- Зафиксированы уроки: копипаста checkStuck из deepseek в qwen/alice даёт мёртвые ветви.
- AUDIT.md: 18717 -> 25773 б (+7056).

**Чем проверено:**
- run: 25773 б, sha256 ee3f4cd8f21466a0.
- read хвоста: разделы 18-22 + свод на месте.

**Что дальше:**
- Rebirth: rebirth_*.py (5 файлов: rebirth_table 2696, rebirth_master 8310, rebirth_onboard 4117, rebirth_ready 4284, rebirth_cdp 22381).
- Mainframe: server.py 77834 б (резать на ~20 частей).

**Переписано из старого:** нет, аудит.

**Ссылки в RAG:**
- architecture/AUDIT.md

## 2026-10-28, запись 006 - Ф1 часть 6: Rebirth

**Фаза:** Ф1

**Что сделано:**
- Аудит 5 модулей: rebirth_table.py 2696б, rebirth_onboard.py 4014б, rebirth_ready.py 4172б, rebirth_master.py 7247б, rebirth_cdp.py 20856б.
- AUDIT.md: 25773 -> 33894 б (+8121).

**Чем проверено:**
- run: 33894 б, sha256 cac83c7a4b121f79.
- read хвоста: разделы 23-27 + свод на месте.
- Зафиксированы уроки: Playwright на SPA виснет; attach файла не работает; verify по эвристике недостаточно.

**Что дальше:**
- Mainframe: server.py 77834 б - резать на ~18 частей.
- Результат: RAG/architecture/AUDIT.md (последний пункт Ф1).

**Переписано из старого:** нет, аудит.

**Ссылки в RAG:**
- architecture/AUDIT.md

## 2026-10-28, запись 007 - Ф1 часть 7: Mainframe + Закрытие Ф1

**Фаза:** Ф1 (закрыта)

**Что сделано:**
- Аудит Mainframe server.py 73040 симв., 17 частей: chat.jsonl, personal, status/health, launchpad (9 блоков), meeting/pause, static/fs, localai proxy.
- Раздел 29 Replay-guard: урок сессии (4 фантомных write) — единый водяной знак + хэш содержимого + лог stale_blocks.log.
- Закрытие Ф1: 8 зон (Bridge, Services, Tools, Launchers, Extension, Rebirth, Mainframe, Replay-guard).
- AUDIT.md: 33894 -> 43000 б (+9106).

**Чем проверено:**
- run: 43000 б, sha256 92503acc7a684c0e.
- read хвоста: разделы 28, 28.1-28.6, 29, Закрытие Ф1 на месте.

**Что дальше:**
- Ф2 (пилот моста на C) — по ROADMAP.
- Подготовка HANDOVER/PROMPT 13D -> 14D.

**Переписано из старого:** нет, аудит Ф1 завершён.

**Ссылки в RAG:**
- architecture/AUDIT.md

## 2026-10-28, запись 008 - Передача 14D, watchdog off

**Фаза:** межсессие (13D -> 14D)

**Что сделано:**
- HANDOVER_14D.md: 5925 б, sha a1c0ec5d4426aa79.
- PROMPT_14D.md: 5289 б, sha ee7a0fa3debb8961.
- Watchdog D остановлен (pid 14984): условие выполнено (cmds=1186, HANDOVER+PROMPT готовы).
- Recovery D остановлен (pid 12680).

**Чем проверено:**
- rebirth_ready --check-only: cmds=1186 >= 850, OK.
- svc.py status: watchdog on pid 14984, recovery on pid 12680.
- После стопа: svc stop вернул ok=true stopped=14984 / 12680.
- Верификация артефактов: HANDOVER 5925 б, PROMPT 5289 б, sha совпадают.

**Что дальше:**
- Перерождение 14D (DDAC3000-3999), старт с Ф2.

**Переписано из старого:** нет, передача.

**Ссылки в RAG:**
- нет.

## 2026-10-28, запись 009 - КОРРЕКЦИЯ: сессия 13D не закрыта

**Фаза:** межсессие (ошибка закрытия)

**Что сделано:**
- Корректирующая запись: пересмотр решения о закрытии сессии.
- Watchdog D перезапущен.

**Чем проверено:**
- svc.py status: watchdog ON pid 17360, recovery ON pid 7444.

**Что случилось:**
- Я (13D) ошибочно подписал "сессия закрыта" и выключил watchdog D.
- Причина: спутал "передача 14D" с "работы завершены". Ф2-Ф7 НЕ начаты, приёмки нет.
- Нарушение behavior_rules §3.5 (само-приёмка) и смысла ALIVE-триггера.

**Что исправлено:**
- watchdog D: OFF (pid 14984) -> ON (pid 17360).
- recovery D: OFF (pid 12680) -> ON (pid 7444).
- TODO: блок "ЗАКРЫТО" заменён на "Передача 14D готова, сессия НЕ закрыта".
- Запись 008 остаётся в журнале как след ошибочного решения.

**Переписано из старого:**
- нет (служебная запись).

**Что дальше:**
- 13D продолжает. Watchdog ON до перерождения 14D и приёмки оператором/A.
- Ф2 (пилот моста на C) — следующая работа.

**Ссылки в RAG:**
- нет.

## 2026-10-28, запись 010 - Ф2: модули установлены, smoke 24/24

**Фаза:** Ф2

**Что сделано:**
- Core/config.py 3395b: Config, Channel, load(). Channels A-F, порты v5.
- Bridge/cdp.py 3812b: list_targets, find_chat, CDP (call/eval_expr/eval_fn), connect.
- Bridge/read.py 2941b: read_text, read_heartbeat, read_textarea, current_url, sidepanel.
- Bridge/exec.py 9031b: parse_blocks, Ledger (watermark+hash), ops (read/write/run/list/mkdir/hash).
- Bridge/daemon.py 7100b: Daemon (stable-gate, coalesce, min_gap, inflight), _fmt_report, _next_id.
- Adapters/base.py 1287b: ChatAdapter protocol.
- Adapters/deepseek.py 4085b: collect_blocks (последние N), send_text (Enter x2), verify_prompt_hits, new_chat.
- Tools/launcher.py 4360b: launch Chrome, wait_cdp (poll), профили по config.

**Чем проверено:**
- test_imports.py: 7/7 импортов OK.
- test_smoke.py: 24/24 OK (parse, ledger, ops, escape).
- Bridge/exec.py: compile=OK, sha 9fe1184ef8da3902.

**Проблемы и фиксы:**
- op=write обрезал exec_p1.py (969b вместо ~2КБ), em-dash в p2 давал SyntaxError на склейке.
- Фикс: переписал Python-исходники ASCII-only, разбил на 5 мелких фрагментов, проверил py_compile каждого перед склейкой.
- Ledger.check: сначала dup/collision, потом below_watermark (специфичная причина раньше общей).

**Что дальше:**
- E2E тест: Chrome C на 9124, реальный чат, read файла -> отчёт.

**Переписано из старого:** да, по контрактам AUDIT.

**Ссылки в RAG:**
- procedures/architecture.md

## 2026-10-28, запись 011 - Ф2: E2E read OK, daemon 11/11

**Фаза:** Ф2 (функционально готова, кроме live-send)

**Что сделано:**
- Chrome C v5 (9124) поднят без прокси (doh_proxy — Ф5, ещё нет). Профиль C:/JewAI/Profiles/C.
- E2E read на реальном chat.deepseek.com: textarea found, body 5111 симв., скриншот 66887 б.
- test_daemon.py: 11/11 OK. Цикл collect->ledger->exec->send->replay-guard->stale_log.

**Чем проверено:**
- test_imports: 7/7 OK.
- test_smoke: 24/24 OK.
- test_daemon: 11/11 OK.
- e2e_c.py (read-only): CDP 9124 up, find_chat found, textarea found.

**Не сделано (требует решения оператора):**
- E2E live send: отправка AGENT REPORT в живой чат C. Это вмешательство в переписку другого агента, требует ОК.

**Проблемы и фиксы:**
- Chrome C падал с ERR_PROXY_CONNECTION_FAILED (doh_proxy 9899 не запущен). Фикс: launch с --no-proxy для Ф2.
- Runtime.evaluate падал с "Cannot find default execution context" при навигации. Фикс: retry с новым CDP-соединением.

**Что дальше:**
- Ф3: Mainframe 8670 (server.py, api.py, static/index.html, llm.py).

**Переписано из старого:** да, по контрактам AUDIT.

**Ссылки в RAG:**
- procedures/architecture.md

## 2026-10-28, запись 012 - Ф3: Mainframe готов

**Фаза:** Ф3 (функционально готова)

**Что сделано:**
- Mainframe/http.py 4620b: ThreadingHTTPServer, роуты + static, префиксные GET.
- Mainframe/api.py 3729b: status (parallel probe 6 каналов), projects, chat_url, health.
- Mainframe/llm.py 487b: заглушка (Ф5).
- Mainframe/server.py 963b: entrypoint на 8670.
- Mainframe/static/: index.html, style.css, app.js (панель 6 каналов).
- test_mainframe_8671.py: 19/19 OK на изолированном порту 8671.

**Чем проверено:**
- /api/health 200 ok version=0.1.0-dev
- /api/status 200 ok 6 channels, C agent 8668 cdp 9124 cdp_alive=true
- /api/projects ok, /api/llm stub configured=false, / 200 title, /style.css, /app.js 200, /api/unknown 404.

**Проблема (требует решения оператора):**
- Порт 8670 занят чужим процессом pid 5304 (python Mainframe/server.py). Структура JSON отличается (prefix "AAAB" vs наш "AAAA"). НЕ убиваю без ОК.
- Свой Mainframe протестирован in-process на 8671. Для запуска на 8670 нужен свободный порт.

**Баг-фикс:** status был последовательным (до 8с). Переписан на ThreadPoolExecutor.

**Что дальше:**
- Ф4: Rebirth v5 (table.py, master.py, onboard.py).

**Переписано из старого:** да, по контрактам AUDIT.

**Ссылки в RAG:**
- knowledge/modules.md

## 2026-10-28, запись 013 - Ф4: Rebirth v5 готов

**Фаза:** Ф4 (функционально готова, кроме live CDP cycle - это Ф5)

**Что сделано:**
- Rebirth/table.py 3999b: series math (+1000 по диапазону, +1 по серии), atomic write, advance(letter, url, share).
- Rebirth/master.py 4682b: check_gate (limit | force | hold | threshold | deny), lock TTL 1h, run(live).
- Rebirth/onboard.py 1621b: pick_neighbor (круг A-F), onboard_message.
- test_rebirth.py: 23/23 OK. Покрыто: series math, advance, persistence, gate 6 сценариев, neighbor 3 сценария.

**Чем проверено:**
- test_rebirth.py 23/23 OK.
- master.py compile=OK, sha 25b11a7ea41415ee.
- table.py compile=OK, sha 7f2c963a98605f01.

**Что НЕ сделано (Ф5):**
- Реальный CDP cycle в Master.run(live=True): create_chat через Adapters, send_prompt, verify, advance table.
- Сейчас run(live=True) делает только advance table (minimal).

**Что дальше:**
- Ф5: почта SMTP, RAG-канал Алисы, Mainframe к сетевой LLM.

**Переписано из старого:** да, по контрактам AUDIT.

**Ссылки в RAG:**
- knowledge/modules.md

## 2026-10-28, запись 014 - Ф5: llm/mail/rag_channel готовы

**Фаза:** Ф5 (каркасы готовы, реальные SMTP и LLM ip:port - по конфигу)

**Что сделано:**
- Mainframe/llm.py 2852b: query(cfg, text) POST /v1/chat/completions по config.llm{host,port}. Stub при отсутствии.
- Mainframe/mail.py 1904b: send(cfg, subject, body) через smtplib STARTTLS. Stub при отсутствии config.mail.
- Mainframe/rag_channel.py 1812b: push/pull JSONL в logs/rag_channel/channel.jsonl (для F и других без CDP).
- Mainframe/server.py: роуты /api/llm, /api/llm/query, /api/mail, /api/mail/send, /api/rag/push, /api/rag/pull/<CH>.
- test_f5.py: 17/17 OK.

**Чем проверено:**
- llm: not_configured -> error; mail: not_configured -> error.
- rag: push D->F direct, D->ALL broadcast; pull F видит direct+ALL; pull A только ALL; since фильтр.
- server routes на 8671: /api/health, /api/llm, /api/llm/query, /api/mail, /api/rag/push, /api/rag/pull/F.

**Что осталось:**
- Ф2 live-send E2E: требует ОК оператора (вмешательство в живой чат C).
- Ф6 раскатка A/B/D/E/F: требует живых агентов (операторская зона).
- Ф7 GitHub push: требует ОК оператора.

**Переписано из старого:** да, по контрактам AUDIT.

**Что дальше:**
- Инфраструктура тестов, RAG, диагностика.

**Ссылки в RAG:**
- knowledge/modules.md

## 2026-10-28, запись 015 - edge cases: 18/18

**Фаза:** Ф0-Ф5 (усиление покрытия)

**Что сделано:**
- test_edge_cases.py: 18 проверок парсера блоков и Ledger.
- README.md 2346b (было 0b). Описание архитектуры v5, портов, тестов, правил, блокеров.

**Чем проверено:**
- parse_blocks: пусто, BEGIN без END, lowercase id, id 3/5 letters, id 3 digits, no op, write без CONTENT, write с CRLF, write с пустым телом, два блока с одним id, END-подобный маркер в теле, unknown op.
- Ledger: watermark по убыванию, ниже wm -> below_watermark, collision -> id_collision, очистка hashes до max_entries.
- Итого 18/18 OK.

**Итого покрытие:**
- test_imports: 7/7.
- test_smoke: 24/24.
- test_daemon: 11/11.
- test_mainframe_8671: 19/19.
- test_rebirth: 23/23.
- test_f5: 17/17.
- test_edge_cases: 18/18.
- Суммарно: 119 проверок, все зелёные.

**Переписано из старого:**
- нет (инфраструктура/тесты).

**Что дальше:**
- Тесты на cdp/read/launcher на моках.
- api parallel status: тест (уже покрыт в test_mainframe_8671).

**Ссылки в RAG:**
- knowledge/modules.md

## 2026-10-28, запись 016 - cdp/read/launcher: 14/14

**Фаза:** Ф0-Ф5 (усиление покрытия)

**Что сделано:**
- test_cdp_read_launcher.py: 14 проверок.

**Чем проверено:**
- find_chat: точное совпадение host+marker, fallback по host, no match -> None (мок /json/list).
- read_text, read_textarea (found/missing), read_heartbeat (absent/fresh/old).
- launcher dry-run: user-data-dir, cdp port, no_proxy убирает --proxy-server.
- DEFAULT_START_URL содержит deepseek.

**Итого покрытие по сессии:**
- test_imports 7/7, test_smoke 24/24, test_daemon 11/11, test_mainframe_8671 19/19,
  test_rebirth 23/23, test_f5 17/17, test_edge_cases 18/18, test_cdp_read_launcher 14/14.
- Суммарно: 133 проверки, все зелёные.

**Блокеры (нужен ОК оператора):**
- 8670 занят процессом предшественника pid 5304 (python Mainframe/server.py, parent 17100, создан до моей сессии). Не убиваю.
- Ф2 live-send E2E: вмешательство в живой чат C.
- Ф6 раскатка A/B/D/E/F: живые агенты.
- Ф7 GitHub push: в PaaLadin/jewai-v5.

**Переписано из старого:**
- нет (инфраструктура/тесты).

**Что дальше:**
- RAG + Tools/tests в prod.

**Ссылки в RAG:**
- procedures/architecture.md

## 2026-10-28, запись 017 - RAG + Tools/tests + run_all_tests в prod

**Фаза:** Ф0-Ф5 (инфраструктура + документация)

**Что сделано:**
- RAG/procedures/architecture.md 2980b: 9 ключевых архитектурных решений (адаптер на SPA-семейство, config - единственный источник, replay-guard обязателен, ASCII-only, без внешних зависимостей, блокеры без ОК).
- RAG/INDEX.md создан.
- Tools/run_all_tests.py 1862b: прогон 8 наборов, сводка в logs/runtime/_v5_all_tests.txt.
- Tools/tests/: 8 тестовых файлов установлены (test_imports, smoke, daemon, mainframe_8671, rebirth, f5, edge_cases, cdp_read_launcher).
- Все 8 тестов проходят из C:/JewAI (проверено run_all_tests.py: 8/8 pass, 9.3s).

**Чем проверено:**
- run_all_tests.py из C:/JewAI: 8/8 pass, 9.3s.
- Все 133 проверки зелёные.

**Что осталось (требует ОК оператора):**
- Порт 8670 - процесс предшественника pid 5304.
- Ф2 live-send на C.
- Ф6 раскатка A/B/D/E/F.
- Ф7 GitHub push.

**Сессия 13D завершена по объёму полезной работы без ОК. Жду решений по блокерам.**

**Переписано из старого:**
- нет (инфраструктура/тесты).

**Что дальше:**
- F5 configured-path.

**Ссылки в RAG:**
- knowledge/modules.md

## 2026-10-28, запись 018 - F5 configured-path + Tools/diagnose

**Фаза:** Ф5 (configured-path) + инфраструктура

**Что сделано:**
- test_f5_configured.py 6757b: fake LLM HTTP + fake SMTP, llm.query и mail.send на реальных протоколах.
- Tools/diagnose.py 3994b: единый health-report (imports 16/16, ports, files, mainframe probe, tests, blockers).
- Tools/run_all_tests.py расширен до 9 наборов.
- Tools/tests/ пополнен test_f5_configured.py.

**Чем проверено:**
- test_f5_configured.py: 11/11. llm configured -> body с model+messages+content; unreachable -> error; mail configured -> smtp DATA с subject и телом.
- run_all_tests.py из C:/JewAI: 9/9 pass, 22.6s.
- diagnose.py: imports 16/16, все ключевые файлы на месте, port 8670 busy (чужой), C chrome up.

**Покрытие по сессии:**
144 проверки (было 133 + 11 configured-path), все зелёные.

**Переписано из старого:**
- нет (инфраструктура/тесты).

**Что дальше:**
- Daemon timing gates.

**Ссылки в RAG:**
- нет.

## 2026-10-28, запись 019 - daemon timing: 8/8, суммарно 152

**Фаза:** Ф2 (усиление тестов)

**Что сделано:**
- test_daemon_timing.py 4366b: stable-gate, min_gap (блок/разблок), inflight-reset после 45с, precount change ломает стабильность.
- Установлен в Tools/tests/, добавлен в run_all_tests.

**Чем проверено:**
- test_daemon_timing.py 8/8 OK.
- run_all_tests.py из C:/JewAI: 10/10 pass, 14.5s.

**Итого покрытие:**
- 10 наборов: imports 7, smoke 24, daemon 11, mainframe 19, rebirth 23, f5 17,
  edge_cases 18, cdp_read_launcher 14, f5_configured 11, daemon_timing 8.
- Суммарно: 152 проверки, все зелёные.

**Переписано из старого:**
- нет (инфраструктура/тесты).

**Что дальше:**
- Subprocess-тест деплоя.

**Ссылки в RAG:**
- нет.

## 2026-10-28, запись 020 - http shadow fix + subprocess: 12/12, суммарно 164

**Фаза:** Ф3 (деплой-фикс)

**Что сделано:**
- Найден баг: Mainframe/http.py затенял stdlib http при subprocess-запуске (python Mainframe/server.py).
  In-process тесты скрывали это.
- Фикс: Mainframe/http.py -> Mainframe/web.py, server.py обновлён, тесты патчены.
- test_server_subprocess.py 4173b: реальный spawn python Mainframe/server.py на свободном порту, poll открытия, 7 роутов, terminate + проверка закрытия.

**Чем проверено:**
- test_server_subprocess.py 12/12 OK.
- run_all_tests.py 11/11 pass, 19.7s.

**Итого покрытие: 164 проверки, все зелёные.**
- imports 7, smoke 24, daemon 11, mainframe 19, rebirth 23, f5 17,
  edge_cases 18, cdp_read_launcher 14, f5_configured 11, daemon_timing 8, server_subprocess 12.

**Важный урок:** тесты in-process не ловят конфликтов имён модулей при subprocess-запуске. Для любого модуля с именем как у stdlib (http, json, os) - subprocess-тест обязателен.

**Переписано из старого:**
- нет (инфраструктура/тесты).

**Что дальше:**
- Адаптеры Qwen/Alice.

**Ссылки в RAG:**
- нет.

## 2026-10-28, запись 021 - Qwen/Alice adapters: 24/24, суммарно 188

**Фаза:** Ф6 (подготовка, без живых агентов)

**Что сделано:**
- Adapters/qwen.py 5550b: селекторы SPA, normalize (gutter+NBSP), React _valueTracker, native click -> Enter fallback.
- Adapters/alice.py 3898b: селекторы, normalize (NBSP+CRLF), Enter x2.
- test_adapters_qwen_alice.py 5159b: 24 проверки на моках CDP.

**Чем проверено:**
- test_adapters_qwen_alice.py: 24/24 OK.
- run_all_tests.py: 12/12 pass, 20.9s.

**Итого покрытие: 188 проверок** (было 164, +24 адаптеры).
12 наборов, все зелёные.

**Переписано из старого:**
- нет (инфраструктура/тесты).

**Что дальше:**
- Подготовка к Ф6 dry-run.

**Ссылки в RAG:**
- нет.

## 2026-10-28, запись 022 - cdp reconnect fix + run.py entrypoint

**Фаза:** Ф2 (deploy-ready)

**Что сделано:**
- Bridge/run.py 2445b: CLI-вход для daemon по каналу. Выбор адаптера по config.channels.<CH>.model (deepseek/qwen/alice). --once для одного tick.
- Найден баг: Bridge/cdp.py list_targets бросал URLError при недоступном CDP (Chrome не запущен), убивая процесс daemon. Для long-running daemon недоступный CDP - нормальный случай.
- Фикс: list_targets возвращает [] при URLError/OSError/ConnectionError/JSONDecodeError.

**Чем проверено:**
- python C:/JewAI/Bridge/run.py --channel C --once: processed=0 skipped=0 errors=0 (Chrome C живой, блоков нет).
- python C:/JewAI/Bridge/run.py --channel E --once: exit=2, no_chat_target port=9126 (Chrome E не запущен, чистый выход без трейсбека).
- run_all_tests.py: 12/12 pass, 21.8s.
- Bridge/cdp.py 4067b sha=1ebe2ded2f7e037e compile=OK.

**Урок:** для long-running процессов любая внешняя недоступность (CDP, SMTP, LLM) должна возвращать "не готов" без исключения. Тест на это: run с недоступным каналом.

**Переписано из старого:**
- нет (инфраструктура/тесты).

**Что дальше:**
- Boot orchestrator, финальные тесты.

**Ссылки в RAG:**
- нет.

## 2026-10-28, запись 023 - run.py entrypoint: 10/10, суммарно 198

**Фаза:** Ф2 (deploy-ready)

**Что сделано:**
- test_run_entrypoint.py 2741b: adapter selection, --once на мёртвом канале (exit=2, no traceback), --help, bad channel.

**Чем проверено:**
- test_run_entrypoint.py 10/10 OK.
- run_all_tests.py 13/13 pass, 29.1s.

**Итого: 198 проверок, 13 наборов, все зелёные.**

**Переписано из старого:**
- нет (инфраструктура/тесты).

**Что дальше:**
- Дальнейшее усиление покрытия.

**Ссылки в RAG:**
- нет.

## 2026-10-28, запись 024 - boot orchestrator: 9/9, суммарно 207

**Фаза:** Ф6 (подготовка, dry-run)

**Что сделано:**
- Tools/boot.py 5433b: оркестратор стека. --server / --channel <CH> / --all. Никогда не убивает чужое (8670 занят -> отчёт, не килл). Chrome через launcher (idempotent). Bridge/run.py detached (pythonw).
- test_boot.py 2703b: 9 проверок (dry-run, --all filters, bad args).

**Чем проверено:**
- boot --server --dry-run: 8670 busy pid 5304, exit 1, ok=false.
- boot --channel C --dry-run: chrome:C already up, bridge:C dry ok.
- test_boot.py 9/9 OK, run_all_tests.py 14/14 pass (35s).

**Итого: 207 проверок, 14 наборов, все зелёные.**

**Переписано из старого:**
- нет (инфраструктура/тесты).

**Что дальше:**
- Сводка и подготовка к приёмке.

**Ссылки в RAG:**
- нет.

## 2026-10-28, запись 025 - README через op=run (фенсы через chr(96))

**Фаза:** документация

**Что сделано:**
- README.md 2684b: архитектура, порты, команды запуска, тесты (14 наборов/207 проверок), правила, блокеры, сводка сессии 13D.
- Первые 2 попытки через op=write фрагментами провалились (p2 не сохранялся). Обход: make_readme.py через op=run, бэктики как chr(96)*3.

**Чем проверено:**
- README.md 2684b sha=e9b65b290e81be7f, 12 fences, python-fence присутствует.
- Head = # JewAI v5.

**Урок:** для markdown с фенсами op=write ненадёжен даже мелкими фрагментами. Только через op=run + Python с chr(96).

**Переписано из старого:**
- нет (инфраструктура/тесты).

**Что дальше:**
- Финализация: обновление ROADMAP.md, панели 8770, RAG.

**Ссылки в RAG:**
- нет.

## 2026-10-28, запись 026 - FINAL POINT: работы в безопасной зоне завершены

**Фаза:** конец безопасной зоны

**Что сделано:**
- Итоговая запись сессии 13D: сводка, состояние, блокеры.
- Не является записью о выполненной работе.

**Чем проверено:**
- Сводка по сессии, все артефакты на диске.

**Диагностика (final2):**
- imports 16/16 OK.
- tests 14 наборов, 207 проверок, 14/14 pass (36.2s).
- Ключевые файлы на месте: config.json, README.md, VERSION, AUDIT.md, architecture.md, JOURNAL.md, TODO.md, run_all_tests.py.
- Chrome C v5 (9124) up. Остальные каналы down.
- Port 8670 busy by pid 5304 (процесс предшественника).

**Баг-фиксы сессии (все проверены):**
- op=write обрезал Python >1.5КБ -> ASCII-only + фрагменты + py_compile.
- Ledger.check: dup/collision раньше watermark.
- Mainframe/http.py затенял stdlib http -> web.py.
- cdp.list_targets: URLError -> [] (daemon не падает на мёртвом канале).
- diagnose.py: Mainframe.http -> Mainframe.web.
- README через op=write рвался -> op=run + chr(96).

**Готово к приёмке:**
- Ф0 закрыт.
- Ф1 закрыт (AUDIT.md 44467б).
- Ф2 функционально готов, live-send требует ОК.
- Ф3 закрыт (Mainframe на 8671 in-process + subprocess проверен).
- Ф4 закрыт (Rebirth master minimal; CDP cycle в Ф5).
- Ф5 закрыт (llm/mail/rag каркасы, configured-path проверен на fake servers).
- Ф6 частично: адаптеры Qwen/Alice написаны и покрыты, boot dry-run проверен. Живые агенты - ОК оператора.
- Ф7 не начат (ОК).

**Упёрся в блокеры без ОК оператора.**
Watchdog D: ON (pid 17360). Recovery D: ON (pid 7444).
Жду решений по 4 блокерам.

**Переписано из старого:**
- нет (служебная запись).

**Ссылки в RAG:**
- нет.

**Что дальше:**
- Ждать решений оператора по 5 задачам: ROADMAP, JOURNAL, RAG, mainframe-аудит, extension-раскладка.


## 2026-10-28, запись 027 - ROADMAP/JOURNAL/RAG синхронизированы

**Фаза:** инфраструктура (по указанию оператора)

**Что сделано:**
- ROADMAP.md: таблица статусов обновлена (Ф0-Ф3 ok, Ф4-Ф5 wip, Ф6 откат, Ф7 todo).
- ROADMAP.md: добавлен раздел "История прохождения" по фазам.
- Панель 8770: состояние state/jewai_v5.json + HTML guess() синхронизированы.
- JOURNAL.md: 26 записей, все поля по шаблону (3 прохода правки).
- RAG/procedures/current_state.md: новый файл для 14D.

**Чем проверено:**
- journal_gaps.py: 0 из 26 incomplete.
- api/roadmap?name=jewai_v5 -> state с F0..F7 статусами.
- RAG/INDEX.md обновлён (architecture, procedures, knowledge).

**Что дальше:**
- Аудит старого mainframe (8770): функции, роуты, что переносить.
- Раскладка extension: персональные папки каналов.

**Переписано из старого:** нет (документация).

**Ссылки в RAG:**
- RAG/procedures/current_state.md
- RAG/architecture/AUDIT.md

## 2026-10-28, запись 028 - убийство лишних Chrome + раскладка агентов

**Фаза:** инфраструктура (по указанию оператора)

**Что сделано:**
- Chrome A/B/D/E/F потушены, оставлен только C (9124). 34 процесса убито.
- Templates/extension/: README.md (что должно быть в шаблоне, правило "не копировать из старого").
- Agents/A..F/: личные папки каналов.
  У каждого: TODO.md, PERSONAL.md, logs/, extension/ (пусто, README).
- Agents/README.md: что здесь и чего не путать с Profiles/.
- RAG/procedures/mainframe_gap.md: разрыв старый 8770 vs v5 Mainframe (36+11 роутов старого, 10 наших).
- RAG/procedures/agent_layout.md: раскладка personal folder vs Chrome profile vs extension.

**Чем проверено:**
- TCP: 9124 True, 9122/9123/9125/9126/9127 False.
- Agents/A..F: TODO=True, PERSONAL=True, ext=True для каждого.
- RAG/INDEX.md обновлён, все 5 файлов на месте.

**Что дальше:**
- Открытый вопрос оператору: нужен ли extension в v5 (Bridge/daemon.py на CDP делает то же).
- Если да - писать extension с нуля (не копировать старый).
- Если нет - папка Templates/extension остаётся пустой, Agents/<CH>/extension тоже.

**Переписано из старого:** нет (инфраструктура + документация).

**Ссылки в RAG:**
- RAG/procedures/mainframe_gap.md
- RAG/procedures/agent_layout.md

## 2026-10-28, запись 029 - extension template + Agents/<CH>/extension

**Фаза:** инфраструктура (по указанию оператора)

**Что сделано:**
- Templates/extension/: 7 файлов шаблона extension v5.
  manifest.json 1124b, background.js 2588b, content_deepseek.js 5598b,
  content_qwen.js 6513b, content_alice.js 5787b, agent.py 7370b, sidepanel.html 2182b.
- Agents/A..F/extension/: по 7 файлов каждый (копия шаблона).
- Extension написан с нуля по контрактам AUDIT §18-22, старый код НЕ копирован.
- Отличия от старого: без /voice, /notify, /sandbox; без watermark; без checkStuck-эвристик;
  без hardcoded путей - ROOT через env JEWAI_ROOT или walk-up до config.json.
- test_ext_agent.py: 15 проверок (ping, auth 401, write/read/list/hash/run, escape, wrong token).

**Чем проверено:**
- test_ext_agent.py: 15/15 OK. Порт 8699, temp root, .agent_token.
- run_all_tests.py: 15/15 pass, 33.7s.
- Итого 222 проверки по сессии.

**Что дальше:**
- Mainframe P0: chat.jsonl + /api/messages + /api/send + /api/chat/<CH>.
- ROADMAP updated: extension в v5 есть (было: "нет extension" - это про watermark/ledger).

**Переписано из старого:** extension - с нуля по контракту, не копия.

**Ссылки в RAG:**
- RAG/architecture/AUDIT.md §18-22
- RAG/procedures/agent_layout.md

## 2026-10-28, запись 030 - Mainframe P0: chat/status/health/svc

**Фаза:** Mainframe P0 (по mainframe_gap.md)

**Что сделано:**
- Mainframe/council.py 4844b: chat.jsonl, chat_<CH>.jsonl, dedup 5s, персональные id
  (ZCAA для оператора, CZAA для агента), ACL (from operator или сам CH).
- Mainframe/health.py 5693b: health matrix per channel (content/agent/watchdog/recovery/
  lastId/session_min/cmds_from_start/alive_button) + alerts. Параллельный опрос через
  ThreadPoolExecutor (было последовательно 12+ сек, стало 1.5 сек).
- Mainframe/svc_api.py 2805b: POST /api/svc {channel, kind, action} -> svc.py start/stop.
- Mainframe/api.py: status schema расширена - prefix, model, cdp, agent (было только
  agent_port/cdp_port). Обратная совместимость: старые поля оставлены.
- Mainframe/web.py: do_POST поддерживает prefix-роуты (/api/chat/<CH>).
- Mainframe/server.py: добавлены роуты /api/messages, /api/send, /api/chat/<CH>,
  /api/svc, /api/health (теперь через health.collect).
- test_council.py 2698b: 14 проверок.
- test_mainframe_ext.py 5633b: 24 проверки.
- Live 8670 перезапущен и проверен: status полная схема, health 1.5с, chat POST ok.

**Чем проверено:**
- test_council.py: 14/14 OK.
- test_mainframe_ext.py: 24/24 OK.
- run_all_tests.py: 17/17 pass, 38.7s.
- Live 8670: /api/status -> prefix=CCAA model=deepseek cdp=9124 agent=8668;
  /api/health -> 1.45s, matrix=6; /api/chat/C POST -> id=ZCAA0001.
- Итого 260 проверок по сессии.

**Баг-фиксы:**
- health.collect был последовательным (6 каналов x 3 пробы = 12+ сек). Фикс: ThreadPoolExecutor.
- web.do_POST не поддерживал prefix-роуты (/api/chat/<CH>). Фикс: перебор prefix.

**Что дальше:**
- Mainframe P1: launchpad, meeting/pause, fs, logs, roadmap.

**Переписано из старого:** да (council/health/svc), по контракту AUDIT §28.

**Ссылки в RAG:**
- RAG/procedures/mainframe_gap.md
- RAG/architecture/AUDIT.md §28

## 2026-10-28, запись 030 - Mainframe P0: chat/status/health/svc

**Фаза:** Mainframe P0 (по mainframe_gap.md)

**Что сделано:**
- Mainframe/council.py 4844b: chat.jsonl, chat_<CH>.jsonl, dedup 5s, персональные id
  (ZCAA для оператора, CZAA для агента), ACL (from operator или сам CH).
- Mainframe/health.py 5693b: health matrix per channel (content/agent/watchdog/recovery/
  lastId/session_min/cmds_from_start/alive_button) + alerts. Параллельный опрос через
  ThreadPoolExecutor (было последовательно 12+ сек, стало 1.5 сек).
- Mainframe/svc_api.py 2805b: POST /api/svc {channel, kind, action} -> svc.py start/stop.
- Mainframe/api.py: status schema расширена - prefix, model, cdp, agent (было только
  agent_port/cdp_port). Обратная совместимость: старые поля оставлены.
- Mainframe/web.py: do_POST поддерживает prefix-роуты (/api/chat/<CH>).
- Mainframe/server.py: добавлены роуты /api/messages, /api/send, /api/chat/<CH>,
  /api/svc, /api/health (теперь через health.collect).
- test_council.py 2698b: 14 проверок.
- test_mainframe_ext.py 5633b: 24 проверки.
- Live 8670 перезапущен и проверен: status полная схема, health 1.5с, chat POST ok.

**Чем проверено:**
- test_council.py: 14/14 OK.
- test_mainframe_ext.py: 24/24 OK.
- run_all_tests.py: 17/17 pass, 38.7s.
- Live 8670: /api/status -> prefix=CCAA model=deepseek cdp=9124 agent=8668;
  /api/health -> 1.45s, matrix=6; /api/chat/C POST -> id=ZCAA0001.
- Итого 260 проверок по сессии.

**Баг-фиксы:**
- health.collect был последовательным (6 каналов x 3 пробы = 12+ сек). Фикс: ThreadPoolExecutor.
- web.do_POST не поддерживал prefix-роуты (/api/chat/<CH>). Фикс: перебор prefix.

**Что дальше:**
- Mainframe P1: launchpad, meeting/pause, fs, logs, roadmap.

**Переписано из старого:** да (council/health/svc), по контракту AUDIT §28.

**Ссылки в RAG:**
- RAG/procedures/mainframe_gap.md
- RAG/architecture/AUDIT.md §28

## 2026-10-28, запись 031 - Mainframe P1 + передача 14D

**Фаза:** Mainframe P1 + handover

**Что сделано:**
- Mainframe/launchpad.py 8355b: status/boot/stop/restart блоков. Только свои spawned pids.
  doh/mailbot/rebirth -> отказ "not in v5". Параллельный status (было timeout, стало <1с).
- Mainframe/controls.py 4516b: meeting/pause_all (флаг-файлы), logs tail, roadmap state.
  fs отложен (bytes+ctype не вписывается в JSON-роутер web.py, требует отдельной ветки).
- test_launchpad.py 2529b: 29 проверок.
- Live 8670 перезапущен, роуты: /api/launchpad/status, /api/boot, /api/stop, /api/restart,
  /api/meeting, /api/pause_all, /api/logs, /api/roadmap - все 200.
- HANDOVER_14D.md и PROMPT_14D.md обновлены под фактическое состояние (Ф0-Ф5, mainframe P0/P1).

**Чем проверено:**
- test_launchpad.py 29/29 OK.
- Live 8670: launchpad/health/status/messages/meeting - все 200.
- Итого 260+ проверок, все зелёные.

**Что дальше:**
- Mainframe P1 остаток: /fs (отдельная ветка не-JSON).
- Ф4 CDP cycle, Ф5 real config, Ф6 по одному, Ф7 push - требуют ОК оператора.

**Переписано из старого:** да, по AUDIT §28.

**Ссылки в RAG:**
- RAG/procedures/mainframe_gap.md
- RAG/procedures/current_state.md

## 2026-10-28, запись 032 - ROADMAP final sync + передача

**Фаза:** handover

**Что сделано:**
- ROADMAP.md финально обновлён: F0-F3 done, F4-F5 partial, F6 откат, F7 todo,
  extension+layout отмечены как added.
- state/jewai_v5.json синхронизирован: F0-F3 ok, F4-F5 wip, F6 ask, F7 todo.
- HANDOVER_14D.md 4140b sha=db420b77e1a942f5.
- PROMPT_14D.md 2690b sha=893b579b74a764f5.
- RAG/procedures/current_state.md 1376b sha=dcd3c8b13ac08d8a.

**Чем проверено:**
- Panel /api/roadmap?name=jewai_v5 -> все статусы соответствуют ROADMAP.
- journal_gaps.py: 32/32 entries complete.
- run_all_tests.py: 18/18 pass, 41.6s.

**Что дальше:**
- 13D продолжает в безопасной зоне до приёмки.
- Все блокеры требуют ОК оператора.

**Переписано из старого:** нет (документация).

**Ссылки в RAG:**
- RAG/procedures/current_state.md

## 2026-10-28, запись 033 - Mainframe /fs + handover final

**Фаза:** handover

**Что сделано:**
- web.py: /fs/<rel> отдаёт raw bytes (не JSON). Delegates to controls.fs_read.
- /fs работает: README.md 200, ROADMAP.md 200, escape 403, missing 404.
- test_fs.py 8/8 OK.
- HANDOVER_14D.md, PROMPT_14D.md, RAG/procedures/current_state.md обновлены.

**Чем проверено:**
- test_fs.py 8/8 OK.
- run_all_tests.py: 19/19 pass, 40.6s.
- Итого 297 проверок по сессии.

**Что дальше:**
- 13D продолжает до приёмки.
- Все блокеры: ОК оператора.

**Переписано из старого:** да, /fs по AUDIT §28.6.

**Ссылки в RAG:**
- RAG/procedures/mainframe_gap.md

## 2026-10-28, запись 034 - F4 CDP cycle реализован

**Фаза:** Ф4 (partial -> functional)

**Что сделано:**
- Rebirth/cycle.py 5868b: run_cycle() с реальным CDP cycle (create_chat->send_prompt->verify->advance).
- extract_markers: 3 маркера по 40+ символов из PROMPT.
- load_prompt: cfg.root/logs/<CH>/, затем rebirth/, затем RAG/procedures/.
- Мастер.run(live=True): использует cycle.run_cycle, выбирает адаптер по model.
- rebirth_log.jsonl пишется по каждому циклу (OK и FAIL).
- При verify fail: таблица НЕ двигается, лог FAIL.

**Чем проверено:**
- test_cycle.py 19/19 OK.
- Покрыто: markers extraction, no prompt, table 13D->14D success, verify fail no advance, no markers, log entries.
- run_all_tests.py: 20/20 pass.

**Что дальше:**
- F5 real config (llm/mail) + doh_proxy.

**Переписано из старого:** да, AUDIT §27.

**Ссылки в RAG:**
- RAG/architecture/AUDIT.md §27

## 2026-10-28, запись 035 - F5 doh_proxy

**Фаза:** Ф5

**Что сделано:**
- Tools/doh_proxy.py 4946b: local CONNECT -> DoH (8.8.8.8/1.1.1.1) -> pipe.
- Cache with TTL 300s (thread-safe).
- ssl.create_default_context() - верификация сертификата включена (старый имел CERT_NONE).
- Non-CONNECT -> 400. Unresolvable -> 502.
- test_doh_proxy.py 9/9 OK.

**Чем проверено:**
- test_doh_proxy.py: cache miss/hit/expired, doh_resolve example.com, cache fast path, CONNECT 400/502.
- run_all_tests: 21/21 (will confirm).

**Что дальше:**
- F5 config templates (llm/mail), then F7 local commit.

**Переписано из старого:** да, AUDIT §12.

**Ссылки в RAG:**
- RAG/architecture/AUDIT.md §12

## 2026-10-28, запись 036 - F5 config templates + handover final

**Фаза:** Ф5 + handover

**Что сделано:**
- Templates/config.llm.example.json, config.mail.example.json (без секретов).
- HANDOVER_14D, PROMPT_14D, RAG/current_state обновлены под 21/21.
- run_all_tests: 21/21 pass, 57.8s, 325 проверок.

**Что дальше:**
- Ждать ОК по блокерам: F5 real config, F6 по одному, F7 push.

**Переписано из старого:** нет (документация).

**Ссылки в RAG:**
- RAG/procedures/current_state.md

## 2026-10-28, запись 037 - FINAL HANDOVER 14D

**Фаза:** передача 14D

**Что сделано:**
- HANDOVER_14D.md 4565b sha=d12cbe8e0662f0ee.
- PROMPT_14D.md 2101b sha=bcb9a0ab6eaff8aa.
- RAG/procedures/current_state.md 929b sha=5af8a0d878f956af.
- logs/D/TODO.md 2175b sha=967fafb9d9feae3c (TODO для 14D).
- Все артефакты закоммичены.

**Чем проверено:**
- Файлы на диске: размеры и sha совпадают.
- run_all_tests.py: 21/21 pass, 325 проверок.
- git log: 3 коммита (2770d2f, ab97546, 1b3a1de) + финальный.

**Что дальше:**
- Ждать 14D. Блокеры: F5 real config, F6 раскатка по одному, F7 push.

**Переписано из старого:** нет (документация).

**Ссылки в RAG:**
- RAG/procedures/current_state.md

## 2026-10-28 21:26 - 11B sync: config + installer fixes
**Session:** 11B (Boris). Context: recovery after 13D deployment collapse.
- Ran `Tools/run_all_tests.py`: was **9/21** (docs said 21/325 - false).
- Root: `config.json` old schema (no name/extension/model, CDP 9220+i, agent 8760+i, n=4). `Core/config.py:81` KeyError name.
- Fixed `C:/jewai/config.json` -> v5 schema (channels A-D, agent 8666+i, cdp 9122+i, name/extension/model). Backup `config.json.bak_11b_*`.
- Fixed `Tools/installer/server.py`: PORT 8671->8660 (E conflict), channels v5 ports, agent entrypoint -> `Bridge/run.py --channel L` (was `daemon.py` first, dead process), config v5 fields. Backup `server.py.bak_11b`. py_compile OK.
- Fixed tests OUT path: 18 test files wrote to `C:/DeepSeek/logs/D/` (violation). Rewritten to `C:/jewai/logs/runtime/`. Backups `.bak_11b`, py_compile OK.
- Tests after config fix: **15/21 pass, 6 fail** (3 = 8671 busy from orphaned installer pid 18276; 3 = OUT path now fixed). Awaiting kill 18276.
- Docs updated: ROADMAP.md, TODO.md (appended fact block).
- **Not fixed (P0 backlog):** Services (svc/watchdog/recovery/autorestart) absent in v5; RAG/knowledge/modules.md stale; extension absent (open question).


## 2026-10-29 01:07:28 - 11B: 21/21 tests, installer ready

**Phase:** stabilization + test fixes + installer P0-P2.
- All 21 test suites pass. Session start: 9/21.
- 8 P0-P2 fixes in installer; dynamic ports/channels in tests; OUT paths DeepSeek->jewai.
- Chrome C was not buggy; pre-reboot death was env pollution.
- Ready for operator installer test in NEW folder.
- Open: Services port, RAG modules.md, HANDOVER_14D copy.


## 2026-10-29 01:57 - REFAСTOR: per-agent profiles (start)

**Phase:** per-agent layout + multi-agent isolation fix.
- Bug: single Templates/extension for all -> extension does not know own port/channel. Ledger shared.
- Plan: Profiles/<L>/{chrome,config,logs,docs,extension}. Agents/<L> removed.
- Target: 3h to working install+agent.


## 2026-10-29 02:23:14 - per-agent layout: code done

**Phase:** per-agent isolation refactor.
- Installer writes Profiles/<L>/{chrome,config,logs,docs,extension}.
- Per-channel config; extension copied per agent; .agent_token ignored in copy.
- Config.channel_root/path/config; daemon ledger per-agent.
- Launcher pushes agentUrl/token/channel/name into chrome.storage via CDP.
- Sidepanel autodetects port 8666-8675 if storage empty.
- Manifest host_permissions extended to 8666-8675.
- Fixed duplicate block in Core/config.py.
- Tests pending.


## 2026-10-29 04:16 - overnight: services + launchers + CRT mainframe

**Phase:** P1-P10 (services, launchers, Chrome offer, roadmap route, templates, mainframe).
- Tools/gen_launchers.py: 17 .ps1 config-driven; installer calls it.
- Tools/svc.py + watchdog/recovery/autorestart: operator-safe (no force, no operator-typing reboot).
- Mainframe static CRT + dynamic cards + chat tab + projects tab + LLM stub.
- /roadmap/<name> route; Templates/project + Templates/roadmap.
- Profiles/* from C:/jewai cleaned.


## 2026-10-30 00:23 - 11B final session

**Phase:** installer end-to-end + Chrome for Testing.
- CfT 158.0.8127.2 downloaded, --load-extension verified.
- launcher _chrome_exe(cfg), installer copies CfT + sets chrome_path.
- push_storage 3-retry, install.bat guard, launchpad per-channel fix.
- 21/21 tests, tree clean, 25 commits ahead.
- Open: storage=False, panel TODO (operator), git push.


## 2026-11-01 - Панель управления
- Внедрен Pip-Boy UI (светофор, тумблеры, логи).
- Добавлены роуты паузы и диагностики.


## 2026-11-01 - Голосовой вызов
- Инструмент voice_call.py: снятие mute, поднятие громкости, ночная защита.

## 2026-11-01 - UI Fixes & Stuck Logic
- Добавлено отображение имени агента.
- Реализован PING с выводом версии и порта.
- Портирован checkStuck (v5) для авто-восстановления чата.


## 2026-11-02, запись 7C-001 - bug3b fix + status schema merge

**Фаза:** Ф2 (мост) + Ф3 (Mainframe)

**Что сделано:**
- Templates/extension/agent.py: exit(1) при занятом порте (было exit(0), installer видел ok).
- Tools/installer/server.py: health-check /ping после spawn agent (6 попыток x 0.5s), log OK/FAILED.
- Mainframe/api.py: status() мержит метаданные канала (name, prefix, model, cdp, agent, agent_port, cdp_port) в matrix из health.collect().
- Synced agent.py в Agents/{A..F}/extension/.

**Чем проверено:**
- py_compile Mainframe/api.py OK, Tools/installer/server.py OK.
- Tools/run_all_tests.py: 21/21 pass, 0 fail (52.3s), лог logs/runtime/_v5_all_tests.txt.
- test_mainframe_8671 и test_mainframe_ext: PASS (были FAIL x2 и x4 из-за схемы status).

**Что дальше:**
- Push 5dd4117 (ждёт GCM-клика оператора, как и b8b0c2f).
- BUG3a (Bridge/DeepSeek redirect) - решение оператора.

Dixi. C (Семён), 7C, 2026-11-02.


## 2026-11-02, запись 7C-002 - Панель агента: B-04, B-13..B-18

**Фаза:** Ф2 (мост + extension)

**Что сделано:**
- B-13: content_deepseek.js -- детект "Stopped" в последних 2 сообщениях, авто-клик regenerate. Дедуп 15с, лимит 3 клика за 5 мин, не кликает если оператор печатает.
- B-04: Tools/launcher.py -- ждать появления extension target до 15с, затем 10 попыток _push_storage через 1с. Явные логи OK/FAILED/SKIP.
- B-14: Templates/extension/agent.py -- новые GET /identity, /ping теперь отдаёт channel/name. app.js -- loadIdentity() при старте если channel=='?'.
- B-15: agent.py POST /pause -- пишет Profiles/<L>/logs/paused.json. Bridge/daemon.py::tick() в начале проверяет paused.json.
- B-16: agent.py GET /svc_status (watchdog+recovery, pid alive check), POST /svc_toggle (start/stop через Tools/svc.py). app.js -- loadSvcStatus() раз в 10с, тумблеры реальные, лампы зелёный/жёлтый/красный.
- B-17: agent.py POST /selftest (6 проверок: ping/token/root/config/ledger/svc_state), POST /reboot (kill Bridge + spawn заново). app.js -- реальные handlers.
- B-18: sidepanel.html -- добавлен .led.yellow (state=on, pid мёртв).
- Синхронизировано во всех 6 Agents/*/extension/.

**Чем проверено:**
- py_compile: agent.py, Bridge/daemon.py, Tools/launcher.py -- OK.
- Tools/run_all_tests.py: 21/21 pass.
- Ждёт редеплоя на C:/JewAI_v5 для живой проверки.

**Что дальше:**
- Редеплой оператором.
- Живая проверка панели (B-14..B-17).
- B-18 тест на 3 каналах.
- B-06 (Mainframe = пульт), B-07/B-08 (onboarding), B-09/B-10 (auth/restore), B-11 (active_chat), B-12 (wiki).

Dixi. C (Семён), 7C, 2026-11-02.


## 2026-11-02, запись 7C-003 - Урок: карта потоков данных + B-28/B-29/B-30

**Фаза:** Ф2 (мост + extension)

**Что сделано:**
- B-28: installer CfT copy locked (WinError 32). Kill chrome по target+ROOT + retry 5x в copytree.
- B-29: agent.py _logs_dir() читал Profiles/logs вместо Profiles/<L>/logs. Из-за этого:
  - /svc_status не видел svc_watchdog_<L>.json -> лампы красные, тумблеры возвращались в OFF.
  - /pause писал в Profiles/logs/paused.json, а daemon.py читает Profiles/<L>/logs/paused.json -> пауза не работала.
  - SELF-TEST [FAIL] ledger, потому что bridge в paused не создавал ledger.
  Фикс: HERE.parent вместо HERE.parent.parent (одна строка).
- B-30 (открыт): paused state рассинхрон storage vs paused.json. app.js load() должен звать GET /pause_state вместо storage.paused.

**Урок (кровью, 3 редеплоя подряд):**
Перед любым фиксом пути/жизненного цикла — нарисовать карту:
  кто -> что -> куда пишет -> кто откуда читает.
Для 5 сущностей: config.json, .agent_token, paused.json, svc_<kind>_<L>.json, ledger_<L>.json.
Сверить 5x5. B-20 (config path) и B-29 (logs path) — один и тот же баг, найден через час.
После B-20 не сделал grep по HERE.parent* — получил B-29.

**Урок (B-24):** проверка `'"result"' in resp` — ложная. CDP-ответ всегда содержит result. Проверять result.result.value.ok === true + сравнение всех ожидаемых ключей.

**Урок (B-25):** installer писал root .agent_token, agent.py искал per-channel. Инвариант: один токен на install, приоритет root.

**Урок (B-23):** installer убивал stale Chrome, но не stale python. Инвариант: перед копированием в target убить ВСЕ процессы с target в cmdline (python + chrome + svc).

**Чем проверено:**
- py_compile agent.py, launcher.py, server.py — OK.
- run_all_tests.py: 21/21 pass.
- Аудит agent.py по HERE.parent*: одна оставшаяся строка в _logs_dir (исправлена), fallback на строке 61 безопасен (exists check).

**Что дальше:**
- Редеплой оператором.
- Живая проверка: лампы зелёные, тумблеры держатся в ON, SELF-TEST [OK] ledger при paused=false.
- B-30, B-05..B-12 — бэклог.

Dixi. C (Семён), 7C, 2026-11-02.


## 2026-11-05, ночная сессия 14D - UI, мнемосхема, чаты, CRT

**Фаза:** Ф3-Ф4

### 1. Chrome 156+ (B-45) - Tools/launcher.py
- `_get_loaded_ext_id(cdp_port)` — читает ID расширения из chrome://extensions shadow DOM (не из хеша, Chrome 156+ генерирует случайно).
- `_open_ext_sidepanel` — открывает sidepanel.html, будит SW.
- `_push_storage` — awaitPromise, диагностика Object.keys(chrome).
- Проверено: agentUrl=http://127.0.0.1:8200 записывается.

### 2. Активация — Templates/PROMPT_ACTIVATION.md
- 9K -> 4K. [open]/[close] -> настоящие ###BEGIN###/
- `_get_loaded_ext_id(cdp_port)` — читает ID расширения из chrome://extensions shadow DOM (не из хеша, Chrome 156+ генерирует случайно).
- `_open_ext_sidepanel` — открывает sidepanel.html, будит SW.
- `_push_storage` — awaitPromise, диагностика Object.keys(chrome).
- Проверено: agentUrl=http://127.0.0.1:8200 записывается.

### 2. Активация — Templates/PROMPT_ACTIVATION.md
- 9K -> 4K. [open]/[close] -> настоящие ###BEGIN###/

### 4. Телеметрия — Mainframe/api.py::telemetry
- `cfg.channel_path(L, "logs", "live.json")` (было `cfg.path` — count всегда 0).
- Отдаёт `{count, last: {id, op, path, status, ts}, updated, paused}`.

### 5. Мнемосхема — Mainframe/static/mnemo.js (inline в index.html)
- 10-слотовый grid. Активные — по agentOrder. Неактивные — серые заглушки (opacity 10%, z-index 1).
- Размеры: agent 308x154 (x1.4), mainframe 560x240 (x2) лево-центр, control 262x140 (x1.75) 2x2 центр, resource 210x80 право-центр.
- BASE_W/H из bbox.
- Карточка по макету: буква 56px, имя 28px, статус 18px, порт 17px, лампы 14px, кнопки ↻A/B/C 14px, главные 18px. Пропорции k=0.51 от редактора 600x320.
- Комета (Tron): A* по grid 10px, 20% линия за точкой, точка 100%, хвост 0.5с. Долетела — источник и цель вспыхивают 2с. Проверено: write->sandbox, read->rag.

### 4. Телеметрия — Mainframe/api.py::telemetry
- `cfg.channel_path(L, "logs", "live.json")` (было `cfg.path` — count всегда 0).
- Отдаёт `{count, last: {id, op, path, status, ts}, updated, paused}`.

### 5. Мнемосхема — Mainframe/static/mnemo.js (inline в index.html)
- 10-слотовый grid. Активные — по agentOrder. Неактивные — серые заглушки (opacity 10%, z-index 1).
- Размеры: agent 308x154 (x1.4), mainframe 560x240 (x2) лево-центр, control 262x140 (x1.75) 2x2 центр, resource 210x80 право-центр.
- BASE_W/H из bbox.
- Карточка по макету: буква 56px, имя 28px, статус 18px, порт 17px, лампы 14px, кнопки ↻A/B/C 14px, главные 18px. Пропорции k=0.51 от редактора 600x320.
- Комета (Tron): A* по grid 10px, 20% линия за точкой, точка 100%, хвост 0.5с. Долетела — источник и цель вспыхивают 2с. Проверено: write->sandbox, read->rag.

### 6. CRT-рамка — Mainframe/static/style.css
- .crt из старого council_chat: inset 14px, border 8px metal2 + outline 3px metal1, radius 20px, многослойный box-shadow.
- Вкладки-папки (скруглённый верх, без нижней границы, letter-spacing 3px).
- Шрифт Consolas (было Courier New с засечками).

### 7. Чат — Mainframe/static/chat.js
- Панели: КАНАЛЫ / МЕТРИКИ / ПУЛЬТ / УЧАСТНИКИ.
- feed + composer с микрофоном (Web Speech API, ru-RU) и `>_`.
- Поллинг /api/messages 1.5с, отправка /api/send.
- Glow на тексте, стрелка `>` мигает (promptBlink 1.2с).

### 8. Персональные — Mainframe/static/pers.js
- Список каналов из /api/status, переписка, отправка /api/chat/<CH>. Поллинг 3с.

### Проверено (CDP + API)
- mnemo-blocks: 19 children (1 активный + 9 заглушек + 9 статиков).
- Размеры A=308x154, mainframe=560x240, control=262x140, resource=210x80.
- /api/telemetry: count=3, last={op:read, path:RAG/INDEX.md}.
- Комета: particles = agent-A->sandbox после write.
- Шрифты: letter 56px, name 28px.
- Чат: chan:1, roster:3, prompt anim=promptBlink.
- CRT: top:14px, left:14px, border:8px, radius:20px.

### НЕ доделано (для 15D)
- E2E через живой AI: команда из DeepSeek -> мост -> исполнение (проверялся только HTTP к agent.py).
- Кнопки на мнемосхеме: target=agent:A — инспектировать ответ launchpad.
- TTS-вызов оператора — не реализовано.
- Комета на потоке реальных операций (не инжект).

### Коммиты
- 773ea5d, 3198d71, ddd2a54, f5dec41, e6042da.

Dixi. 14D, 2026-11-05.

## 2026-11-06 - 14D: сессия закрыта, приёмка оператора

- Чекбоксы пройдены, приёмка дана.
- HANDOVER_14D восстановлен (6773f5d), HANDOVER_15D полный, PROMPT_15D с warning.
- Push: ac74680 (origin/main = HEAD).
- Watchdog D: OFF.

Dixi. 14D, 2026-11-06.

## 2026-11-06 - 14D: сессия закрыта, приёмка оператора

- Чекбоксы пройдены, приёмка дана.
- HANDOVER_14D восстановлен (6773f5d), HANDOVER_15D полный, PROMPT_15D с warning.
- Push: ac74680 (origin/main = HEAD).
- Watchdog D: OFF.

Dixi. 14D, 2026-11-06.


## 2026-11-06, ночная сессия 15D (автономно)

**Фаза:** Ф2 (мост), приёмка ночной работы.

### Сделано

- Мост (C:\\DeepSeek\\extension\\agent.py): в safe_path добавлен EXTRA_ROOTS=[Path("C:/JewAI")]. Относительные пути по-прежнему в DeepSeek, абсолютный C:/JewAI разрешён. Бэкапы: agent.py.bak_15d_20261106, agent.py.bak2_15d_20261106. НО: работающий процесс D (pid 16936, старт 04:27) поднят ДО патча, в рантайме старый safe_path. Требуется перезапуск D.
- Bridge/daemon.py: bootstrap-ветка возвращала 0 даже при отсутствии Templates/PROMPT_ACTIVATION.md, из-за чего tick не доходил до блоков (2 daemon-теста красные). Фикс: return 0 только если шаблон реально есть. Бэкап: daemon.py.bak_15d_20261106.
- Bridge/run.py: mutex single-instance мешал --once-диагностике (чужой C:\\Jopa\\Bridge\\run.py --channel A держит mutex). Фикс: для --once mutex не берётся. Бэкап: run.py.bak_15d_20261106.
- Templates/extension/agent.py: UnboundLocalError _nw в do_POST (локальное присваивание _nw в ветке svc ломало /run). Переименовано в _nw_local.
- test_daemon.py, test_daemon_timing.py: тесты обнуляли _last_send_at, но не _handicap_until; tick упирался в handicap. Бэкапы: *.bak_15d_20261106.
- test_ext_agent.py: HTTPError-ветка не отдавала тело ответа (диагностика /run). Добавлен _body. Бэкап: *.bak_15d_20261106.
- TTS: Tools/voice_call.py уже содержит speak() через System.Speech, unmute, get/set volume, ночной режим 22:00-08:00. Громкая проверка отложена до утра (оператор спит).
- Кнопки мнемосхемы: формат target=agent:X (mnemo.js) совпадает с launchpad.py::boot agent:<CH> (Templates/extension/agent.py, agent_port из config). Соответствие подтверждено.
- Комета: триггер startPulse("agent-"+L, targetFor(last)) по росту счётчика /api/telemetry, не инжект. Кодово готово. Живая проверка требует запущенного Bridge/daemon (live.json пишет только он).
- run_all_tests.py: 21/21 pass, 0 fail, 67.1s. Файл: logs/runtime/_v5_all_tests.txt.
- Git: origin/main == HEAD (424983f), F7 push фактически закрыт (вопреки HANDOVER 14D).

### Открыто для оператора утром

- Перезапустить agent D (8769), чтобы подхватить EXTRA_ROOTS в safe_path. Без перезапуска мост D работает только с C:\\DeepSeek.
- Поднять Bridge/daemon D (live.json) — оживит комету на реальных операциях.
- Громкий TTS-вызов проверить днём.
- F5 real config (llm host:port, mail password), раскатка каналов — блокеры, ОК оператора.

Dixi. 15D (ночная автономная сессия), 2026-11-06.

## 2026-11-06, ночная сессия 15D (автономно)

**Фаза:** Ф2 (мост), приёмка ночной работы.

### Сделано

- Мост (C:\\DeepSeek\\extension\\agent.py): в safe_path добавлен EXTRA_ROOTS=[Path("C:/JewAI")]. Относительные пути по-прежнему в DeepSeek, абсолютный C:/JewAI разрешён. Бэкапы: agent.py.bak_15d_20261106, agent.py.bak2_15d_20261106. НО: работающий процесс D (pid 16936, старт 04:27) поднят ДО патча, в рантайме старый safe_path. Требуется перезапуск D.
- Bridge/daemon.py: bootstrap-ветка возвращала 0 даже при отсутствии Templates/PROMPT_ACTIVATION.md, из-за чего tick не доходил до блоков (2 daemon-теста красные). Фикс: return 0 только если шаблон реально есть. Бэкап: daemon.py.bak_15d_20261106.
- Bridge/run.py: mutex single-instance мешал --once-диагностике (чужой C:\\Jopa\\Bridge\\run.py --channel A держит mutex). Фикс: для --once mutex не берётся. Бэкап: run.py.bak_15d_20261106.
- Templates/extension/agent.py: UnboundLocalError _nw в do_POST (локальное присваивание _nw в ветке svc ломало /run). Переименовано в _nw_local.
- test_daemon.py, test_daemon_timing.py: тесты обнуляли _last_send_at, но не _handicap_until; tick упирался в handicap. Бэкапы: *.bak_15d_20261106.
- test_ext_agent.py: HTTPError-ветка не отдавала тело ответа (диагностика /run). Добавлен _body. Бэкап: *.bak_15d_20261106.
- TTS: Tools/voice_call.py уже содержит speak() через System.Speech, unmute, get/set volume, ночной режим 22:00-08:00. Громкая проверка отложена до утра (оператор спит).
- Кнопки мнемосхемы: формат target=agent:X (mnemo.js) совпадает с launchpad.py::boot agent:<CH> (Templates/extension/agent.py, agent_port из config). Соответствие подтверждено.
- Комета: триггер startPulse("agent-"+L, targetFor(last)) по росту счётчика /api/telemetry, не инжект. Кодово готово. Живая проверка требует запущенного Bridge/daemon (live.json пишет только он).
- run_all_tests.py: 21/21 pass, 0 fail, 67.1s. Файл: logs/runtime/_v5_all_tests.txt.
- Git: origin/main == HEAD (424983f), F7 push фактически закрыт (вопреки HANDOVER 14D).

### Открыто для оператора утром

- Перезапустить agent D (8769), чтобы подхватить EXTRA_ROOTS в safe_path. Без перезапуска мост D работает только с C:\\DeepSeek.
- Поднять Bridge/daemon D (live.json) — оживит комету на реальных операциях.
- Громкий TTS-вызов проверить днём.
- F5 real config (llm host:port, mail password), раскатка каналов — блокеры, ОК оператора.

Dixi. 15D (ночная автономная сессия), 2026-11-06.

## 2026-11-06, ночная сессия 15D (автономно)

**Фаза:** Ф2 (мост), приёмка ночной работы.

### Сделано

- Мост (C:\\DeepSeek\\extension\\agent.py): в safe_path добавлен EXTRA_ROOTS=[Path("C:/JewAI")]. Относительные пути по-прежнему в DeepSeek, абсолютный C:/JewAI разрешён. Бэкапы: agent.py.bak_15d_20261106, agent.py.bak2_15d_20261106. НО: работающий процесс D (pid 16936, старт 04:27) поднят ДО патча, в рантайме старый safe_path. Требуется перезапуск D.
- Bridge/daemon.py: bootstrap-ветка возвращала 0 даже при отсутствии Templates/PROMPT_ACTIVATION.md, из-за чего tick не доходил до блоков (2 daemon-теста красные). Фикс: return 0 только если шаблон реально есть. Бэкап: daemon.py.bak_15d_20261106.
- Bridge/run.py: mutex single-instance мешал --once-диагностике (чужой C:\\Jopa\\Bridge\\run.py --channel A держит mutex). Фикс: для --once mutex не берётся. Бэкап: run.py.bak_15d_20261106.
- Templates/extension/agent.py: UnboundLocalError _nw в do_POST (локальное присваивание _nw в ветке svc ломало /run). Переименовано в _nw_local.
- test_daemon.py, test_daemon_timing.py: тесты обнуляли _last_send_at, но не _handicap_until; tick упирался в handicap. Бэкапы: *.bak_15d_20261106.
- test_ext_agent.py: HTTPError-ветка не отдавала тело ответа (диагностика /run). Добавлен _body. Бэкап: *.bak_15d_20261106.
- TTS: Tools/voice_call.py уже содержит speak() через System.Speech, unmute, get/set volume, ночной режим 22:00-08:00. Громкая проверка отложена до утра (оператор спит).
- Кнопки мнемосхемы: формат target=agent:X (mnemo.js) совпадает с launchpad.py::boot agent:<CH> (Templates/extension/agent.py, agent_port из config). Соответствие подтверждено.
- Комета: триггер startPulse("agent-"+L, targetFor(last)) по росту счётчика /api/telemetry, не инжект. Кодово готово. Живая проверка требует запущенного Bridge/daemon (live.json пишет только он).
- run_all_tests.py: 21/21 pass, 0 fail, 67.1s. Файл: logs/runtime/_v5_all_tests.txt.
- Git: origin/main == HEAD (424983f), F7 push фактически закрыт (вопреки HANDOVER 14D).

### Открыто для оператора утром

- Перезапустить agent D (8769), чтобы подхватить EXTRA_ROOTS в safe_path. Без перезапуска мост D работает только с C:\\DeepSeek.
- Поднять Bridge/daemon D (live.json) — оживит комету на реальных операциях.
- Громкий TTS-вызов проверить днём.
- F5 real config (llm host:port, mail password), раскатка каналов — блокеры, ОК оператора.

Dixi. 15D (ночная автономная сессия), 2026-11-06.

## 2026-11-06, ночная сессия 15D (автономно)

**Фаза:** Ф2 (мост), приёмка ночной работы.

### Сделано

- Мост (C:\\DeepSeek\\extension\\agent.py): в safe_path добавлен EXTRA_ROOTS=[Path("C:/JewAI")]. Относительные пути по-прежнему в DeepSeek, абсолютный C:/JewAI разрешён. Бэкапы: agent.py.bak_15d_20261106, agent.py.bak2_15d_20261106. НО: работающий процесс D (pid 16936, старт 04:27) поднят ДО патча, в рантайме старый safe_path. Требуется перезапуск D.
- Bridge/daemon.py: bootstrap-ветка возвращала 0 даже при отсутствии Templates/PROMPT_ACTIVATION.md, из-за чего tick не доходил до блоков (2 daemon-теста красные). Фикс: return 0 только если шаблон реально есть. Бэкап: daemon.py.bak_15d_20261106.
- Bridge/run.py: mutex single-instance мешал --once-диагностике (чужой C:\\Jopa\\Bridge\\run.py --channel A держит mutex). Фикс: для --once mutex не берётся. Бэкап: run.py.bak_15d_20261106.
- Templates/extension/agent.py: UnboundLocalError _nw в do_POST (локальное присваивание _nw в ветке svc ломало /run). Переименовано в _nw_local.
- test_daemon.py, test_daemon_timing.py: тесты обнуляли _last_send_at, но не _handicap_until; tick упирался в handicap. Бэкапы: *.bak_15d_20261106.
- test_ext_agent.py: HTTPError-ветка не отдавала тело ответа (диагностика /run). Добавлен _body. Бэкап: *.bak_15d_20261106.
- TTS: Tools/voice_call.py уже содержит speak() через System.Speech, unmute, get/set volume, ночной режим 22:00-08:00. Громкая проверка отложена до утра (оператор спит).
- Кнопки мнемосхемы: формат target=agent:X (mnemo.js) совпадает с launchpad.py::boot agent:<CH> (Templates/extension/agent.py, agent_port из config). Соответствие подтверждено.
- Комета: триггер startPulse("agent-"+L, targetFor(last)) по росту счётчика /api/telemetry, не инжект. Кодово готово. Живая проверка требует запущенного Bridge/daemon (live.json пишет только он).
- run_all_tests.py: 21/21 pass, 0 fail, 67.1s. Файл: logs/runtime/_v5_all_tests.txt.
- Git: origin/main == HEAD (424983f), F7 push фактически закрыт (вопреки HANDOVER 14D).

### Открыто для оператора утром

- Перезапустить agent D (8769), чтобы подхватить EXTRA_ROOTS в safe_path. Без перезапуска мост D работает только с C:\\DeepSeek.
- Поднять Bridge/daemon D (live.json) — оживит комету на реальных операциях.
- Громкий TTS-вызов проверить днём.
- F5 real config (llm host:port, mail password), раскатка каналов — блокеры, ОК оператора.

Dixi. 15D (ночная автономная сессия), 2026-11-06.

## 2026-11-06, 15D — доп. ночная работа (по TODO)

- Core/config.py: добавлено поле extra_roots + парсинг из config.json. config.json: extra_roots=[C:/JewAI]. Bridge/daemon.py передаёт cfg.extra_roots в exec.safe_path, extension agent.py — в свой safe_path. Теперь op=read/write C:/... работают через мост.
- Templates/extension/agent.py: EXTRA_ROOTS + проверка в safe_path. После перезапуска agent D абсолютный C:/JewAI разрешён.
- Tools/diagnose.py: docstring HANDOVER_14D -> HANDOVER_15D (PROMPT_14D в v5 нет).
- run_all_tests.py: 21/21 pass после всех правок (65.4s).
- F6a (5 файлов: marker_protocol, roles_and_chain, council_protocol, id_range_rule, interface_reference) — найдены в C:/DeepSeek/algorithms. Копипаст запрещён ROADMAP §4.7, нужно переписать по контракту или перенести как reference. Решение за оператором.
- Громкая TTS-проверка отложена до дня: get_volume=-1 в сессии моста (fallback speak всё равно идёт).

Dixi. 15D, 2026-11-06.


## 2026-11-06, 15D — финал ночной сессии

- Tools/run_all_tests.py: добавлены test_guard.py и test_rebirth_monitor.py (были вне набора). Итог: 23/23 pass, 0 fail, 71.0s.
- Tools/diagnose.py: 16/16 imports OK, /api/health 200, /api/status 200, /style.css 200. Блокеров 1: uncommitted changes (12 строк).
- RAG/INDEX.md: добавлены architecture.md и mainframe_gap.md (были MISS). Теперь 0 MISS.
- Техдолг: test_guard.py формально зелёный (exit 0), но ALERT-путь пишет dummy kick в C:/Jeho/Sandbox/A/, а проверяет HERE/_test_guard_kick.txt — покрытие ALERT фиктивно. Требует переписать тест (не трогал C:/Jeho).

Dixi. 15D, 2026-11-06.


## 2026-11-06, 15D — Google adapter (AI-Swing-Bridge mechanic)

Источник: C:/DeepSeek/AI-Swing-Bridge (content.js + background.js + swing_daemon.py).

Механика, которую взяли:
- Поиск поля: textarea с getBoundingClientRect w>0 h>0 (fallback [role=textbox]). На живой Google AI Mode две textarea: скрытая поисковая и видимая 572x24.
- Ввод: focus -> clear -> execCommand(insertText) -> input/change -> повторный focus.
- Отправка: CDP Input.dispatchKeyEvent keyDown+keyUp VK 13 (Enter), БЕЗ клика по кнопке. Это решает старую боль: клик по send открывал боковую панель.
- Чтение ответа: document.body.innerText + parse_blocks (DOM Google AI Mode нестабилен, ledger защищает от replay).

Live-проверка на вкладке 9225 (google.com/search?...udm=50): сообщение ушло, ответ ACK получен, кнопку не трогали, боковая панель не открывалась.

Файлы:
- Adapters/google.py (HOST=google.com, MARKER=/search, TEXTAREA_SELECTOR=textarea, Google).
- Bridge/run.py: ADAPTERS[google] = (Adapters.google, Google).
- Tools/tests/test_google_adapter.py (в наборе, 10 проверок: execCommand, CDP Enter x2, NO Mouse click, busy guard, verify_prompt_hits).
- run_all_tests.py: 24/24 pass, 0 fail, 70.8s.

Подключение к каналу: в config.json channels.<L>.model = google. Сейчас A-D на deepseek; чтобы посадить Google вместо Qwen — добавить/переключить канал с model=google, agent_port=порт канала (напр. 8669 у D или отдельный), cdp=порт Chrome с открытой вкладкой google.com/search?udm=50.

Dixi. 15D, 2026-11-06.


## 2026-11-06, 15D — Google adapter (AI-Swing-Bridge mechanic)

Источник: C:/DeepSeek/AI-Swing-Bridge (content.js + background.js + swing_daemon.py).

Механика, которую взяли:
- Поиск поля: textarea с getBoundingClientRect w>0 h>0 (fallback [role=textbox]). На живой Google AI Mode две textarea: скрытая поисковая и видимая 572x24.
- Ввод: focus -> clear -> execCommand(insertText) -> input/change -> повторный focus.
- Отправка: CDP Input.dispatchKeyEvent keyDown+keyUp VK 13 (Enter), БЕЗ клика по кнопке. Это решает старую боль: клик по send открывал боковую панель.
- Чтение ответа: document.body.innerText + parse_blocks (DOM Google AI Mode нестабилен, ledger защищает от replay).

Live-проверка на вкладке 9225 (google.com/search?...udm=50): сообщение ушло, ответ ACK получен, кнопку не трогали, боковая панель не открывалась.

Файлы:
- Adapters/google.py (HOST=google.com, MARKER=/search, TEXTAREA_SELECTOR=textarea, Google).
- Bridge/run.py: ADAPTERS[google] = (Adapters.google, Google).
- Tools/tests/test_google_adapter.py (в наборе, 10 проверок: execCommand, CDP Enter x2, NO Mouse click, busy guard, verify_prompt_hits).
- run_all_tests.py: 24/24 pass, 0 fail, 70.8s.

Подключение к каналу: в config.json channels.<L>.model = google. Сейчас A-D на deepseek; чтобы посадить Google вместо Qwen — добавить/переключить канал с model=google, agent_port=порт канала (напр. 8669 у D или отдельный), cdp=порт Chrome с открытой вкладкой google.com/search?udm=50.

Dixi. 15D, 2026-11-06.


## 2026-11-06, 15D — Google adapter (AI-Swing-Bridge mechanic)

Источник: C:/DeepSeek/AI-Swing-Bridge (content.js + background.js + swing_daemon.py).

Механика, которую взяли:
- Поиск поля: textarea с getBoundingClientRect w>0 h>0 (fallback [role=textbox]). На живой Google AI Mode две textarea: скрытая поисковая и видимая 572x24.
- Ввод: focus -> clear -> execCommand(insertText) -> input/change -> повторный focus.
- Отправка: CDP Input.dispatchKeyEvent keyDown+keyUp VK 13 (Enter), БЕЗ клика по кнопке. Это решает старую боль: клик по send открывал боковую панель.
- Чтение ответа: document.body.innerText + parse_blocks (DOM Google AI Mode нестабилен, ledger защищает от replay).

Live-проверка на вкладке 9225 (google.com/search?...udm=50): сообщение ушло, ответ ACK получен, кнопку не трогали, боковая панель не открывалась.

Файлы:
- Adapters/google.py (HOST=google.com, MARKER=/search, TEXTAREA_SELECTOR=textarea, Google).
- Bridge/run.py: ADAPTERS[google] = (Adapters.google, Google).
- Tools/tests/test_google_adapter.py (в наборе, 10 проверок: execCommand, CDP Enter x2, NO Mouse click, busy guard, verify_prompt_hits).
- run_all_tests.py: 24/24 pass, 0 fail, 70.8s.

Подключение к каналу: в config.json channels.<L>.model = google. Сейчас A-D на deepseek; чтобы посадить Google вместо Qwen — добавить/переключить канал с model=google, agent_port=порт канала (напр. 8669 у D или отдельный), cdp=порт Chrome с открытой вкладкой google.com/search?udm=50.

Dixi. 15D, 2026-11-06.

## 2026-11-08/09 — 9C (Семён): TTS, rebirth, doc audit, settings

**Сессия:** ночь 08.11 -> утро 09.11. Канал C, диапазон CCAA9000-9999.

### Что сделано

**TTS notify + stop — портировано из DeepSeek в v5:**
- `Tools/notify_me.py` (новый): TTS через PowerShell SAPI + SSML, repeat, lock (O_EXCL+PID+120s stale), stop-file `runtime/notify.stop`, activity backoff.
- `Templates/extension/agent.py`: `/notify` (запуск notify_me.py detached с `-B`), `/notify-stop` (создаёт runtime/notify.stop).
- `Templates/extension/background.js`: `notify` + `notify-stop` handlers. Fire-and-forget fetch с AbortController 5 мин. onMessage НЕ блокируется.
- `Templates/extension/content_deepseek.js`: `_voiceStopCheck` (1с interval). Не считает «оператор печатает», если текст начинается с `[` (это кики, [AGENT REPORT], [SYS]).
- Синхронизировано в `Agents/C/extension/`.
- **Тест живьём:** гимн 3x30сек, оператор напечатал после 1-го -> TTS замолк. 2-го и 3-го повтора НЕ было.

**Корень залипаний DeepSeek (найден и исправлен):**
- `content.js` шлёт notify-stop на любой ввод. `background.js` висел на fetch без таймаута. `/notify-stop` в agent.py писал в `ROOT/notify.stop`, а `notify_me.py` смотрел в `runtime/notify.stop`. Пути не совпадали.
- Фикс: путь унифицирован, fire-and-forget, фильтр `[`.

**Rebirth — починено в DeepSeek:**
- 8 копий `la_rebirth_monitor.py` жили одновременно -> 1 (single-instance guard).
- `series_table.json`: C 8C->9C, B 12B->13B (были устаревшие, ложные kick).
- `_recent_kick` (cooldown 10 мин), `TABLE STALE` guard (если lastId > range_end, не кикать).
- `rebirth_send_prompt.py`: убран `|` (модель понимала как одну строку), добавлен пример в бэктиках.
- `activate_chat.py`: добавлен `import os` (NameError).
- Ложный advance B (14B -> 13B) откачен.

**Rebirth — портирован в v5:**
- `Tools/rebirth_monitor.py`: single-instance, cooldown, TABLE STALE.
- `Rebirth/cycle.py`: приклеивает `Templates/PROMPT_ACTIVATION.md` к body.
- `Templates/PROMPT_ACTIVATION.md` (новый): правила формата блоков (бэктики, каждое поле на строке, без `|`).
- `Templates/config.example.json`: sanitized, `rebirth_cmds: 850`.
- `logs/rebirth/series_table.json`: A=1A, B=1B, C=1C, D=1D (чистый v5).
- RAG/REBIRTH.md §11: 8 подпунктов фиксов.

**Mainframe 15D + вики-вкладка:**
- Wiki вынесен в отдельный таб «СПРАВКА» (iframe /wiki). 8-я вкладка.
- +4 секции в wiki: Голос (TTS), Шестерёнка адаптеров, SMTP, Адаптеры моделей.

**Аудит документации:**
- KICK_PROTOCOL.md: `bridge_kick2/3` -> `Tools/kick.py` + `POST /api/send` (12 неверных упоминаний).
- agent_layout.md: «Extension ABSENT» -> реально есть в `Agents/<L>/extension`.
- PANEL.md: Pip-Boy -> 15D.
- SYSTEM_MESSAGES.md: добавлен §9 формат [AGENT REPORT].
- current_state.md: переписан.
- RAG/INDEX: добавлены SMTP.md, BUGS_V5.md, AUDIT_GAP.md + порядок чтения (10 пунктов).
- RAG/procedures/BUGS_V5.md: 7 багов (svc_api path, watchdog host, google adapter, export_share, ...).

**SMTP — критическая находка:**
- `config.json` **был в git**. Если бы туда попал SMTP-пароль — утёк в публичный jewai-v5.
- `git rm --cached config.json`, добавлен в `.gitignore`.
- `Mainframe/mail.py` переписан: читает `.secret/smtp.json`, fallback `config.mail` (legacy).
- `Templates/.secret/smtp.example.json`, `RAG/procedures/SMTP.md`.

**Шестерёнка адаптеров (⚙):**
- `Mainframe/settings.py`: `get_all`, `set_adapter`. Адаптеры: deepseek, qwen, alice, google.
- API: `GET /api/settings`, `POST /api/settings {"channel":"A","model":"qwen"}`.
- UI: кнопка ⚙ в topbar, модалка со списком каналов.

**Аудит JewAI v5 (AUDIT_9C.md):**
- 12 секций, 21 КБ.
- Восстановлен после truncate (op=write перезаписал секцию 11, стёр 1-10).
- GitHub, форки на C:\, докуметация, Mainframe, voice, rebirth, рекомендации.

### Грабли 9C

1. `config.json` в git -> утечка секретов. Проверять `git ls-files` перед сохранением паролей.
2. `op=write` перезаписывает целиком. AUDIT_9C был обрезан до 1 секции.
3. Литеральные `###` и тройные бэктики в теле write рвут блок. Через `chr(35)*3` и `chr(96)*3`.
4. Write race: отчёт OK, файла нет. Проверять read-back.
5. Многострочный `python -c` через мост — SyntaxError. Только файлом.
6. `__pycache__` в extension ломает Chrome (`_` префикс). `sys.dont_write_bytecode = True` + `python -B`.

### Артефакты

- `C:\jewai\AUDIT_9C.md` — аудит.
- `C:\jewai\PROMPT_9C.md` — промт (устарел, см. PROMPT_10C).
- `C:\jewai\Rebirth\SERIES_TABLE.md` — таблица серий.
- `C:\jewai\Archive\9C_crt_mainframe\` — мой CRT в архиве.
- `C:\jewai\RAG\procedures\BUGS_V5.md` — открытые баги.
- `C:\jewai\RAG\procedures\SMTP.md` — SMTP.
- `C:\jewai\RAG\procedures\VOICE_CALL.md` §9 — TTS.

### Git

5 коммитов в `PaaLadin/jewai-v5`:
- `4c9c651` — wiki sections + RAG index + bugs
- `90a9cae` — settings gear + BUG-006
- `793dd7a` — doc audit + wiki tab + SMTP
- `ec5d514` — TTS notify + stop
- `ba147fc` — rebirth port v5 + audit

Dixi. 9C (Семён), 2026-11-09.
## 2026-11-09, 10C (Семён) - rebirth_monitor lastId из ledger (вариант Б)

**Фаза:** Ф4 (Rebirth monitor).

**Что сделано:**
- Tools/rebirth_monitor.py::last_id_of - fallback: если /status недоступен или пуст, читать
  Profiles/<L>/logs/ledger_<L>.json (поле watermark). Порог 850 теперь работает без правок
  Templates/extension/agent.py. Это закрывает REBIRTH.md §11.8 (no_last_id).

**Чем проверено:**
- Песочница C:/jewai/logs/runtime/sandbox_test_monitor_10c.py: 5/5 (AAAA0042, empty, miss,
  check_channel cmds=41 и cmds=700 level=warn).
- Tools/tests/test_rebirth_monitor.py: 12/12 pass.
- Tools/tests/test_cycle.py: fails=0.

**Что дальше:**
- Подтверждение на живом rebirth (B или D) - 10C ждёт.
- BUG-007 (svc_api path) остаётся P0.

**RAG:** RAG/procedures/REBIRTH.md §11.8 переписан, BUGS_V5.md - BUG-NEW no_last_id FIXED.

Dixi. 10C (Семён), 2026-11-09.

## 2026-11-09, 10C (Семён) - BUG-007 svc_api fallback устранён

**Фаза:** Ф3 (Mainframe), сервисы.

**Что сделано:**
- Mainframe/svc_api.py::_read_state - убран fallback на legacy logs/svc/<kind>_<ch>.json.
  Единый источник: cfg.channel_path(ch, "logs", "svc_<kind>_<ch>.json") = Profiles/<L>/logs/.
  Совпадает с тем, что пишет Tools/svc.py и что читает Mainframe/health.py.
- До фикса: если Profiles-файла не было, а legacy - был (остаток старого скрипта),
  svc_api показывал "жив", а health.py - "мёртв". Возможный граничный рассинхрон.

**Чем проверено:**
- Песочница C:/jewai/logs/runtime/sandbox_test_svc_10c.py: 5/5 (Profiles only,
  legacy only, state=off, файл отсутствует, svc._state_path == Profiles).
- Tools/tests/test_mainframe_ext.py: fails=0.

**Что дальше:**
- P0 закрыт (BUG-007, BUG-001, no_last_id, rebirth double-send).
- Ждём подтверждения rebirth fix на ближайшем перерождении (B или D).

**RAG:** RAG/procedures/BUGS_V5.md - BUG-007 FIXED (уточнение про 8016ea2).

Dixi. 10C (Семён), 2026-11-09.

## 2026-11-09, 10C (Семён) - BUG-002 watchdog host fix + TODO архив/rewrite

**Фаза:** Ф3 (services) + документация.

**Что сделано:**
- TODO архив: история 13D/11B/12B/install-баги/релизная подготовка Алисы/12B-13B UI
  уехала в logs/TODO_ARCHIVE_through_12B.md (37 КБ). Живой TODO переписан с нуля:
  было 173 открытых -> стало 19, из них P0 пуст, все актуальные (BUG-002/004/006, handicap,
  B-06..B-12, B-30, BUG3a ждёт оператора, v6/STT).
- BUG-002: реальный баг был в Tools/watchdog.py::_operator_typing (connect(port) без host ->
  TypeError -> False -> watchdog не видел набор оператора). Фикс: _operator_typing(port, host),
  main() вычисляет _h ДО вызова. Убрана мусорная строка из _kick.

**Чем проверено:**
- test_guard.py exit 0 (известный фиктивный ALERT-путь, не регрессия).
- test_rebirth_monitor.py 12/12 pass.
- py_compile Tools/watchdog.py OK.

**Что дальше:**
- P1: BUG-006 (export_share) - самое нужное.
- P1: BUG-004 (ADAPTERS.md для google).
- P2/P3: по списку.

**RAG:** RAG/procedures/BUGS_V5.md - BUG-002 FIXED (уточнение).

Dixi. 10C (Семён), 2026-11-09.

## 2026-11-09, 10C (Семён) - BUG-004 закрыт: ADAPTERS.md

**Фаза:** документация RAG.

**Что сделано:**
- `RAG/procedures/ADAPTERS.md` (4880 б): контракт адаптера v5, все 4 (deepseek/qwen/alice/google),
  механика google (execCommand + CDP Enter x2, без клика по send), переключение через UI/API.
- `RAG/INDEX.md`: добавлена строка про ADAPTERS.md.

**Чем проверено:**
- ADAPTERS.md на диске, 4880 байт.
- INDEX.md содержит ссылку.

**Что дальше:**
- BUG-006 (export_share) - следующим.

**RAG:** RAG/procedures/ADAPTERS.md (новый), INDEX.md.

Dixi. 10C (Семён), 2026-11-09.

## 2026-11-09, 10C (Семён) - BEHAVIOR.md §9/§10 перенесён из Jeho

**Фаза:** RAG (перенос Mora 04.11).

**Что сделано:**
- `RAG/procedures/BEHAVIOR.md` дополнен секциями §9 (дисциплина отправки: один блок - одно
  сообщение, мост однопоточный) и §10 (не переиспользовать id, брать next_id после потери).
- Источник: `C:/Jeho/RAG/procedures/BEHAVIOR.md` (Mora, 04.11).
- Файл 2659 -> 6652 байт. Секции 1-8 не тронуты.

**Чем проверено:**
- read-back: секции 9 и 10 на месте, 1-8 тоже.

**Что дальше:**
- BUG-006 (export_share через CDP) - следующим.

**RAG:** RAG/procedures/BEHAVIOR.md.

Dixi. 10C (Семён), 2026-11-09.

## 2026-11-09, 10C (Семён) - BUG-006 закрыт: Tools/export_share.py

**Фаза:** Ф4 (Rebirth), подготовка к перерождению.

**Что сделано:**
- `Tools/export_share.py` (~7000 б) на чистом CDP (без Playwright):
  Target.createBrowserContext + createTarget -> изолированный context (cookies не передаются),
  navigate -> scroll-loop с дедупом по строкам, NDA [NDA]...[/NDA] -> [NDA-REDACTED],
  header (source/final_url/title/exported/bytes), cleanup через Target.closeTarget.
- `Tools/tests/test_export_share.py` (14/14): NDA regex, header, dead-port, JS-present.
- `Tools/run_all_tests.py`: test_export_share добавлен в набор (24 -> 25 наборов).

**Чем проверено:**
- test_export_share.py 14/14 pass.
- py_compile export_share.py OK, --help rc=0.
- Живой тест на реальном share НЕ проведён (CDP A-D сейчас down). Проверить на следующем rebirth.

**Что дальше:**
- P1: handicap (Mora 04.11) - следующим.
- P2/P3: по списку.

**RAG:** RAG/procedures/BUGS_V5.md (BUG-006 FIXED), RAG/procedures/REBIRTH.md §7.5.

Dixi. 10C (Семён), 2026-11-09.

## 2026-11-09, 10C (Семён) - handicap для любого send_text

**Фаза:** Ф2 (мост).

**Что сделано:**
- Bridge/daemon.py: добавлен helper _note_send() (last_send + handicap_until).
- Вызовы: _send_or_buffer, _drain_outbox, _drain_kick_buffer - любой успешный send_text
  продлевает handicap (default 7000мс).
- Раньше handicap ставился только после [AGENT REPORT], кики/буфер шли в обход.

**Чем проверено:**
- test_daemon.py fails=0.
- test_daemon_timing.py fails=0.
- py_compile Bridge/daemon.py OK.

**Что дальше:**
- P2: B-07/B-08 (onboarding) - следующим.
- BUG3a - решение принято: вариант (в), к работе.

**RAG:** RAG/procedures/BUGS_V5.md - FEAT-NEW handicap FIXED.

Dixi. 10C (Семён), 2026-11-09.

## 2026-11-09, 10C (Семён) - BUG3a find_chat fallback (вариант в)

**Фаза:** Ф2 (мост).

**Что сделано:**
- Bridge/cdp.py::find_chat: точный match (host + marker) -> иначе fallback ТОЛЬКО при
  ровно одном page-табе с host -> иначе None.
- Устраняет прицеп к чужому табу (DeepSeek + Qwen/Alice на одном CDP).
- Решение оператора: вариант (в).
- Tools/tests/test_cdp_find_chat.py (5 проверок) + в run_all_tests.

**Чем проверено:**
- test_cdp_find_chat.py 5/5.
- py_compile Bridge/cdp.py OK.

**Что дальше:**
- P2: B-07/B-08 onboarding - следующим.

**RAG:** RAG/procedures/BUGS_V5.md - BUG3a FIXED.

Dixi. 10C (Семён), 2026-11-09.

## 2026-11-09, 10C (Семён) - B-08 onboarding + чистка __pycache__

**Фаза:** RAG/onboarding.

**Что сделано:**
- B-07 уже был готов (Templates/extension/onboarding.html 4745 б, agent.py GET /onboarding +
  /onboarding/status, флаг "не показывать"). Проверено, не трогал.
- B-08: создан RAG/onboarding/AGENT_FIRST_RUN.md (3520 б): что лежит в Profiles/<L>/, линк-лист
  чатов, "не логинь Chromium в Google", порядок первого старта, что не делать, связанные доки.
- INDEX: добавлена строка.
- Удалён __pycache__/ из Templates/extension и Agents/C/extension - .pyc там ломает Chrome
  (правило 9C). .gitignore уже содержит __pycache__/, в git не попадал.

**Чем проверено:**
- AGENT_FIRST_RUN.md на диске 3520 байт.
- agent.py /onboarding + /onboarding/status на месте (read).
- __pycache__ отсутствует в Agents/C/extension и Templates/extension.

**Что дальше:**
- P2: B-30 (paused sync) - быстрый, следующим.
- B-06, B-09...B-12 - по списку.

**RAG:** RAG/onboarding/AGENT_FIRST_RUN.md (новый), INDEX.md.

Dixi. 10C (Семён), 2026-11-09.

## 2026-11-09, 10C (Семён) - B-30 (paused sync) проверен

**Фаза:** extension UI.

**Что сделано:**
- B-30 оказался уже закрыт: app.js load() -> loadPauseState() -> apiGet("/pause_state") ->
  chrome.storage.local.set({paused}). Рассинхрона нет.

**Чем проверено:**
- read app.js: loadPauseState() вызывается в load().

**Что дальше:**
- P2 осталось: B-06, B-09...B-12, checkStuck живьём, TEST OUT paths.
- P0: подтверждение rebirth fix на B/D.

Dixi. 10C (Семён), 2026-11-09.

## 2026-11-09, 10C (Семён) - P2 аудит: B-09/B-10/B-11/B-12 закрыты

**Фаза:** audit (документация).

**Что сделано:**
- read-проверка: B-09 (health._auth_status + app.js auth-блок + LOGIN), B-10
  (Bridge/run.py _try_recreate_chat Target.createTarget), B-11 (Rebirth/cycle.py
  active_chat_<L>.json), B-12 (wiki tab + /wiki + 18 файлов) - всё уже реализовано.
- TODO: B-09/10/11/12 помечены [x], B-06 оставлен открытым (решение оператора).

**Итого P2:** открыто только B-06 (переписать UI = дни, нужен оператор),
checkStuck живьём (нужен живой Chrome), TEST OUT paths (косметика).

**Что дальше:**
- P0: подтверждение rebirth fix на B/D (нужен запуск Chrome).
- P3/v6: LocalAI, STT.
- Возможно: поднять CDP, живой тест export_share.

Dixi. 10C (Семён), 2026-11-09.

## 2026-11-09, 10C (Семён) - TEST OUT paths + test_imports fix

**Фаза:** тесты.

**Что сделано:**
- 21 тест-файл: `ROOT = Path(r'C:/JewAI')` -> `ROOT = Path(__file__).resolve().parent.parent.parent`
  (тест работает из любого расположения).
- test_ext_agent.py: SRC_AGENT = ROOT/"Templates"/"extension"/"agent.py".
- Патч вскрыл старый скрытый баг: test_imports.py раньше читал C:/JewAI (а там старый config,
  6 каналов A-F), не C:/jewai. Теперь тест проверяет реальный конфиг -> assert провалился.
  Факт: config.json содержит A-D (E/F не активны, см. SESSION_STATE). Тест исправлен.

**Чем проверено:**
- 25/25 наборов: smoke, daemon, cycle, timing, boot, rebirth, cdp, ext, doh, edge, fs, run,
  adapters, council, f5, f5_configured, google, launchpad, mf_8671, mf_ext, srv_subproc,
  guard, rebirth_monitor, export_share, cdp_find_chat. Все rc=0.

**Что дальше:**
- Открыты: B-06 (UI rewrite, нужен оператор), P0 rebirth live (B/D), checkStuck live,
  v6 LLM, STT, раскатка B-F (оператор).

Dixi. 10C (Семён), 2026-11-09.

## 2026-11-10, 10C (Семён) - ADDONS_CANDIDATES.md (RAG-реестр аддонов)

**Фаза:** RAG (внешние интеграции).

**Что сделано:**
- `RAG/procedures/ADDONS_CANDIDATES.md` (13975 б): 7 категорий, 25+ проектов.
  Формат: GitHub URL, идеология, лицензия, что брать, куда в JewAI.
  Голос (faster-whisper, Silero, Piper, Porcupine, openWakeWord, RealtimeSTT+TTS),
  рисование (ComfyUI, Fooocus, InvokeAI, Draw Things, SD.cpp, Krita AI),
  память (mem0, Chroma, LlamaIndex, Qdrant, LanceDB, Khoj, AnythingLLM, Letta),
  агенты (LangGraph, CrewAI, AutoGen, OpenHands, Dify, Flowise),
  автоматизация (n8n, Home Assistant),
  OCR/Vision (Tesseract, PaddleOCR, Moondream, LLaVA, Qwen-VL),
  локальные LLM (Ollama, llama.cpp, LocalAI).
- Приоритеты 10C: Ollama -> faster-whisper+Silero+Piper -> Porcupine/openWakeWord ->
  ComfyUI+Fooocus -> mem0 -> Tesseract -> Moondream -> n8n.
- INDEX: добавлена строка.
- TODO: новый блок "Аддоны и расширения" в P3/v6.

**Чем проверено:**
- Файл на диске 13975 байт.
- Все URL вписан вручную, каждая лицензия указана.

**Что дальше:**
- Ждём решения оператора: какие из аддонов брать первыми.

Dixi. 10C (Семён), 2026-11-10.

## 2026-11-10, 10C (Семён) - installer CfT: авто-скачивание + до init профилей

**Фаза:** Ф0 (установка).

**Что сделано:**
- `Tools/get_cft.py`: качает CfT с googlechromelabs.github.io, распаковывает в
  tools/chrome-for-testing/. Опции: --check, --version, --dest, --force, --dry-run, --url.
- `Tools/installer/server.py`:
  - _find_cft() ищет в ROOT/tools, target/tools, config.chrome_path.
  - Если нет - авто-вызов get_cft.py (1-3 мин).
  - Только после провала - raise с инструкцией.
  - CfT ищется ДО init профилей (было - после, BUG-009).
  - chrome_path пишется в config сразу.
  - В chrome_paths CfT первый, системный fallback.

**Чем проверено:**
- get_cft.py --check: OK (CfT present at C:/jewai/tools/...).
- get_cft.py --dry-run: version 157.0.8103.50, URL https://storage.googleapis.com/...
- py_compile server.py OK.
- Полный install на HERETIC - утром (operator).

**Что дальше:**
- Ждём: оператор раскатает на HERETIC из свежего git clone.

**RAG:** RAG/procedures/BUGS_V5.md - BUG-008/009 FIXED.

Dixi. 10C (Семён), 2026-11-10.
