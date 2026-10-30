# TODO JewAI v5

Правила:
- «Сделано» — только после проверки на диске (файл + размер + тест).
- Каждый модуль — по протоколу переноса (ROADMAP.md).
- Код старого проекта не копируется. Только переписывание.
- Отметка `[x]` ставится вместе с записью в JOURNAL.

## Ф0. Скелет

- [ ] Структура C:/JewAI/ (RAG, Sandbox, Profiles, Tools, Projects, Mainframe, Archive, .secret, logs)
- [ ] VERSION
- [ ] README.md
- [ ] ROADMAP.md

## Ф1. Аудит

- [ ] AUDIT.md

## Ф2. Пилот моста

- [ ] Core/config.py
- [ ] Bridge/cdp.py
- [ ] Bridge/read.py
- [ ] Bridge/exec.py
- [ ] Bridge/daemon.py
- [ ] Adapters
- [ ] Tools/launcher.py

## Ф3. Mainframe

- [ ] server.py + static

## Ф4. Rebirth

- [ ] table.py, master.py, onboard.py

## Ф5. Надстройки

- [ ] llm/mail/rag каркасы

## Ф6. Раскатка

- [ ] A, B, D, E, F по одному

## Ф7. GitHub

- [ ] push в PaaLadin/jewai-v5