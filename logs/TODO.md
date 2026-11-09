# TODO JewAI v5

**Версия:** 0.1.0-dev
**Старт:** 2026-10-28
**Ответственный:** оператор + 12D (Димон), пилот - канал C (Семён)
**Актуализирован:** 2026-11-09, 10C (Семён)

## Правила

- «Сделано» - только после проверки на диске (файл + размер + тест).
- Каждый модуль - по протоколу переноса (см. ROADMAP.md).
- Код старого проекта не копируется. Только переписывание.
- Отметка `[x]` ставится вместе с записью в JOURNAL.
- Каждый закрытый пункт отмечается `[x]` в этом же коммите, что и правка. Иначе история снова зарастёт.

## История

- Живой список - этот файл.
- История до 2026-11-02 (13D / 11B / 12B / install-баги 29-30.10 / релизная подготовка Алисы / 12B-13B UI) - в `logs/TODO_ARCHIVE_through_12B.md`.
- Что было сделано 10C - секции ниже + `logs/JOURNAL.md` (записи 2026-11-09) + `RAG/procedures/BUGS_V5.md` (Исправлено 10C).

## Статус на 2026-11-09 (10C)

P0 в v5 - ПУСТ. Всё, что было, закрыто. Открыто только подтверждение rebirth fix на живом цикле.

Закрыто 10C (краткая сводка):

- [x] Rebirth double-send + зависание в textarea + ложный verify. `PaaLadin/jewai` c949386, `PaaLadin/jewai-v5` 1a5c2d1.
- [x] `no_last_id` (REBIRTH.md §11.8) - вариант (б), Monitor читает `ledger_<L>.json`. `PaaLadin/jewai-v5` 06587a9.
- [x] BUG-007 (svc_api path mismatch) - единый путь `Profiles/<L>/logs/svc_<kind>_<ch>.json`. `PaaLadin/jewai-v5` db19fc4.
- [x] BUG-003 - уже был закрыт в 9C (SYSTEM_MESSAGES.md §9), просто висел в BUGS_V5. Убрано при ревизии BUGS_V5.
- [x] BUG-005 (current_state.md устарел) - переписан 9C. Убрано при ревизии BUGS_V5.
- [x] PROMPT_10C.md создан 9C.
- [x] HANDOVER_9C.md создан 9C.
- [x] SESSION_STATE.md в jewai создан 9C.
- [x] ROADMAP подрезан 9C (5 дублей -> 2 секции).

## P0 - подтверждение (ждёт живого rebirth)

- [ ] **Подтверждение rebirth fix:** на ближайшем rebirth B или D смотреть `Tools/see_chat.py`. Ожидается ровно одно сообщение в чате, textarea пуста. Если снова два - откат по `.bak_10c_20261109`.

## P1 - важное

- [x] **BUG-002:** FIXED 2026-11-09 (10C). Реально баг был в `_operator_typing` (connect без host -> TypeError -> False). Теперь watchdog видит набор оператора. `_kick` уже был с host.
- [x] **BUG-006:** FIXED 2026-11-09 (10C). `Tools/export_share.py` на чистом CDP (без Playwright): изолированный context, scroll-loop, дедуп, NDA-redact, header. `test_export_share.py` 14/14. Живой тест на share - при следующем rebirth.
- [x] **BUG-004:** FIXED 2026-11-09 (10C). `RAG/procedures/ADAPTERS.md` создан (4880 б), INDEX обновлён.
- [x] **Handicap при отправке (Mora 04.11):** FIXED 2026-11-09 (10C). Базовая пауза была; добавлен `_note_send()` helper и вызовы в `_send_or_buffer`/`_drain_outbox`/`_drain_kick_buffer`. Теперь любой send_text продлевает handicap_ms (default 7000). test_daemon + test_daemon_timing зелёные.
- [x] **BEHAVIOR.md §9/§10 в jewai:** FIXED 2026-11-09 (10C). Перенесено из `C:/Jeho/RAG/procedures/BEHAVIOR.md` (2550 б). §9 дисциплина отправки, §10 не переиспользовать id. Файл 6652 б, секции 9-10 на месте.

## P2 - причёсывание

- [x] **B-07 / B-08:** B-07 уже был готов (`Templates/extension/onboarding.html` 4745 б, `agent.py` `GET /onboarding` + `/onboarding/status`, флаг «не показывать»). B-08 создан 10C: `RAG/onboarding/AGENT_FIRST_RUN.md` (3520 б) - Profiles/<L>/, линк-лист чатов, «не логинь Chromium в Google», порядок первого старта, связи.
- [ ] **B-06:** Mainframe 8670 - переписать UI как DeepSeek 8770, не Pip-Boy sidepanel. Масштабируемость по config.letters (1-10). MEDIUM. (Открыт: требует решения оператора - текущий UI CRT/8 табов рабочий, переписывание = дни.)
- [x] **B-09:** уже закрыт. `health.py::_auth_status` + `Mainframe/static/app.js` (auth-блок + LOGIN-кнопка при != logged_in). Проверено 10C read.
- [x] **B-10:** уже закрыт. `Bridge/run.py::_try_recreate_chat` (Target.createTarget), B-48 guard не открывает до onboarding ack. Проверено 10C.
- [x] **B-11:** уже закрыт. `Rebirth/cycle.py` пишет `logs/active_chat_<L>.json`. Проверено 10C.
- [x] **B-30:** уже закрыт. `app.js load()` вызывает `loadPauseState()`, читает `/pause_state`, пишет в `chrome.storage.local.set({paused})`. Проверено 10C read.
- [x] **B-12:** уже закрыт. Wiki-таб + `/wiki` + 18 файлов в `Mainframe/`. Проверено 10C.
- [ ] **checkStuck живьём:** проверить авто-клик Continue/Retry в `content_deepseek.js` на живом залипании.
- [ ] **TEST OUT paths:** вынести OUT-пути из хардкода `C:/jewai` в `Path(__file__).resolve().parent.parent.parent` (динамически от расположения теста).

## P3 / v6 - внешнее

- [ ] **v6 - LLM в v5.** LocalAI (Qwen 3B :8090) в v5 не портирован. Оператор: план на v6.
- [ ] **STT + wake-word «Джошуа».** В долгий ящик. На Хабре кто-то выкладывал, изучить.

## Ждёт решения оператора

- [x] **BUG3a (Bridge/DeepSeek redirect chat -> www).** FIXED 2026-11-09 (10C) вариантом (в): `find_chat` fallback только при ровно одном page-табе с host. `test_cdp_find_chat.py` 5/5.
- [ ] **Раскатка B-F:** каналы, живые агенты, приёмка. Организационное, за оператором.

## Правила 9C (наследие, действует)

1. `config.json` в `.gitignore`. SMTP-пароли только в `.secret/smtp.json`.
2. `op=write` перезаписывает целиком. Для append - `open(...,'a')` через `run`.
3. Литеральные `###` и бэктики в теле write - `chr(35)*3` / `chr(96)*3`.
4. Write race - read-back после каждого write.
5. `__pycache__` в extension ломает Chrome. `sys.dont_write_bytecode = True`.
6. Пуш: токен из `.secret/github_token`, inline URL, `GIT_TERMINAL_PROMPT=0`.
7. Rebirth: гейт 850. Не обходить. force только через `force_<CH>.flag`.
8. Многострочный `python -c` через мост - SyntaxError. Только файлом.

Dixi. 10C (Семён), 2026-11-09.

