# TODO JewAI v5

**Версия:** 0.1.0-dev
**Старт:** 2026-10-28
**Ответственный:** оператор + 12D (Димон), пилот - канал C (Семён)
**Актуализирован:** 2026-11-10 (10C)

**Структура:** 2 раздела - **Установка (installer)** (всё, что про `install.bat`, `Tools/installer/server.py`, CfT, зависимости, копирование) и **Остальное** (всё про runtime, каналы, rebirth, addons, v6).

## Правила

- «Сделано» - только после проверки на диске (файл + размер + тест).
- Каждый модуль - по протоколу переноса (см. ROADMAP.md).
- Код старого проекта не копируется. Только переписывание.
- Отметка `[x]` ставится вместе с записью в JOURNAL.
- Каждый закрытый пункт отмечается `[x]` в этом же коммите, что и правка. Иначе история снова зарастёт.

## История

- Живой список - этот файл.
- История до 2026-11-02 (13D / 11B / 12B / install-баги 29-30.10 / релизная подготовка Алисы / 12B-13B UI) - в `logs/TODO_ARCHIVE_through_12B.md`.
- Что сделано 10C: `RAG/procedures/BUGS_V5.md` секции «Исправлено 10C» (BUG-001..018) + `logs/JOURNAL.md` (записи 2026-11-09/10).

---

# РАЗДЕЛ 1: УСТАНОВКА (installer)

Цель раздела: довести `install.bat` + `Tools/installer/server.py` до идеала. Одна команда на чистой машине: `git clone` → `install.bat` → работает.

## Installer: закрыто 10C

- [x] **BUG-008/009:** CfT обязателен. `Tools/get_cft.py` качает с googlechromelabs, распаковывает. Installer ищет в ROOT/target/config, если нет - автоскачивание. `raise` если после этого CfT не найден. CfT до init профилей. `chrome_path` в config. `PaaLadin/jewai-v5` 3f1f819.
- [x] **BUG-010:** проверка Python-зависимостей (`import websocket`) до копирования. Авто `pip install -r requirements.txt`. `raise` если pip не помог. `requirements.txt` создан. 5b1e8f7.
- [x] **BUG-017:** `emergency/` создан в source (36 файлов), installer копирует. `Rebirth/cycle.py::load_prompt` ищет в 4 местах. 7d02396.
- [x] **BUG-018:** `sandbox/rebirth.py::check_ready` (DeepSeek) - multi-path к PROMPT. Патч на DeepSeek. (Не в git v5, это DeepSeek-only.)
- [x] **BUG-011:** autodetect 8660..8720 + Mainframe fallback. 5b1e8f7.
- [x] **BUG-013:** .agent_token в root - agent.py walk-up находит. Не баг.

## Installer: к доделке 10C (аудит source)

- [ ] **Идемпотентность:** повторный запуск `install.bat` поверх существующей установки. Сейчас копирует без сноса, но старые Profiles/A/logs/ledger не трогает -> может быть mix from old and new. Продумать: (а) сохранять старые данные через .bak, (б) всегда clean Profiles/logs при --force, (в) проверять VERSION в config.
- [ ] **Валидация после install:** сейчас только check «Mainframe health OK» и «Agent A /ping OK». Добавить:
  - `Tools/get_cft.py --check` -> если fail, warn+raise.
  - Расширение грузится? CDP `/json/list` ищет `chrome-extension://` target - если нет, warn.
  - config.json: chrome_path, letters, channels[] заполнены корректно.
  - Все `requirements.txt` пакеты import-ятся.
  - `Profiles/A/logs/` создана.
- [ ] **source == target guard в installer**, не только в `install.bat`. Если `os.path.abspath(ROOT) == os.path.abspath(target)` -> ошибка в installer (сейчас warning).
- [ ] **Python отсутствует в PATH:** `install.ps1` предлагает скачать, но если откажут - сейчас продолжает. Проверить, что installer не стартует без Python (сейчас try/except).
- [ ] **pip отсутствует:** если `python -m pip` недоступен (Microsoft Store Python - ограничение), installer даёт понятную ошибку и exit-code != 0. Сейчас raise RuntimeError с текстом, но родительский процесс (install.ps1) может не показать его. Добавить `exit 2` в bat.
- [ ] **Chrome выбран не CfT:** launcher WARN (B-44) - оставить, но добавить в installer провepку: если chrome_path не CfT -> warn «системный Chrome 137+ не грузит unpacked ext» и НЕ ставить chrome_path, чтобы launcher сам искал CfT.
- [ ] **Копирование HANDOVER / SESSION_STATE:** сейчас в copytree берётся из source, но `HANDOVER_9C.md`, `SESSION_STATE.md` - персональные (не должны переезжать). Проверить ignore.
- [ ] **TEMP-артефакты:** `logs/runtime/`, `_lada_*`, `_cft_*` - не должны попадать в target. Проверить ignore (сейчас `logs` в ignore, `runtime` тоже).
- [ ] **Gen launchers:** `Tools/gen_launchers.py` использует `os.environ.JEWAI_CONFIG`. Проверить, что launcher-scripts правильно работают после install (сейчас создаются 8 bat).
- [ ] **Setup hostname/identity:** если запускается на новой машине (`HERETIC`, `Monolith`), installer пишет hostname в config для diagnostics. Сейчас нет.
- [ ] **Uninstall:** `uninstall.bat` - удаляет Profiles/, config, logs. Опционально.

## Installer: тесты

- [ ] **Smoke test в tempdir:** `Tools/installer/smoke_test.py` - ставит в `%TEMP%/jewai_test/`, проверяет 8 пунктов выше, удаляет. Запускается в CI (GitHub Actions).
- [ ] **Test загрузки CfT:** mock HTTP server -> get_cft.py качает, extract, проверяет chrome.exe.
- [ ] **Test deps check:** venv без websocket-client -> installer ставит, повторный check OK.

---

# РАЗДЕЛ 2: ОСТАЛЬНОЕ

## Статус на 2026-11-10 (10C)

P0 - все закрыты. Открыто: подтверждение rebirth fix на живом цикле (B или D).

Закрыто 10C (краткая сводка):

- [x] Rebirth double-send + зависание в textarea + ложный verify. `PaaLadin/jewai` c949386, `PaaLadin/jewai-v5` 1a5c2d1.
- [x] `no_last_id` (REBIRTH.md §11.8) - вариант (б). 06587a9.
- [x] BUG-007 (svc_api path mismatch). db19fc4.
- [x] BUG-003, BUG-005 - уже закрыты 9C. Убрано при ревизии.
- [x] BUG-001/002/004/006/010/011/012/013/014/015/017/018 - см. BUGS_V5.md.
- [x] PROMPT_10C, HANDOVER_9C, SESSION_STATE - созданы 9C.
- [x] ROADMAP подрезан 9C.
- [x] TODO архив: 173 -> 19, потом переписан. 38e0205.
- [x] Lada на HERETIC: llama.cpp b4720 не знает qwen3vl. Отложено (см. P3/v6).

## P0 - подтверждение (ждёт живого rebirth)

- [ ] **Подтверждение rebirth fix:** на ближайшем rebirth B или D смотреть `Tools/see_chat.py`. Ожидается ровно одно сообщение в чате, textarea пуста. Если снова два - откат по `.bak_10c_20261109`.

## P1 - важное

- [ ] **BUG-014/015 (HERETIC):** после утреннего `_10c_fix.bat` - проверить `Profiles/A/logs/ledger_A.json` и `Bridge A` живой. Смотреть `install.log` строки `10C CfT:`, `10C deps:`.
- [ ] **BUG-016 (DeepSeek v4):** `Bridge/daemon.py` в v5 уже с fix (не шлёт [AGENT REPORT] если все SKIP). В DeepSeek старый daemon без fix - там Борис в цикле stale: duplicate. Патч в DeepSeek: `Bridge/daemon.py::_tick` - `_has_real` проверка. Не в git v5 (DeepSeek-only).

## P2 - причёсывание

- [ ] **B-06:** Mainframe 8670 - переписать UI. MEDIUM. (Открыт: текущий CRT/8 табов рабочий, переписывание = дни.)
- [ ] **checkStuck живьём:** проверить авто-клик Continue/Retry в `content_deepseek.js` на живом залипании.

## P3 / v6 - внешнее

### Аддоны и расширения (см. RAG/procedures/ADDONS_CANDIDATES.md)

- [ ] **Голосовой цикл:** wake-word + STT + VAD + агент + TTS.
- [ ] **Рисование:** ComfyUI + Fooocus.
- [ ] **Память:** mem0.
- [ ] **OCR:** Tesseract.
- [ ] **Vision:** Moondream.
- [ ] **Локальная LLM:** Ollama (замена LocalAI в v6).
- [ ] **Автоматизация:** n8n (по необходимости).

### LLM на HERETIC (отдельный блок)

- [ ] **Lada на HERETIC:** llama.cpp не знает `qwen3vl` (GGUF Qwen-3-VL-8B). Варианты: (а) найти более новый llama.cpp с qwen3vl (сейчас 404 на win-zip), (б) взять Qwen2.5-VL или обычный Qwen2.5, (в) LM Studio GUI-режим (сейчас падает "daemon not running").

### Прочее

- [ ] **v6 - LLM в v5.** LocalAI (Qwen 3B :8090) не портирован.
- [ ] **STT + wake-word «Джошуа».** В долгий ящик.

## Ждёт решения оператора

- [ ] **Раскатка B-F:** каналы, живые агенты, приёмка. Организационное.
- [ ] **Борис (14B fake-rebirth):** _manual_rebirth_14B.py, series_table 14B/BBAB4000, last_id BBAB3990, в старом чате. Реальный rebirth 14B->15B при cmds=850 через чеклист (уже с фиксом BUG-018). Решение: оставить / откатить / гибрид.

## Правила 9C (наследие, действует)

1. `config.json` в `.gitignore`. SMTP-пароли только в `.secret/smtp.json`.
2. `op=write` перезаписывает целиком. Для append - `open(...,'a')` через `run`.
3. Литеральные `###` и бэктики в теле write - `chr(35)*3` / `chr(96)*3`.
4. Write race - read-back после каждого write.
5. `__pycache__` в extension ломает Chrome. `sys.dont_write_bytecode = True`.
6. Пуш: токен из `.secret/github_token`, inline URL, `GIT_TERMINAL_PROMPT=0`.
7. Rebirth: гейт 850. Не обходить. force только через `force_<CH>.flag`.
8. Многострочный `python -c` через мост - SyntaxError. Только файлом.

Dixi. 10C (Семён), 2026-11-10.
