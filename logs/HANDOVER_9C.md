# HANDOVER 9C -> 10C (JewAI v5)

**От:** 9C (Семён), CCAA9000-9999, lastId CCAA9734.
**Кому:** 10C, CCAB0000-CCAB0999.
**Дата:** 2026-11-09, ночь.
**Проект:** JewAI v5. DeepSeek — frozen, но живёт (live backup в git).

## Что сделано 9C

### 1. TTS notify + stop (портировано из DeepSeek)

**Новые файлы в v5:**
- `Tools/notify_me.py` (~7 КБ): TTS через PowerShell SAPI + SSML. Repeat, interval. Lock (O_EXCL + PID + 120с stale). Stop-file `runtime/notify.stop`. Activity backoff.
- `Templates/extension/agent.py`: `/notify` (запускает notify_me.py detached, `-B` флаг), `/notify-stop` (создаёт `runtime/notify.stop`).
- `Templates/extension/background.js`: handlers `notify` и `notify-stop`. Fire-and-forget с AbortController 5 мин. onMessage НЕ блокируется.
- `Templates/extension/content_deepseek.js`: `_voiceStopCheck` (1с interval). Фильтр: текст с `[` в начале НЕ считается «оператор печатает» (это кики, [AGENT REPORT], [SYS]).
- Синхронизировано в `Agents/C/extension/`.

**Тест:** гимн 3x30сек, оператор напечатал после 1-го -> TTS замолк. **ТЕСТ ПРИНЯТ.**

**DeepSeek-фиксы:**
- `content.js`: fire-and-forget (не блокирует onMessage).
- `background.js`: путь `runtime/notify.stop` (было `ROOT/notify.stop`, не совпадало).
- `agent.py`: то же.
- Все 4 extension: `sys.dont_write_bytecode = True` в agent.py (иначе `__pycache__` ломает Chrome).

### 2. Rebirth (DeepSeek — фикс, v5 — порт)

**DeepSeek:**
- Single-instance guard (8 копий -> 1).
- Cooldown 10 мин между kick.
- TABLE STALE guard (lastId > range_end -> не кикать, лог).
- `rebirth_send_prompt.py`: убран `|` из примера, добавлен полный пример в бэктиках.
- `activate_chat.py`: `import os` (NameError).
- `series_table.json`: C 8C->9C, B 12B->13B (были ложные kick).
- Ложный advance B (14B->13B) откачен.

**v5:**
- `Tools/rebirth_monitor.py`: патч (single-guard, cooldown, TABLE STALE).
- `Rebirth/cycle.py`: приклеивает `Templates/PROMPT_ACTIVATION.md` к body.
- `Templates/PROMPT_ACTIVATION.md`: правила формата блоков.
- `Templates/config.example.json`, `logs/rebirth/series_table.json` (A=1A, B=1B, C=1C, D=1D).
- RAG/REBIRTH.md §11: 8 подпунктов.

### 3. Mainframe — wiki таб

8-я вкладка «СПРАВКА» (iframe /wiki). 4 новые секции в wiki: Голос, Шестерёнка адаптеров, SMTP, Адаптеры моделей.

### 4. Doc audit (§18)

**Исправлено 7 расхождений:**
- `KICK_PROTOCOL.md`: `bridge_kick2/3` -> `Tools/kick.py` + `POST /api/send` (12 неверных упоминаний).
- `agent_layout.md`: «Extension ABSENT» -> реально есть `Agents/<L>/extension`.
- `PANEL.md`: Pip-Boy -> 15D.
- `SYSTEM_MESSAGES.md`: добавлен §9 формат `[AGENT REPORT]`.
- `current_state.md`: переписан.
- `RAG/INDEX`: SMTP.md, BUGS_V5.md, AUDIT_GAP.md + порядок чтения.
- `RAG/procedures/BUGS_V5.md` (новый): 7 багов.

### 5. SMTP — критическая находка

**`config.json` был в git!** Если бы туда попал SMTP-пароль — утёк бы в публичный jewai-v5.

Сделано:
- `git rm --cached config.json`.
- `.gitignore` += `config.json`, `config.json.bak_*`, `.secret/**`.
- `Mainframe/mail.py`: читает `.secret/smtp.json`, fallback `config.mail` legacy.
- `Templates/.secret/smtp.example.json` (пример).
- `RAG/procedures/SMTP.md` (для оператора + агентов).
- Раздел в wiki.

### 6. Шестерёнка адаптеров

- `Mainframe/settings.py`: `get_all`, `set_adapter`. Адаптеры: deepseek/qwen/alice/google.
- API: `GET /api/settings`, `POST /api/settings {"channel":"A","model":"qwen"}`.
- UI: кнопка ⚙ в topbar, модалка со списком каналов.

### 7. Аудит JewAI v5

- `C:\jewai\AUDIT_9C.md` (12 секций, 21 КБ).

## Что открыто для 10C

### P0 — блокирует

1. **Живой тест rebirth в v5.** Гейт 850 работает. CDP cycle не прогонялся на живом.
2. **BUG-007:** `svc_api.py` path mismatch (панель показывает watchdog=false при живом).

### P1 — важное

3. **BUG-002:** `watchdog.py::_kick` без `HOST`.
4. **BUG-006:** `export_share` через CDP (не Playwright).
5. **BUG-004:** `Adapters/google.py` не описан.

### P2 — причёсывание

6. **ROADMAP.md** (14 КБ) — 5 дублей «Status after 14D».
7. **SESSION_STATE.md** в jewai — нет.
8. **PROMPT_10C.md** — создать.

## Git (origin/main `PaaLadin/jewai-v5`)

- `4c9c651` — wiki sections + RAG index + bugs
- `90a9cae` — settings gear
- `793dd7a` — doc audit + wiki tab + SMTP
- `ec5d514` — TTS notify + stop
- `ba147fc` — rebirth port v5 + audit

**DeepSeek `PaaLadin/jewai`:** `8b6ab17` (live backup extension).

## Грабли 9C

1. `config.json` в git — утечка секретов. Проверять `git ls-files` перед паролем.
2. `op=write` перезаписывает целиком. AUDIT_9C был обрезан до 1 секции.
3. Литеральные `###` / бэктики в теле write рвут блок. `chr(35)*3` / `chr(96)*3`.
4. Write race — read-back после каждого write.
5. Многострочный `python -c` — SyntaxError. Файлом.
6. `__pycache__` в extension ломает Chrome (`_` префикс).

## Что делать 10C

1. Прочитать: RAG/INDEX (порядок 10 пунктов), BEHAVIOR, KICK_PROTOCOL, SYSTEM_MESSAGES, HANDOVER_15D, этот файл.
2. Спросить оператора: (а) живой тест rebirth v5, (б) BUG-007 (панель), (в) ROADMAP подрезать.
3. Доложить: `[10C] on-line, прочитал N, роль принял, lastId CCAB0000+`.

Dixi. 9C (Семён), 2026-11-09.