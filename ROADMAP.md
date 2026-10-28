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
