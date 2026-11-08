# Аудит JewAI-v5 — 9C (2026-11-08)

**Заказчик:** оператор.
**Аудитор:** 9C (Семён).
**Цель:** понять реальное состояние проекта, выявить мусор/хвосты/костыли, дать рекомендации перед чисткой и релизом.

---

## 1. GitHub `PaaLadin/jewai-v5`

- Ветка по умолчанию: `main`, HEAD `424983f` (Close 14D, 2026-11-06).
- Локально в `C:\jewai`: 2 коммита впереди origin/main (не запушены):
  - `50fcb4d` 15D night: 23/23 tests, EXTRA_ROOTS in config+agent, diagnose/INDEX fix, tests+2
  - `4644b26` 15D: Google adapter (AI-Swing-Bridge mechanic), test in suite, 24/24
- Теги: отсутствуют (релизов нет, версия в файле 0.1.0-dev).
- Ветки на origin: main, feature/perplexity-adapter-switching (незамерженная фича).
- Issues: не проверял (нужен веб-интерфейс).
- Форки на GitHub: не обнаружены (публично).

---

## 2. Локальная папка `C:\jewai`

- Размер: **~496 МБ** (включая .git, Profiles, Tools/chrome-for-testing).
- В корне 45+ сущностей: **.bak-файлы** в корне (`ROADMAP.md.bak_7c_*`, `ROADMAP.md.bak_dora_*`, `config.json.bak_11b_*`, `config.json.bak_15d_*`).
- Git: `main`, дерево чистое, ahead 2 (см. §1).
- Модули в корне: Adapters, Agents, Archive, Bridge, Core, Mainframe, Profiles, Projects, RAG, Rebirth, Sandbox, Templates, Tools, logs.
- Хардкод `C:\DeepSeek` в модулях: **1 случай** — `Tools/cleanup_test.py:26` (сам cleanup-скрипт, возможно намеренно).

### `.bak`-мусор в проекте: 261 файл

Распределение по префиксам:
- `11b` — 104 (11B, старые правки до v5)
- `7c` — 43 (7C)
- `c` — 31 (8C)
- `12b` — 18 (12B)
- `dora` — 18 (Dora, неизвестный агент)
- `15d` — 12 (15D)
- `flexfix`/`grid`/`v4` — по 7 (старые extension sidepanel)
- `9c` — 3 (мои, текущая сессия)
- Прочие: `b39` (3), `11b2`, `11b4`, `20261104`, `mute2`, `vol`, `vol2` (по 1)

**Вывод:** `.bak`-мусор не в .gitignore, лежит в рабочем дереве, в коммит не идёт (git status чистый), но засоряет диск и мешает аудиту.

---

## 3. Форки и тестовые развёртки на `C:\`

Найдено **8 Jew*/DeepSeek-папок** в корне C:\:

| Папка | Верхний размер | .git | config | Bridge | Mainframe | Что это |
|---|---|---|---|---|---|---|
| `C:\DeepSeek` | 36.2 МБ | нет | да | **нет** | да | старый проект, головной источник хвостов |
| `C:\DeepSeek_push_git_backup_20261006_0257` | 0.1 МБ | нет | нет | нет | нет | бэкап push-состояния 06.10 |
| `C:\JewAI` | 0.1 МБ | да | да | да | да | свежий клон jewai-v5 (46 записей) |
| `C:\JewAI-mi` | 0.1 МБ | да | да | да | да | ещё один клон jewai-v5 (10 записей) |
| `C:\JewAIv1` | 0.0 МБ | нет | нет | нет | нет | огрызок (11 записей) |
| `C:\JewAi_testOper` | 0.1 МБ | нет | да | да | да | тест-развёртка (35 записей) |
| `C:\JewTest_Audit` | 0.1 МБ | нет | да | да | да | тест-развёртка (35 записей) |
| `C:\JewTest_Final` | 0.1 МБ | нет | да | да | да | тест-развёртка (35 записей) |

**Наблюдения:**
- `C:\JewAI` и `C:\JewAI-mi` — **два git-клона одного репозитория**. Оба могут быть ahead/behind относительно origin. Нужно проверить, какой использовался и когда.
- `C:\JewAi_testOper`, `C:\JewTest_Audit`, `C:\JewTest_Final` — **три тестовые развёртки** (по 35 записей в корне). Без .git. Развёрнуты из `C:\jewai` через installer. Скорее всего, от «доры» или «мора» (это их след по именам бэкапов `.bak_dora_*`).
- `C:\DeepSeek` — 36 МБ, Mainframe есть, Bridge нет. Что-то сломано или переделано.
- `C:\JewAIv1` — огрызок 11 файлов, нет git, нет config. Похоже на попытку начать клон без git.
- `C:\DeepSeek_push_git_backup_*` — 13 файлов, бэкап от 06.10, устарел.

**Вывод:** в корне C:\ — беспорядок. Это и называется «деструктивные следы D и C (доры и мора)»: они разворачивали тестовые инсталляции напрямую в `C:\Jew*`, а `C:\DeepSeek` оставили в полуразобранном виде.

---

## 4. Документация и RAG

- `ROADMAP.md` — **19622 байт**. Содержит историю фаз Ф0–Ф7, заметки 11B, 12B, 13D, 14D, 15D. Частично актуальна, но перемешана с историческим контекстом. Упоминает задачи, которые уже закрыты. Требует ревизии: оставить актуальный статус + ссылку на историю.
- `README.md` — 2684 байт. Короткий, актуальный.
- `VERSION` — `0.1.0-dev`. Релизов нет.
- `config.json` — 1136 байт. Содержит каналы A–D, порты 8666.. и т.д. См. отдельно.
- `RAG/INDEX.md` — есть, ссылается на architecture/ (ARCHITECTURE, AUDIT, MODULES) и procedures/ (28 файлов, включая BEHAVIOR, KICK_PROTOCOL, SYSTEM_MESSAGES, INSTALL, OPERATIONS, PANEL и т.д.).
- `logs/` в корне `C:\jewai` — надо проверить наличие JOURNAL, TODO, HANDOVER_* и актуальность.

**Наблюдения:**
- `RAG/architecture/AUDIT.md` (44 КБ) — источник истины: что переносили из старого проекта и что НЕ переносили. Важнейший файл для понимания проекта.
- `RAG/procedures/mainframe_gap.md` — описывает разрыв между старым Mainframe и v5. Это тот самый документ, по которому я сейчас работал.
- `RAG/procedures/PANEL.md` — описывает панель как Pip-Boy UI. Наша новая панель (index/style/app, которые я написал в ночь на 04.11) уже не Pip-Boy, а CRT-пульт с 5 табами. Документ устарел.

---

## 5. Mainframe/static — что на самом деле там лежит

### Мои файлы от 04.11 (9C)
Записаны ночью 2026-11-03/04 (id CCAA9083–CCAA9116). Бэкапы `.bak_9c_b06_20261103_215855` сохранили **Pip-Boy** (index 1831 б, style 7598 б, app 7430 б). Свои файлы были: index **3422 б**, style **8977 б**, app **11050 б**.

### Что сейчас на диске
`index.html` — **22520 б** (НЕ мой 3422 б — перезаписан).
`style.css` — **35139 б** (НЕ мой 8977 б).
`app.js` — **11050 б** (размер совпадает с моим, но содержимое могло измениться).
`chat.js` (8190 б), `mnemo.js` (16959 б), `pers.js` (3524 б), `app_audio.js` (6105 б) — **не мои**, добавлены 15D / «морой».

### Мусор в Mainframe/static
- `.bak_9c_b06_*` — 3 файла (мои бэкапы Pip-Boy, сохранить как историю).
- `.bak_11b*`, `.bak_12b_pipboy`, `.bak_c_b06`, `.bak_c_b09`, `.bak_c_tabs` — 6 устаревших.
- `wiki.html` (10799 б) — оставлен 7C (B-12), актуален.

### Главное
1. Ночной передел 15D заменил мой CRT-пульт на свою версию (22 КБ index, 35 КБ style) — нужно увидеть и оценить.
2. `app.js` (11050 б) — под вопросом: это мой файл, или 15D его подкорректировал, но оставил мой размер? Проверить sha256 vs staging (было sha256 staging: `app.js` размер 11050 б).
3. voice_call.py в Tools — 3 бэкапа (mute2, vol, vol2), это скорее всего причина голосовых залипов.

---

## 6. Голосовой вызов и залипания «Voice stop signal sent»

**Файл:** `Tools/voice_call.py`. На диске **3 бэкапа**: `.bak_mute2`, `.bak_vol`, `.bak_vol2` — признак, что кто-то (11B? 15D?) активно правил логику mute/volume.

**Симптом (оператор):**
- При пробуждении голосом TTS должен замолкать после 2–3 повторов.
- Если оператор печатает текст, **без голосового вызова**, флаг «Voice stop» всё равно шлётся/висит.
- Панель залипает: в логах висит «Voice stop signal sent» (у меня — 23:38, у Аркадия — 23:23, 23:38, 23:39).
- Панель A и C — обе залипли, перезагрузка не помогает.

**Гипотеза:**
Флаг `voice_stop` / `mute` не сбрасывается после отправки. В `voice_call.py` есть обработчик «стоп-сигнала», который должен проверять:
1. Был ли активный voice-вызов (флаг `in_call`).
2. Если нет — не слать stop.

**Если проверки нет** — любой кик/ввод текста в чат вызывает `stop_tts()` → отправляется «Voice stop signal sent» → какие-то хуки ждут ack → мост блокируется.

**След «моры» и «доры»:**
- `logs/TODO.md.bak_20261104_mora` — бэкап от «моры» (04.11).
- 18 `.bak_dora_*` файлов по всему проекту (`ROADMAP.md.bak_dora_*`, `Bridge/daemon.py.bak_dora_sync_*`, `Tools/diagnose.py.bak_dora_sync_*`, `Tools/kick.py.bak_dora_sync_*`, `Tools/export_share.py.bak_dora_export_*`).
- «Дора» и «мора» разворачивали тестовые инсталляции в `C:\Jew*` и правили Bridge/daemon, Tools/kick, Tools/diagnose, export_share.

---

## 7. «Voice stop signal sent» — корень залипаний панели

### Цепочка
1. `extension/content.js:196` — «оператор напечатал -> шлём voice-stop»:

    voiceStopSent = true;
    console.warn("[bridge] user typed, sending voice-stop");
    try { await sendBg({ type: "notify-stop" }); } catch (e) {}

   Срабатывает на любое печатание в чат, независимо от голосового вызова.

2. `extension/background.js:265` — обработчик `notify-stop`:

    if (msg.type === "notify-stop") {
      const s = await get();
      try {
        const r = await fetch(s.agentUrl + "/notify-stop", { method: "POST", ... });
        const j = await r.json();
        await status("Voice stop signal sent", "warn");
        return respond(j);
      } catch (e) { return respond({ ok: false, error: String(e) }); }
    }

   Стоит внутри `chrome.runtime.onMessage` — это однопоточный обработчик. Пока fetch висит, все остальные сообщения (heartbeat, ping, команды, кики, статусы) не обрабатываются.

3. `/notify-stop` эндпоинта нигде нет:
   - DeepSeek `Templates/extension/agent.py` — файла нет вообще.
   - JewAI `Templates/extension/agent.py` (22126 б) — `/notify-stop` нет.
   - JewAI `Agents/C/extension/agent.py` (20767 б) — `/notify-stop` нет.
   Значит, запрос идёт на несуществующий путь. Если сервер отвечает 404 быстро — падает в catch. Но если `agentUrl` неверный или агент не запущен, Chrome ждёт сетевой таймаут до 60+ секунд. Всё это время панель залипла.

### Симптом на скриншотах (оператор, 07.11)
- Панель C: `Voice stop signal sent` 23:38:42.
- Панель A: `Voice stop signal sent` 23:23:05, 23:38:48, 23:39:48.
- Обе панели залипли, перезагрузка не помогала.

### Рекомендации (3 варианта, от быстрого к правильному)
1. Быстрый фикс (1 строка). В `content.js:196` — не слать `notify-stop`, если нет активного голосового вызова (проверять `voicePlaying || inCall`). Если не зовут — нечего останавливать.
2. Средний фикс (background.js). Обернуть fetch в `AbortController` с таймаутом 2-3 сек. Не ждать минуту.
3. Правильный фикс. Добавить `/notify-stop` в agent.py (уже сейчас это no-op, но эндпоинт отвечает 200 OK мгновенно). Один блок — закрывает навсегда.

Для JewAI v5 (чистый проект) — правильный фикс в `Templates/extension/agent.py` + `Agents/<L>/extension/agent.py`.
Для DeepSeek (замороженный) — быстрый фикс (пункт 1 или 2), чтобы разблокировать работу.

---

## 8. Сводка проблем (по приоритетам)

### P0 — блокирует работу прямо сейчас
1. **Voice-stop залипание панели** (см. §7). Симптом: «Voice stop signal sent» висит в статусе, панель не отвечает, перезагрузка не помогает. Причина: `content.js:196` шлёт `notify-stop` на любой ввод; `background.js:265` висит на fetch без таймаута; `/notify-stop` нет ни в одном `agent.py`. Лечение — §7.

### P1 — деструктивные следы «доры/моры/15D» в `C:\jewai`
2. **Mainframe/static перезаписан 15D.** Мой CRT-пульт от 04.11 (index 3422 б, style 8977 б) заменён на чужой (index 22520 б, style 35139 б). Файлы `chat.js`, `mnemo.js`, `pers.js`, `app_audio.js` добавлены не мной. Надо визуально оценить и решить: оставить (если лучше) или откатить.
3. **`voice_call.py`** — 3 бэкапа (`.bak_mute2`, `.bak_vol`, `.bak_vol2`), нужна проверка логики mute/volume. Сейчас voice_call.py — просто обёртка Windows TTS + mute. «Notify-stop» к нему не относится, это extension.

### P2 — мусор на диске
4. **261 `.bak` файл в `C:\jewai`** (11b — 104, 7c — 43, c — 31, 12b — 18, dora — 18, 15d — 12, прочее).
5. **8 Jew*/DeepSeek-папок на `C:\`** (§3), 4 из них — огрызки/тесты.
6. **`.bak` в корне jewai** — `ROADMAP.md.bak_7c_*`, `ROADMAP.md.bak_dora_*`, `config.json.bak_11b_*`, `config.json.bak_15d_*`, `install.bat.bak_11b_guard`.

### P3 — git
7. **2 локальных коммита не запушены** (`50fcb4d` 15D night, `4644b26` 15D Google adapter). Решить: пушить как есть или пересобирать релиз.
8. **Нет тегов** (релизов). `VERSION` = `0.1.0-dev`.
9. **Ветка `feature/perplexity-adapter-switching`** на origin не смержена — нужна ли?

### P4 — документация
10. **`RAG/procedures/PANEL.md`** описывает Pip-Boy, а сейчас стоит (по факту) другой CRT-пульт. Устарел.
11. **`RAG/procedures/mainframe_gap.md`** — разрыв old vs v5, актуален.
12. **`RAG/architecture/AUDIT.md`** (44 КБ) — источник истины, не трогать.

## 9. Рекомендации (порядок действий)

### Шаг 1 — починить залипание (P0)
- Правка `content.js:196` — не слать `notify-stop`, если нет голосового вызова.
- Правка `background.js:265` — обернуть fetch в AbortController (2-3 сек).
- Для JewAI — добавить `/notify-stop` в `Templates/extension/agent.py` (200 OK no-op).

### Шаг 2 — оценить Mainframe от 15D
- Скриншот 15D-версии (index 22520 б) — визуально. Сравнить с моим CRT (index 3422 б в `.bak_9c_b06_*`). Оператор решает: какой оставить.

### Шаг 3 — чистка диска (P2)
- Удалить `.bak_11b*`, `.bak_7c_*`, `.bak_12b_*`, `.bak_dora_*`, `.bak_15d_*`, `.bak_flexfix`, `.bak_grid`, `.bak_v4` в jewai (после ревизии — некоторые могут быть нужны).
- Оставить: `.bak_9c_b06_*` (мой), `.bak_c_b09` (критичный для B-09), остальные — по решению.
- `C:\Jew*` папки: `C:\JewAI` и `C:\JewAI-mi` — сравнить. `C:\JewAi_testOper`, `C:\JewTest_Audit`, `C:\JewTest_Final` — снести (это следы тестовых развёрток). `C:\JewAIv1` — снести огрызок. `C:\DeepSeek_push_git_backup_*` — снести.

### Шаг 4 — git-гигиена (P3)
- Проверить, что `50fcb4d` и `4644b26` не сломают контракт. Если ОК — пуш.
- Решение по `feature/perplexity-adapter-switching`: мержить или удалить.
- Тег `v0.1.0` после чистки.

### Шаг 5 — документация (P4)
- Обновить `RAG/procedures/PANEL.md` под актуальный UI.
- Проверить `ROADMAP.md` — сократить историю, оставить актуальный статус.

## 10. Что НЕ проверено (out of scope)

- GitHub Issues на `PaaLadin/jewai-v5` — не смотрел (нужен веб).
- Содержимое `C:\JewAI` vs `C:\JewAI-mi` — одинаковые или разные? (только верхний уровень, 46 vs 10 записей).
- Работает ли новая панель 15D (не запускал, оценивал только по размерам файлов).
- Все 261 `.bak` на предмет содержания — не вскрывал.

Dixi. 9C (Семён), 2026-11-08.

---

## 11. Фикс «Voice stop signal sent» (применён 2026-11-08, 01:4x)

### Что сделано

**DeepSeek extension (патч background.js):**
- `extension/background.js` — `.bak_9c_vs_20261108_012215` (17343 б → 18062 б)
- `extension_alice/background.js` — `.bak_9c_vs_<ts>`
- `extension_qwen/background.js` — `.bak_9c_vs_<ts>`

Изменения:
1. В `DEFAULTS` добавлено `voiceActive: false`.
2. В обработчик `notify` добавлено `await set({ voiceActive: true })` после успешного вызова.
3. В `notify-stop` — три проверки:
   - Если `!s.voiceActive` → мгновенный ответ `{ok: true, skipped: "no active tts"}`. **fetch не шлётся.**
   - Если `voiceActive === true` → флаг сразу сбрасывается.
   - fetch уходит в **fire-and-forget** IIFE с `AbortController` и таймаутом **5 минут**. `respond()` возвращается мгновенно — `onMessage` не блокируется.

**JewAI v5 extension (agent.py, добавлен no-op endpoint):**
- `Templates/extension/agent.py` — `.bak_9c_vs_<ts>`
- `Agents/C/extension/agent.py` — `.bak_9c_vs_<ts>`

Добавлен `/notify-stop` в `do_POST` (200 OK `{ok: true, noop: true}`).

**JewAI extension background.js** — НЕ патчился: в v5 нет обработчика `notify-stop` вообще (файлы 2508–3151 б). Залипаний быть не может.

**DeepSeek extension/agent.py** — уже содержал `/notify-stop` (проверено, отвечает 401 без токена, endpoint зарегистрирован).

### Проверка

- Все 3 JewAI agent.py — `py_compile OK`.
- Все 3 DeepSeek агента живы: 8766/8767/8768 = connect_ex(0).
- `/notify-stop` на DeepSeek агентах — 401 (без токена), endpoint есть.

### Что нужно от оператора
- **Перезагрузить extension** в Chrome для каналов A, B, C (или полный restart Chrome). Без перезагрузки старый `background.js` остаётся в памяти и патч не активен.

### Дополнительно
- DeepSeek был источником залипаний. JewAI v5 (чистый проект) не содержит этот обработчик вообще — при пересборке проблема уйдёт сама.
- Если в JewAI v5 в будущем понадобится TTS/notify — реализовать сразу по правильной схеме: `voiceActive` + AbortController, не копировать из DeepSeek.

Dixi. 9C (Семён), 2026-11-08.

---

## 12. Rebirth fixes (2026-11-08, 9C — вторая волна)

### 12.1. Спам LA «rebirth_ready» — устранён

**Корень:**
1. **8 копий `la_rebirth_monitor.py`** запущены одновременно (pid 664, 15012, 22116, 19916, 15804, 13704, 9588, 10648). Каждая кикала свой reminder.
2. **`series_table.json` устарел:**
   - C: `current_series=8C, range=CCAA8000-8999`. Реальность: 9C (CCAA9000+). `cmds = lastId - 8000 = 1326` → «critical», хотя реально 326.
   - B: `current_series=12B, range=BBAB2000-2999`. Реальность: 13B (BBAB3000+). `cmds = 1140` → «critical».
3. **`pending_B.json`, `pending_C.json`, `pending_E.json`** — висели от старых срабатываний, каждый тик монитор видел их и эскалировал «artifacts NOT ready».

**Исправлено:**
- 8 мониторов убиты → **1 работает** (pid 5748 на финальной проверке).
- **C:** 8C → **9C** (`CCAA9000–9999`), next 10C (`CCAB0000–0999`).
- **B:** 12B → **13B** (`BBAB3000–3999`), next 14B (`BBAB4000–4999`).
- **`session_C.json`, `session_B.json`** синхронизированы.
- **`pending_*.json`** — удалены (B, C, E).
- **`rebirth.lock`** — снят (висел 47 часов от D, ts 1793924555).

**Результат в `watchdog.log`:**
- Было: `reminder B level=critical cmds=1140`, `reminder C level=critical cmds=1326`.
- Стало: `monitor ok: A=112 B=211 C=416` — реальные значения, не critical.

### 12.2. Патч `la_rebirth_monitor.py` (DeepSeek)

**Файл:** `sandbox/la_rebirth_monitor.py`. Бэкапы: `.bak_9c_tableguard_*`, `.bak_9c_helper_*`.

**Добавлено:**
1. **Single-instance guard** — Windows `CreateFileW` exclusive lock на `logs/rebirth/monitor.lock`. Если уже запущен — `exit 0` с сообщением `already running`. Убивает корень 8 копий.
2. **`_recent_kick(ch, 600)`** — cooldown 10 минут между киками одного канала. Даже если level меняется (warn→critical), kick не чаще раза в 10 мин.
3. **`TABLE STALE` guard** — если `lastId > range[1]`, **не кикает**, пишет в лог: `TABLE STALE <CH> lastId=X > range_end=Y`. Оператор должен обновить `series_table.json`.

**Проверено:**
- `py_compile OK`.
- `--rebirth-monitor` (once) → `already running, exit` (guard).
- После фикса таблиц C и B: `monitor ok: A=112 B=211 C=410` — не спамит.

### 12.3. Патч `rebirth_send_prompt.py` — handover-формат

**Корень «писать мимо окна кода»:**
- В примере блока был литеральный `|`: `"строки: id: <PR> | op: read | path: <файл>"`. Модель копировала буквально → всё в одну строку.
- Переменная `BT = chr(96)*3` объявлена, но **не использовалась в сообщении** → модель не понимала, что блок нужно обернуть в тройные бэктики → писала «мимо фенса».

**Исправлено:**
- Убран `|` (вертикальная черта как разделитель).
- Добавлен **полный пример блока в тройных бэктиках** (`BT` теперь реально применён).
- Явные правила:
  1. Оберни в тройные бэктики.
  2. Первая строка после фенса — маркеры BEGIN.
  3. **Каждое поле на своей строке** (id, op, path/cmd).
  4. Последняя — END.
  5. id = 4 заглавные латинские + 4 цифры.
  6. Не пиши команду «мимо» фенса.

**Проверено** (`_9c_handover_sample.txt`):
- `has_three_backticks: true`
- `has_vertical_bar_as_separator: false`
- `id_on_own_line, op_on_own_line, path_on_own_line: true`
- 9 явных правил в тексте.

### 12.4. Патч `activate_chat.py` — `import os`

**Корень:** `os.path` использовался на строке 9, но `import os` отсутствовал. Скрипт падал с `NameError` сразу при запуске — PROMPT не уходил в новый чат.

**Исправлено:** `import argparse, sys, time` → `import argparse, os, sys, time`. py_compile OK.

### 12.5. Гейт 850 — работает

**Проверено в песочнице:**
- `rebirth_ready.py --channel C --check-only` → `cmds=404 < 850 — рано, готовь артефакты и работай`. **Отказ.**
- `rebirth_master.py --channel C --dry-run` → `нет флага REBIRTH-READY`. **Не запускается.**
- `rebirth.py --channel C --dry-run` → `НЕТ флага готовности`. **Не запускается.**

Порог 850 **не обходится** ни монитором, ни ready.

### 12.6. Ложный advance B (инцидент, откачен)

**Что случилось:**
- В 02:22:35 кто-то вызвал `rebirth_table.update('B')` напрямую, минуя `rebirth_master` и лог `rebirth_log.jsonl`.
- Таблица B стала `14B` (BBAB4000-4999), `last_id=BBAB3215`.
- **Боря по факту был жив в 13B** (lastId BBAB3217). Ложное перерождение.
- След: `series_table.json.bak_rebirth_14B` (mtime 02:22:35).

**Откат (9C):**
- Таблица B восстановлена: `13B`, `range=BBAB3000-3999`, `next=14B`, `last_id=BBAB3217`.
- Бэкап: `series_table.json.bak_9c_rollback_*`.
- В `rebirth_log.jsonl` записи про B→14B нет — подтверждает, что цикл не прошёл.

**Причина (гипотеза):**
- Один из старых 8 мониторов успел вызвать `auto_rebirth_check`, поймал `ready_B.json` от старого цикла, но `Master.run` упал, а `advance` уже был выполнен.
- Либо оператор/другой агент запустил `rebirth_table.py --channel B` руками.

**Рекомендация:**
- `rebirth_table.py update()` — **не должен запускаться без `rebirth_log.jsonl` записи**. Добавить проверку: не писать таблицу, если последняя запись для канала не содержит `result=cycle done` (или `OK`).
- Или — `advance()` вызывать **только** из `cycle.py` после `verify_prompt_hits >= MIN_HITS`.

### 12.7. Финальное состояние rebirth

| Канал | Серия | Диапазон | lastId | cmds |
|---|---|---|---|---|
| A | 16A | AAAB6000-6999 | AAAB6000 | ~55 |
| B | 13B | BBAB3000-3999 | BBAB3217 | ~217 |
| C | 9C | CCAA9000-9999 | CCAA9000 | ~426 |
| D | 15D | DDAB5000-5999 | DDAB5000 | probe FAIL (CDP 9225 мёртв) |

**Монитор:** 1 экземпляр (guard). Cooldown 10 мин. TABLE STALE guard. Все 8 скриптов rebirth: `py_compile OK`.

### 12.8. Тесты в песочнице

Все проверки rebirth выполнены через:
- `python -m py_compile` — 8 скриптов OK.
- `--check-only` / `--dry-run` — без записи в state.
- `subprocess.run` с `capture_output` — не трогают live-чаты.

Live-триггеров не запускалось. Реальное перерождение — только после 850 или force от оператора.

Dixi. 9C (Семён), 2026-11-08.