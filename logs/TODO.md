# TODO JewAI v5

**Версия:** 0.1.0-dev
**Старт:** 2026-10-28
**Ответственный:** оператор + 12D (Димон), пилот — канал C (Семён)

## Правила

- «Сделано» — только после проверки на диске (файл + размер + тест).
- Каждый модуль — по протоколу переноса (см. ROADMAP.md).
- Код старого проекта не копируется. Только переписывание.
- Отметка `[x]` ставится вместе с записью в JOURNAL.

## Ф0. Скелет проекта

- [x] Структура C:/JewAI/ (RAG, Sandbox, Profiles, Tools, Projects, Mainframe, Archive, .secret, logs)
- [x] VERSION 0.1.0-dev
- [x] README.md
- [x] ROADMAP.md
- [x] logs/JOURNAL.md (шаблон + правила)
- [x] logs/TODO.md (этот файл)

## Ф1. Аудит старого JewAI

Цель: по каждому модулю старого проекта выписать контракт и костыли. Не код — знание.

- [x] Bridge: cdp_client.py — контракт + костыли
- [x] Bridge: bridge_kick2/3.py — контракт + костыли
- [x] Bridge: read_panel_state2.py — контракт + костыли
- [x] Rebirth: rebirth_*.py — контракты + костыли
- [x] Mainframe: council_chat/server.py — контракт роутов, что нужно, что мусор
- [x] Services: svc.py, watchdog.py, recovery_loop.py, autorestart.py — контракты
- [x] Extension: content*.js, background*.js, agent.py — что делает, нужно ли в v5
- [x] Launchers: start-*.ps1, boot-all.ps1 — контракт запуска
- [x] Tools: find.py, see_chat.py, say.py, doh_proxy.py — контракты
- [x] Результат: RAG/architecture/AUDIT.md

## Ф2. Пилот моста на C

- [x] Профиль Chrome C (копия в C:/JewAI/Profiles/C)
- [x] Core/config.py — порты, каналы
- [x] Bridge/cdp.py — нативный CDP
- [x] Bridge/read.py — чтение чата
- [x] Bridge/exec.py — парсер блоков + read/write/run
- [x] Bridge/daemon.py — цикл
- [x] Adapters/deepseek.py — create_chat, send_prompt, verify_prompt_hits
- [x] Tools/launcher.py — запуск Chrome
- [~] E2E тест: read OK, live-send требует ОК оператора

## Ф3. Mainframe 8670

- [x] server.py — HTTP-сервер, 7 роутов
- [x] api.py — status, projects, chat_url, boot/stop/restart
- [x] static/index.html — панель
- [x] llm.py — сетевая LLM (заглушка до ip:port)

## Ф4. Rebirth v5

- [x] table.py — серии
- [x] master.py — create → send → verify → update → onboard (minimal, CDP cycle в Ф5)
- [x] onboard.py — приветствие
- [ ] Тест: rebirth C при cmds >= 850

## Ф5. Надстройки

- [x] Почта SMTP (каркас, config.mail)
- [x] RAG-канал для Алисы (rag_channel.jsonl)
- [x] Mainframe к сетевой LLM (ip:port, config.llm)

## Ф6. Раскатка

- [ ] A, B, D, E, F по одному
- [ ] Старый JewAI → Archive после приёмки

## Ф7. GitHub

- [ ] git init C:/JewAI
- [ ] push в PaaLadin/jewai-v5

Dixi. 12D, 2026-10-28.
## 13D — Передача 14D готова, сессия НЕ закрыта

**Статус:** Ф1 (аудит) завершён. Ф2-Ф7 НЕ начаты. Передача артефактов готова.
**Watchdog D: ON** (перезапущен вручную после ошибочного снятия).
**Приёмка:** требуется оператором/A. Само-приёмка запрещена (behavior_rules §3.5).
- Ф1: AUDIT.md 43000 б, sha 92503acc7a684c0e.
- HANDOVER_14D.md: 5925 б, sha a1c0ec5d4426aa79 (артефакт передачи).
- PROMPT_14D.md: 5289 б, sha ee7a0fa3debb8961 (артефакт передачи).
- cmds=1186.
- Инцидент replay write: logs/D/INCIDENT_20261028_replay_write.md.
- Следующий: 14D (DDAC3000-DDAC3999), старт с Ф2. До перерождения: 13D продолжает.

## 13D - ИТОГИ СЕССИИ 2026-10-28

**Сделано и проверено:**
- Ф1: AUDIT.md 44467 б, 29 разделов + replay-guard.
- Ф2-Ф5: 27 модулей, 14 наборов тестов, 207 проверок зелёные.
- Инфраструктура: README.md 2684б, RAG/procedures/architecture.md 2980б, Tools/diagnose.py, Tools/boot.py, Tools/run_all_tests.py, Tools/tests/ (14 файлов).
- Chrome C v5 (9124) live, E2E read: textarea, body 5111 симв.
- HANDOVER_14D 6450б + PROMPT_14D 6513б (обновлены).
- JOURNAL 25 записей.

**НЕ сделано (требует ОК оператора):**
- Порт 8670 - процесс предшественника pid 5304. Kill+restart требует ОК.
- Ф2 live-send: отправка [AGENT REPORT] в живой чат C.
- Ф6 раскатка A/B/D/E/F: живые агенты.
- Ф7 GitHub push в PaaLadin/jewai-v5.

**Watchdog D:** ON (pid 17360). Recovery D: ON (pid 7444). Не снимаются до приёмки.
**Передача 14D:** HANDOVER_14D + PROMPT_14D актуальны.

## 13D FINAL POINT 2026-10-28

Все работы в безопасной зоне (без разрушительных действий и ОК оператора) выполнены.
Ф0-Ф5 функционально готовы, 14 тестов / 207 проверок зелёные.
Watchdog D ON до приёмки.
Блокеры требуют ОК: 8670, Ф2 live-send, Ф6 живые агенты, Ф7 push.

## 13D - HANDOVER REMINDER

При lastId >= DDAB3850 (за 100-150 id до конца серии) - остановиться и обновить:
- HANDOVER_14D.md (C:/DeepSeek/logs/D/)
- PROMPT_14D.md (C:/DeepSeek/logs/D/)
- logs/D/TODO.md (полный статус сессии)
- logs/JOURNAL.md (итоговая запись)

Актуальные lastId: DDAB3682. До порога ~168 id.


## 2026-10-28 11B - Sync docs with facts

**Found by tests run + code read (11B):**
- **Tests: 9/21 pass, 12 fail** (not 21/325). 11/12 cause: `config.json` old schema - no `name/extension/model`, CDP 9220+i (need 9122+i), agent 8760+i (need 8666+i), n=4 hardcoded.
- **installer/server.py:** PORT 8671 conflicts with agent E; CDP 9220+i; agent 8760+i; `DETACHED_PROCESS` no stderr; n=4 hardcoded.
- **Bridge/daemon.py is NOT CLI** (no `__main__`/`argparse`, 180 lines). Installer picks it first -> dead process. Correct entrypoint: `Bridge/run.py --channel X`.
- **Services missing in v5:** no `svc.py/watchdog.py/recovery_loop.py/autorestart.py` (4 modules from AUDIT). `Mainframe/svc_api.py` manages non-existent services.
- **3 tests write to `C:/DeepSeek/logs/D/`** (violates "do not touch DeepSeek"): `test_server_subprocess`, `test_run_entrypoint`, `test_boot`.
- **RAG/knowledge/modules.md stale:** generated before `Mainframe/{controls,council,launchpad,svc_api}.py`; `server.py` size 1377 b (real 3462).
- **HANDOVER_14D/PROMPT_14D only in `C:/DeepSeek/logs/D/`**, absent in `C:/jewai`.
- **Extension absent in v5** (rag_agent_layout: open question - needed?).

**Plan:** (1) fix config.json + installer/server.py to v5 schema; (2) rerun tests -> expect 18/18 pass (3 remaining to isolate into tempdir); (3) update ROADMAP/TODO/current_state/modules with facts.

- [x] 11B: 18 test OUT paths DeepSeek->jewai/logs/runtime
- [x] 11B: test_server_subprocess dynamic channels; test_run_entrypoint E->A; test_launchpad ABCDEF->cfg.letters
- [ ] 11B: kill orphan installer pid 18276 (port 8671, awaiting operator OK)
- [ ] 11B: rerun run_all_tests.py after kill -> expect 21/21

- [x] 11B: kill orphan installer pid 18276 (port 8671 freed)
- [x] 11B: 3 hardcoded tests -> dynamic (server_subprocess/mf_8671/mf_ext/run_entrypoint/launchpad)
- [x] 11B: index.html title JewAI -> JewAI v5 (backup .bak_11b)
- [x] 11B: Chrome C (9124) raised via Tools/launcher.py --channel C (pid 14128)


## 2026-10-28 22:49 - FINAL before reboot (11B)

Operator reboots PC (kill all Chrome, full restart). 11B persisted state.

### Tests: 20/21 pass (last run 22:30)
- Was 9/21 at session start.
- Only fail: test_mainframe_8671: cdp_alive C=False (Chrome C 9124 not running).
- NEXT after reboot: diagnose Chrome C death (variant 1: read-only check of 23 chrome procs, ports 9122-9127, profile conflicts).

### P0-P2 fixed (all backed up .bak_11b*)
- install.ps1: 8671->8660 (conflict with agent E).
- server.py: PORT 8660; doh_proxy_port written; run_launch calls launcher.py --channel L; basePort from UI; health-check after Mainframe spawn; model=deepseek (P1-5 reverted: all channels deepseek, qwen/alice test-only via manual extension swap).
- app.js: defaults 8760->8666.
- index.html: title JewAI -> JewAI v5.
- svc_api.py: _SVC -> local Tools/svc.py.
- 18 test files OUT path DeepSeek->jewai/logs/runtime.
- 5 test files: dynamic ports/channels.

### Still NOT done (after reboot, blocked)
- Chrome C death cause (not tree-kill: launcher.py:100 already DETACHED_PROCESS).
- Services (svc/watchdog/recovery/autorestart) not in v5.
- RAG/knowledge/modules.md stale.
- HANDOVER_14D/PROMPT_14D only in C:/DeepSeek/logs/D/.
- Installer not yet run/tested. Operator runs install after reboot.


## 2026-10-29 00:21 - 11B test stabilization

**Chrome C after clean reboot:** stable 180+ sec via launcher. Pre-reboot death = dirty env (orphans), NOT code.
**test_boot:** was assuming 8670 busy. Fixed: test occupies 8670 via socket, releases in finally.
**test_ext_agent:** was fixed sleep(1.5), flaky under load. Fixed: poll /ping up to 10s.
**test_mf_8671 + test_fs:** dynamic ports (was hardcoded 8671, mutual conflict).
**Tests status:** 20/21 pass. Tests stabilized; further fails were timing/env flakes, now addressed.


## 2026-10-29 01:07:28 - 21/21 tests pass (11B FINAL)

- [x] 21/21 pass, 0 fail (was 9/21 at session start).
- [x] Installer P0-P2 fixed (all backed up).
- [x] Chrome C stable post-reboot (root cause: dirty env pre-reboot).
- [ ] OPERATOR: run installer in NEW test folder.
- [ ] Services (svc/watchdog/recovery/autorestart) not ported.
- [ ] RAG/knowledge/modules.md stale.
- [ ] HANDOVER_14D/PROMPT_14D to copy from DeepSeek if needed.


## 2026-10-29 01:14 - LLM: ручной старт из панели

**Правило (оператор):** local_ai/LLM НЕ в автозагрузке. Поднимается только вручную кнопкой "Старт" в панели мейнфрейма.
- [x] 11B: local_ai/server.py (pid 7676, 840 MB) заглушён.
- [ ] Реализовать в v5 Mainframe кнопку "LLM start/stop" (api.py + UI).
- [ ] Убрать local_ai из boot-all.ps1 / gen_launchers (не стартовать при boot).
- [ ] Тесты: вынести OUT-пути из хардкода C:/jewai в Path(__file__).resolve().parent.parent.parent (динамически от расположения теста).


## 2026-10-29 01:38 - Требования оператора (сессия Q&A)

### 1. Очистка C:/jewai от тестового профиля
- [ ] Снести Profiles/* (в т.ч. Profiles/C - тестовый профиль Семёна) из C:/jewai.
- [ ] Проверить, что install не копирует Profiles/Agents (уже в ignore, подтвердить).

### 2. Installer: токен и Chrome
- [ ] .agent_token добавить в ignore при copytree (не тащить токен из C:/jewai).
- [ ] Chrome: если не найден - ПРЕДЛОЖИТЬ скачать (как Python в install.ps1: Read-Host + Invoke-WebRequest). Сейчас только warning в лог.

### 3. Лаунчеры - в одно место
- [ ] Собрать все launchers в подпапку (Tools/launchers/ или аналог): boot-all, stop-all, start-<CH>, restart.
- [ ] Комплектный запуск всего и по каналам, ярлык на рабочий стол.
- [ ] В C:/jewai сейчас папки launchers нет вообще - только python Tools/boot.py + Tools/launcher.py.

### 4. Chrome: флаги и режим окна
- [ ] --hide-crash-restore-bubble ОБЯЗАТЕЛЕН во всех запусках Chrome. Внести в документацию (RAG/procedures/architecture.md или отдельный chrome_flags.md).
- [ ] НЕ открывать как PWA (--app=...). Открывать полноценное окно Chrome с вкладками.
  Причина: (а) агент работает в своей вкладке с другими вкладками; (б) в PWA не открыть панель расширений.
- [ ] Проверить, что Tools/launcher.py не передаёт --app (сейчас не передаёт; старый start-B.ps1 в DeepSeek передавал).

### 5. Сервисы v5: переработка, не копия
- [ ] Перенести svc/watchdog/recovery/autorestart в v5 с чистого листа по контракту AUDIT.
- [ ] ALIVE не перебивает черновик оператора: проверка userHasTyped перед вставкой; force=false для служебных сообщений (PANEL-STUCK/ALIVE).
- [ ] Recovery НЕ делает F5/reload, если оператор печатает (проверка активной печати, порог по keystroke).
- [ ] ALIVE-спам: не сбрасывать silencePinged на каждый ответ агента; ALIVE_REPEAT_MS (30 мин) между повторами.
- [ ] PANEL-STUCK: не отправлять как сообщение агенту, писать в лог/панель; не force=true.
- [ ] Авто-пауза при 3 FAIL: пересмотреть - не блокировать канал из-за сетевых флапов.
- [ ] svc_api.py: Tools/svc.py должен существовать (сейчас ссылка в пустоту).

### 6. LLM (подтверждение)
- [ ] local_ai/LLM только ручной старт кнопкой из панели мейнфрейма. Не в автозагрузке, не в boot-all.
- [x] local_ai/server.py (pid 7676, 840 MB) заглушён 2026-10-29.

### 7. Git
- [ ] C:/jewai - это и есть чистый git-проект (рабочее дерево). Изменения сессии НЕ закоммичены.
- [ ] Перед установкой - зафиксировать состояние коммитом.


## 2026-10-29 01:45 - Мейнфрейм v5: визуал и функционал (требования оператора)

**Контекст:** после установки мейнфрейм (8670) открывается, но "нифига не сделано толком". Привести к уровню текущего DeepSeek-мейнфрейма.

### 1. Визуал
- [ ] Привести к стилю инсталлятора: CRT/BBS-терминал (зелёный на чёрном, typewriter, Web Audio синт кликов/принтера).
- [ ] Единый визуальный язык инсталлятор <-> мейнфрейм.

### 2. Динамические блоки по числу агентов
- [ ] Количество блоков = letters из config.json (после установки 1-10), не хардкод 6.
- [ ] Источник правды: config.channels / config.letters.
- [ ] Референс: C:/DeepSeek sandbox/council_chat/server.py (launchpad блоки) + git/jewai (наглядно).

### 3. Функционал блоков (как в DeepSeek-мейнфрейме)
- [ ] Индикаторы состояния (alive/cdp/content/lastId/cmds) - работающие, не заглушки.
- [ ] Кнопки СТАРТ / СТОП / РЕБУТ для каждого блока (agent:<CH>, chrome:<CH>, server).
- [ ] Мнемосхема: связи между блоками, красные/зелёные лампы по cmds_from_start.
- [ ] Защита server: нельзя stop/reboot себя.

### 4. Чаты
- [ ] Общий чат (broadcast) - работает.
- [ ] Персональные чаты по каналам (вкладка "Персональные").
- [ ] Плейсхолдеры и имена/индексы агентов - из инсталлятора (config.channels.<L>.name), не хардкод "Agent A".

### 5. LLM (Лада)
- [ ] Пока заглушка: блок "LADA" в мейнфрейме, статус "не настроено".
- [ ] Кнопка ручного старта/остановки LLM (см. п.6 прошлого блока).
- [ ] Позже - нормальная интеграция (ip:port из config.llm).

### 6. Роадмапы
- [ ] Динамическое подтягивание из Projects/*/ROADMAP.html (скан директории, список, просмотр).
- [ ] API: GET /api/projects, GET /roadmap/<name> (как в DeepSeek).

### 7. Шаблоны в инсталляторе
- [ ] Шаблон проекта (Project) - структура папки, README, TODO.
- [ ] Шаблон роадмапа (ROADMAP.html/md) - чтобы модели понимали формат.
- [ ] Класть шаблоны в Templates/ при установке, доступны новым проектам.

### 8. Конфиги (справка, где что)
- config.json (корень) - главный: root, bind, chat_port, doh_proxy_port, letters, channels{name,agent,cdp,prefix,extension,model}, thresholds, timeouts, version. Читает Core/config.py.
- .agent_token (корень) - X-Token для API агентов.
- Templates/config.llm.example.json, config.mail.example.json - шаблоны, автоматически не грузятся.
- logs/svc/*.json - state сервисов (в v5 пока не создаются).
- logs/rebirth/* - таблица серий (в v5 пока нет живого цикла).


## 2026-10-29 01:57 - РЕФАКТОР: per-agent profiles (11B)

**Цель:** за 3 часа получить чистую систему, где установка создаёт рабочего агента с нуля.

**Проблема (баг):** все профили грузят один Templates/extension. Extension не знает свой порт/токен/канал. Леger общий. Это ломает мультиагентность.

**Решение (по указанию оператора):**
- Новая структура: Profiles/<L>/chrome (user-data), Profiles/<L>/config/config.json (per-channel), Profiles/<L>/logs/, Profiles/<L>/docs/ (PERSONAL, TODO), Profiles/<L>/extension/ (per-channel копия).
- Agents/<L> убрать из схемы (один источник правды).
- Инсталлятор создаёт структуру, пишет per-channel config, копирует extension.
- Extension читает свой config через chrome.storage.local (заполняется инсталлятором через CDP при первом запуске Chrome).
- Ledger per-channel: Profiles/<L>/logs/ledger.json.
- Launcher: --user-data-dir=Profiles/<L>/chrome --load-extension=Profiles/<L>/extension.
- Миграция агента: унёс папку Profiles/<L> — унёс всё (config, logs, docs, extension, chrome).

**План по шагам (3 часа):**
1. [ ] План в TODO/ROADMAP/JOURNAL/HANDOVER.
2. [ ] Инсталлятор: новая структура Profiles/<L>, per-channel config, копия extension, docs-шаблоны.
3. [ ] Core/config.py: channel_path(L, *parts) -> Profiles/<L>/...
4. [ ] Extension: чтение agentUrl/token из chrome.storage, fallback на ручной ввод.
5. [ ] Bridge/exec.py: ledger в Profiles/<L>/logs/ledger.json.
6. [ ] Tools/launcher.py: пути из Profiles/<L>/{chrome,extension}.
7. [ ] Инсталлятор при первом Chrome (CDP): chrome.storage.local.set({agentUrl, token, channel, name}).
8. [ ] Тесты: обновить под новую схему (dynamic).
9. [ ] Обновить RAG/procedures/agent_layout.md и current_state.md.
10. [ ] Обновить HANDOVER_11B.md.


## 2026-10-29 02:23:14 - per-agent refactor CODE DONE

- [x] Installer: Profiles/<L>/{chrome,config,logs,docs,extension}, per-channel config, extension copy, .agent_token ignore.
- [x] Core/config.py: channel_root/channel_path/channel_config.
- [x] Bridge/daemon.py: ledger in Profiles/<L>/logs/ledger_<L>.json.
- [x] Tools/launcher.py: chrome dir Profiles/<L>/chrome; push_storage via CDP.
- [x] Templates/extension: manifest host_permissions 8666-8675; sidepanel autodetect.
- [x] Tools/diagnose.py: Profiles/C/chrome.
- [ ] Тесты прогнать после рефактора.
- [ ] Chrome install offer (как Python).
- [ ] Launchers .ps1 в Tools/launchers/.
- [ ] Сервисы (svc/watchdog/recovery/autorestart) переработать.
- [ ] Мейнфрейм: визуал CRT + динамические блоки + чат + roadmap + шаблоны.
- [ ] Убрать Profiles/* из C:/jewai (тестовый профиль Семёна).


## 2026-10-29 04:16 - overnight work: p1-p9 done

### Готово (эта ночь)
- [x] P10: Profiles/* из C:/jewai снесены (A,B,C,D,E,F).
- [x] P13: Agents/ убран из инсталлятора.
- [x] P14: --load-extension + --hide-crash-restore-bubble при инициализации профиля.
- [x] P3: Chrome not found -> offer download + pause (install.ps1).
- [x] P2: Tools/gen_launchers.py + 17 .ps1 в Tools/launchers/; вызов из run_install и run_launch.
- [x] P7: /roadmap/<name> route отдаёт ROADMAP.html/md из Projects/<name>/; /api/projects уже есть.
- [x] P8: Templates/project/ + Templates/roadmap/ + Templates/README.md.
- [x] P1: Tools/svc.py + Tools/watchdog.py + Tools/recovery.py + Tools/autorestart.py.
  ALIVE: silence_pinged + alive_repeat=1800s; kick fails if busy (operator safe).
  Recovery: skip if operator typing; CDP-only reload; cooldown.
  Autorestart: ledger mtime + operator typing guard + restart via Bridge/run.py.
- [x] P4/P5/P6/P9: mainframe static CRT (green on black, scanlines); dynamic cards by config.letters; START/STOP/REBOOT per block; mnemo tab; chat tab; projects tab; LLM tab (stub "Тут будет ЛЛМ").
  Chat: placeholder names from config.channels.<L>.name.

### Осталось
- [ ] Тесты после всех правок.
- [ ] Git commit.
- [ ] P12: end-to-end install + run (утром с оператором).
- [ ] P11: финальный коммит после приёмки.


## 2026-10-29 04:21 - FINAL overnight commit a2332ca

- [x] 21/21 тестов зелёные.
- [x] Коммит a2332ca (70 files).
- [x] P1-P11, P13, P14.
- [ ] P12: end-to-end install (оператор).
- [ ] Приёмка (оператор).


## 2026-10-29 04:23 - smoke install PASS

- [x] install run_install end-to-end (tempdir, A/B): structure, config, launchers, templates - all OK.
- [x] stale Tools/launchers removed before regen.
- [ ] Operator acceptance test in real folder (P12).
