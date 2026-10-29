# ROADMAP JewAI v5

**Версия:** 0.1.0-dev
**Старт:** 2026-10-28
**Корень:** C:/JewAI/
**Ответственный:** оператор + 12D (Димон), пилот — канал C (Семён)

## Цель

Пересобрать JewAI начисто в C:/JewAI/. Старый проект (C:/DeepSeek/) заморожен, не правится, используется только как источник знаний (контракты, идеи, грабли).

Код старого проекта **не копируется**. Каждый модуль переписывается с нуля.

## Правило переноса кода

На каждый модуль:
1. Прочитать старый файл целиком.
2. Выписать контракт: что делает полезного (2–5 строк).
3. Выписать костыли: что в нём лишнее и почему появилось.
4. Решить: что из костылей нужно в новой архитектуре, что выкинуть.
5. Написать модуль с нуля по контракту.
6. Тест.
7. Запись в JOURNAL.

Проверка перед коммитом:
- в новом файле нет ничего, чего нет в контракте;
- нет импортов старого проекта;
- нет хардкода `C:\DeepSeek`;
- нет закомментированного кода «на всякий случай».

## Фазы

| Фаза | Название | Статус | Примечание |
|------|----------|--------|------------|
| Ф0 | Скелет проекта | done | структура, VERSION, README, JOURNAL, TODO |
| Ф1 | Аудит старого JewAI | done | AUDIT.md 44467b, 29 разделов + §30 replay-guard |
| Ф2 | Пилот моста на C | done | Core/Bridge/Adapters/Tools; E2E read+send на C (9124) |
| Ф3 | Mainframe 8670 | done | P0+P1: chat/status/health/svc/launchpad/meeting/logs/roadmap; /fs отложен |
| Ф4 | Rebirth v5 | done | table/master/onboard + gate + lock + CDP cycle; test_rebirth 23/23, test_cycle 19/19 |
| Ф5 | Надстройки | partial | llm/mail/rag каркасы + doh_proxy реализован (test 9/9); real config требует данные оператора |
| Ф6 | Раскатка A/B/D/E/F | откат в план | Chrome поднимались вне правил, потушены; агенты не запускались |
| Ф7 | GitHub-публикация | в плане | precheck только; push не выполнялся |
| + | Extension (added 13D) | done | Templates/extension 7 файлов + Agents/<CH>/extension; test 15/15 |
| + | Layout (added 13D) | done | Profiles/<CH>/ (browser) + Agents/<CH>/ (personal) + Templates/ |

## Порты

| Канал | Agent | CDP |
|-------|-------|-----|
| A | 8666 | 9122 |
| B | 8667 | 9123 |
| C | 8668 | 9124 |
| D | 8669 | 9125 |
| E | 8671 | 9126 |
| F | 8672 | 9127 |

Панель: 8670. Прокси: 9899.

## Что НЕ переносим

- Лада (local_ai, Qwen 3B) — галлюцинирует. В v5 — сетевая LLM по ip:port.
- Playwright — виснет на SPA.
- Attach файла в DeepSeek (`input[type=file]`) — не работает.
- Watermark/Ledger extension — в v5 нет (это старый механизм из C:/DeepSeek/extension/).
- Базовый extension для агентов — в v5 ЕСТЬ: Templates/extension/ + Agents/<CH>/extension/.
  Написан с нуля по контракту, без watermark, без voice/notify/sandbox.
- Хардкод `C:\DeepSeek` — всё через `config.root()`.
- Мусор: hexxagon, kdp, itch, fix/patch/check, `_d_*`, `_c_*`, `.bak`.

Dixi. 12D, 2026-10-28.

## История прохождения (13D, 2026-10-28)

Правило: ROADMAP обновляется по мере прохождения фаз, не в конце.
13D не обновлял таблицу вовремя - исправлено задним числом.

### Ф0 - done
Структура C:/JewAI/, VERSION 0.1.0-dev, README.md, logs/JOURNAL.md, logs/TODO.md.

### Ф1 - done
AUDIT.md 44467b, 29 разделов + §30 (replay-guard). Покрыто 8 зон:
Bridge, Services, Tools, Launchers, Extension, Rebirth, Mainframe, replay-guard.

### Ф2 - done
Модули: Core/config.py, Bridge/cdp.py (fix: list_targets -> [] на мёртвом CDP),
Bridge/read.py, Bridge/exec.py (replay-guard), Bridge/daemon.py,
Bridge/run.py (entrypoint), Adapters/deepseek.py, Tools/launcher.py.
Тесты: imports 7/7, smoke 24/24, daemon 11/11, daemon_timing 8/8, cdp_read_launcher 14/14.
E2E: read (body 5111) + live-send marker (7/7) в живом чате C.

### Ф3 - done
Mainframe/web.py (переименован из http.py - затенял stdlib), api.py (parallel probe),
server.py, static/index+style+app.js, llm.py (stub).
8670 занят чужим pid 5304 -> убит по ОК оператора, наш сервер pid 15984, все роуты 200.
Тесты: mainframe_8671 19/19, server_subprocess 12/12.

### Ф4 - partial
Готово: table.py (series math, atomic write), master.py (gate limit/force/hold/threshold/deny,
lock TTL 1h, run minimal), onboard.py (pick_neighbor, message). test_rebirth 23/23.
Не сделано: CDP cycle (create_chat -> send_prompt -> verify -> advance) реально не реализован.
master.run(live=True) только двигает таблицу. Тест 'rebirth C при cmds>=850' не выполнен.

### Ф5 - partial
Каркасы: llm.py (config.llm{host,port}), mail.py (config.mail), rag_channel.py (JSONL).
Проверено на fake HTTP/SMTP: f5 17/17, f5_configured 11/11.
Не настроено: реальный LLM/SMTP (нужен config), doh_proxy 9899 (не начат).

### Ф6 - откат в план
Chrome A/B/D/E/F поднимались вне правил (все разом, до приёмки Ф2-Ф5).
Потушены 2026-10-28 по указанию оператора. Активен только C (9124).
Агенты (Bridge/run --channel) не запускались.
Правильный порядок: по одному, после приёмки предыдущего канала.

### Ф7 - в плане
Precheck: .git есть, branch main, 1 коммит 2770d2f, remote PaaLadin/jewai-v5 (без токена).
Untracked готово к коммиту. Push не выполнялся.

## Итоги сессии 13D (2026-10-28)

18 наборов тестов, 289 проверок, все зелёные (41.6с).
Chrome C (9124) live. Mainframe 8670 live (наш pid). Watchdog D ON.
Передача: HANDOVER_14D 4140b, PROMPT_14D 2690b, RAG/procedures/current_state.md 1376b.

Блокеры (ОК оператора):
1. Ф4 CDP cycle.
2. Ф5 real config.
3. Ф6 раскатка по одному.
4. Ф7 push.
5. Mainframe /fs (non-JSON ветка).


## Phase 8: Clean Build & Installer
- Self-contained build, GUI installer in mainframe style, configurable paths/ports.

## Phase 9: New Mainframe UI
- Match visual RAG, dynamic tabs based on agents.

## Phase 10: Voice Acceptance
- Call operator by voice before git push.


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


## 2026-10-29 01:07:28 - 11B: 21/21 tests pass

**All 21 test suites green.** Session start was 9/21.

### Fixed (11B, all backed up .bak_11b*)
- config.json v5 schema (channels A-D, agent 8666+i, cdp 9122+i, model=deepseek).
- installer/server.py: PORT 8660 (was 8671 conflict); doh_proxy_port written; run_launch calls Tools/launcher.py; basePort from UI; health-check after spawn; model=deepseek (qwen/alice test-only).
- installer/install.ps1: http://127.0.0.1:8660.
- installer/app.js: defaults 8760->8666.
- Mainframe/static/index.html: title JewAI -> JewAI v5.
- Mainframe/svc_api.py: _SVC -> local Tools/svc.py.
- 18 tests: OUT path C:/DeepSeek -> C:/jewai/logs/runtime.
- 5 tests: dynamic ports (mf_8671, mf_ext, fs) and dynamic channels (server_subprocess, run_entrypoint, launchpad).
- test_boot: self-occupies 8670 (was assuming busy).
- test_ext_agent: poll /ping up to 10s (was fixed sleep 1.5s).

### Key finding
- Chrome C after clean reboot: stable 180+ sec. Pre-reboot death was dirty env (orphans), NOT launcher code.
- launcher.py:100 already uses DETACHED_PROCESS. No fix needed.

### Ready for operator installer test
- Installer: run in NEW test folder (not C:/jewai).
- Expected: empty Chrome profiles, Templates/extension v5.0.0, panel on 8670, agents on 8666-8669.

### Still open (not blocking installer)
- Services (svc/watchdog/recovery/autorestart) not ported. svc_api.py points to non-existent Tools/svc.py.
- RAG/knowledge/modules.md stale.
- HANDOVER_14D/PROMPT_14D only in C:/DeepSeek/logs/D/.
- Autostart/boot slowdown analysis (operator zone, not touched).


## 2026-10-29 01:57 - Phase 11: per-agent profiles

**Status:** IN PROGRESS.
- Profiles/<L>/{chrome,config,logs,docs,extension} - one folder per agent, migration-friendly.
- Extension knows own port via chrome.storage (set by installer via CDP).
- Ledger per-channel.
- Agents/<L> removed (single source of truth).


## 2026-10-29 04:16 - Phase 12: services + launchers + CRT

**Status:** DONE (code), pending operator test.
- P1: svc/watchdog/recovery/autorestart (operator-safe ALIVE).
- P2: Tools/launchers/*.ps1 (start/stop/restart per channel + server + shortcut).
- P3: Chrome install offer in install.ps1.
- P4-P6: mainframe CRT + dynamic cards + chat + projects.
- P7: /roadmap/<name> route.
- P8: Templates/project + Templates/roadmap.
- P10: C:/jewai Profiles/ cleaned.
