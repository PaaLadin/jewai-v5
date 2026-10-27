# TODO JewAI v5

**Версия:** 0.1.0-dev
**Старт:** 2026-10-28
**Ответственный:** оператор + 12D (Димон), пилот — C (Семён)

## Правила

- «Сделано» — только после проверки на диске (файл + размер + тест).
- Каждый модуль — по протоколу переноса (см. ROADMAP.md и JOURNAL.md).
- Код старого проекта не копируется. Только переписывание.

## Ф0. Скелет (в плане)

- [ ] Структура C:/JewAI/ — готова (осталась)
- [ ] VERSION 0.1.0-dev — готов
- [ ] README.md — готов
- [ ] ROADMAP.md — откачен к чистому плану
- [ ] logs/JOURNAL.md — откачен, с инструкцией переноса
- [ ] logs/TODO.md — этот файл
- [ ] RAG/architecture/OVERVIEW.md — заглушка
- [ ] RAG/procedures/rebirth_v5.md — заглушка
- [ ] RAG/procedures/cdp_transport_v5.md — заглушка
- [ ] RAG/INDEX.md — есть

## Ф1. Аудит старого (в плане)

Цель: по каждому модулю старого проекта выписать контракт и костыли. Не код, а знание.

- [ ] Bridge: cdp_client.py -> контракт + костыли
- [ ] Bridge: bridge_kick2/3.py -> контракт + костыли
- [ ] Bridge: read_panel_state2.py -> контракт + костыли
- [ ] Rebirth: rebirth_*.py (9 файлов) -> контракты + костыли
- [ ] Mainframe: council_chat/server.py -> контракт роутов, что нужно, что мусор
- [ ] Services: svc.py, watchdog.py, recovery_loop.py, autorestart.py -> контракты
- [ ] Extension: content*.js, background*.js, agent.py -> что делает, нужно ли в v5
- [ ] Launchers: start-*.ps1, boot-all.ps1 -> контракт запуска
- [ ] Tools: find.py, see_chat.py, say.py, doh_proxy.py -> контракты
- [ ] Результат: RAG/architecture/AUDIT.md (контракты, не код)

## Ф2. Пилот моста на C (в плане)

- [ ] Профиль Chrome C (копия в C:/JewAI/Profiles/C)
- [ ] Core/config.py — порты, каналы (с нуля)
- [ ] Bridge/cdp.py — нативный CDP (с нуля)
- [ ] Bridge/read.py — чтение чата (с нуля)
- [ ] Bridge/exec.py — парсер блоков + read/write/run (с нуля)
- [ ] Bridge/daemon.py — цикл (с нуля)
- [ ] Adapters/deepseek.py — create_chat, send_prompt, verify (с нуля)
- [ ] Tools/launcher.py — запуск Chrome (с нуля)
- [ ] E2E тест: агент C читает файл, отчёт возвращается

## Ф3. Mainframe 8670 (в плане)

- [ ] server.py — HTTP-сервер, 7 роутов (с нуля)
- [ ] api.py — status, projects, chat_url, boot/stop/restart (с нуля)
- [ ] static/index.html — панель (с нуля)
- [ ] llm.py — сетевая LLM (с нуля, заглушка до ip:port)

## Ф4. Rebirth v5 (в плане)

- [ ] table.py — серии (с нуля)
- [ ] master.py — create->send->verify->update->onboard (с нуля)
- [ ] onboard.py — приветствие (с нуля)
- [ ] Тест: rebirth C при cmds >= 850

## Ф5. Надстройки (в плане)

- [ ] Почта SMTP (когда оператор решит провайдера)
- [ ] RAG-канал для Алисы (после GitHub)
- [ ] Mainframe к сетевой LLM (ip:port от оператора)

## Ф6. Раскатка (в плане)

- [ ] A, B, D, E, F по одному
- [ ] Старый JewAI -> Archive после приёмки

## Ф7. GitHub (в плане)

- [ ] git init C:/JewAI
- [ ] push в PaaLadin/jewai-v5

Dixi. 12D, 2026-10-28.