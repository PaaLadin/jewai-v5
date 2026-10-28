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
