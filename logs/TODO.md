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

## P1.5 - installer gaps (обнаружено при раскатке на HERETIC)

- [x] **BUG-017:** PROMPT не находится из emergency/. emergency/ создан в source, load_prompt расширен, installer копирует. FIXED 2026-11-10 (10C).
- [ ] **installer: не копирует emergency/, HANDOVER, TEMP-артефакты.** Проверить, что все важные корневые папки копируются. Частично закрыто BUG-017.
## P2 - причёсывание

- [x] **B-07 / B-08:** B-07 уже был готов (`Templates/extension/onboarding.html` 4745 б, `agent.py` `GET /onboarding` + `/onboarding/status`, флаг «не показывать»). B-08 создан 10C: `RAG/onboarding/AGENT_FIRST_RUN.md` (3520 б) - Profiles/<L>/, линк-лист чатов, «не логинь Chromium в Google», порядок первого старта, связи.
- [ ] **B-06:** Mainframe 8670 - переписать UI как DeepSeek 8770, не Pip-Boy sidepanel. Масштабируемость по config.letters (1-10). MEDIUM. (Открыт: требует решения оператора - текущий UI CRT/8 табов рабочий, переписывание = дни.)
- [x] **B-09:** уже закрыт. `health.py::_auth_status` + `Mainframe/static/app.js` (auth-блок + LOGIN-кнопка при != logged_in). Проверено 10C read.
- [x] **B-10:** уже закрыт. `Bridge/run.py::_try_recreate_chat` (Target.createTarget), B-48 guard не открывает до onboarding ack. Проверено 10C.
- [x] **B-11:** уже закрыт. `Rebirth/cycle.py` пишет `logs/active_chat_<L>.json`. Проверено 10C.
- [x] **B-30:** уже закрыт. `app.js load()` вызывает `loadPauseState()`, читает `/pause_state`, пишет в `chrome.storage.local.set({paused})`. Проверено 10C read.
- [x] **B-12:** уже закрыт. Wiki-таб + `/wiki` + 18 файлов в `Mainframe/`. Проверено 10C.
- [ ] **checkStuck живьём:** проверить авто-клик Continue/Retry в `content_deepseek.js` на живом залипании.
- [x] **TEST OUT paths:** FIXED 2026-11-09 (10C). 21 тест-файл переведён на `ROOT = Path(__file__).resolve().parent.parent.parent`. Тесты вскрыли старый баг `test_imports` (ждал 6 каналов A-F, реально 4 A-D) - тоже исправлен. 25/25 наборов зелёные.

## P3 / v6 - внешнее

### Установка (installer)

- [x] **BUG-008/009:** installer авто-скачивает CfT (`Tools/get_cft.py`), требует его до init профилей. Без CfT Chrome 137+ не грузит расширение. FIXED 2026-11-10 (10C).
### Аддоны и расширения (по RAG/procedures/ADDONS_CANDIDATES.md)

- [ ] **Голосовой цикл:** wake-word (Porcupine/openWakeWord) -> STT (faster-whisper) -> VAD (Silero) -> агент -> TTS (Piper).
- [ ] **Рисование:** ComfyUI (API) + Fooocus (простой режим).
- [ ] **Память:** mem0 (запоминание между сессиями).
- [ ] **OCR:** Tesseract (быстро, бесплатно).
- [ ] **Vision:** Moondream (лёгкая VLM).
- [ ] **Локальная LLM:** Ollama (замена LocalAI в v6).
- [ ] **Автоматизация:** n8n (по необходимости).

### Прочее


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


## 2026-11-10 ночь (10C) - HERETIC: найденные баги при установке

Установка на HERETIC (`\\HERETIC\JewAI_v5`), оператор ушёл спать. Собрано полным аудитом.

- [x] **BUG-010 (P0):** на HERETIC нет `websocket-client` -> launcher push_storage FAILED, Bridge A не стартует, активатор не постится. Fix 10C: `requirements.txt` + проверка в installer до copy + авто-pip install.
- [x] **BUG-011 (P1):** FIXED 2026-11-10 (10C): autodetect 8660..8720 + Mainframe fallback + save to storage при 1 агенте.
- [x] **BUG-012 (P2):** НЕ баг. Кнопки настоящие (inline script дёргает /api/boot, /api/stop, /api/restart). Не работали из-за мёртвого Bridge A (BUG-010).
- [x] **BUG-013 (P0):** НЕ баг. agent.py::_find_token_file walk-up находит root .agent_token (install-wide). Per-channel не нужен.
- [ ] **BUG-014 (P0):** Bridge A не работает (следствие BUG-010). Проверить утром после _10c_fix.bat.
- [ ] **BUG-015 (P0):** Проверить утром после _10c_fix.bat: должен появиться Profiles/A/logs/ledger_A.json.

Установщик на HERETIC: дважды запускался (двойной install.log), CfT скачался с 3-й попытки (~200 MB за 9 сек). CfT OK, extension OK, chrome_path OK.

План:
1. Исправить BUG-010 (уже в source, надо синхронизировать на HERETIC и проверить).
2. Исправить BUG-013 (проверить, где agent.py ищет токен).
3. Исправить BUG-011 (autodetect).
4. Проверить BUG-012 (mnemo live).
5. Синхронизировать все фиксы на HERETIC через SMB.
6. Коммит + push.
