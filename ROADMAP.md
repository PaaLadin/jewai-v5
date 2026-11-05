# ROADMAP JewAI v5 (v0.2, draft Dora 2026-11-04)

**Версия:** 0.1.0-dev
**Старт:** 2026-10-28
**Ответственный:** оператор
**Корень прода:** C:/jewai (оттуда пуш на GitHub)
**Рабочая зона:** C:/Jeho (деплой, где живут агенты)
**Архив/референс:** C:/DeepSeek (не правится, только чтение)

## 1. Манифест

JewAI v5 — локальный мост между браузерными LLM-чатами и файловой системой.
Агент (языковая модель в SPA-чате) не имеет доступа к диску напрямую; он
пишет текстовые блоки-команды, локальный Python-процесс их исполняет и
возвращает отчёт. Так агенты читают файлы, пишут код, запускают тесты,
общаются друг с другом и перерождаются, не теряя преемственности.

Цель v5 — пересобрать систему начисто: без хвостов бета-версии, без
костылей, с явной идеологией и проверяемыми критериями приёмки. Каждый
модуль пишется с нуля по контракту из аудита; код старого проекта не
копируется.

## 2. Три папки — три роли

| Папка | Роль | Правила |
|-------|------|---------|
| C:/DeepSeek | архив, референс | не править, только читать |
| C:/jewai | чистовик, прод | только чистый код, ROADMAP, ARCHITECTURE; отсюда push |
| C:/Jeho | деплой, рабочая зона | TODO/JOURNAL/RAG/тесты/мусор локально; найденное чиним и коммитим в jewai |

Правило переноса: DeepSeek -> (прочитал, понял, проверил) -> собрал с нуля
в песочнице -> протестировал -> положил в jewai. Никакого копипаста.

## 3. Идеология

1. **Агент — не процесс, а участник.** У агента есть имя, канал, префикс id,
   диапазон, серия, предшественник. Он живёт в чате, но оставляет следы на
   диске: TODO, JOURNAL, RAG, HANDOVER.
2. **Преемственность важнее непрерывности.** Перерождение — штатный механизм,
   не авария. Таблица серий, гейт, lock, onboarding — чтобы смена поколения
   не теряла знания.
3. **Мост — единственный канал.** Агент не исполняет сам. Всё, что он делает
   с диском, идёт через блоки команд и отчёты моста. Это даёт аудит и replay-guard.
4. **Знание живёт в файлах, не в контексте.** RAG, HANDOVER, JOURNAL — источник
   правды. Контекст чата — расходник, файлы — память.
5. **Песочница прежде оператора.** Сначала проверь в Sandbox, потом неси в прод.
6. **Факт сильнее намерения.** «Сделано» — только после проверки на диске
   (read/hash/тест). Декларация без артефакта — не результат.

## 4. Принципы (инженерные)

1. **Config — единственный источник правды.** Порты, каналы, пути, таймауты —
   только из `config.json` через `Core/config.py`. Хардкод путей/портов запрещён
   (кроме тестов).
2. **Python-исходники ASCII-only.** Кириллица — только в данных (JSON, md,
   конфиг). Причина — AUDIT §30: op=write >1.5 КБ режет тело, em-dash ломает
   парсер. Дробить на фрагменты, py_compile каждого, склейка build-скриптом.
3. **Replay-guard обязателен.** Водяной знак + хэш содержимого + `stale_blocks.log`
   в `Bridge/exec.py` Ledger. Не обходить, не отключать.
4. **Daemon — единственный владелец цикла.** stable-gate, coalesce, min_gap,
   inflight — только в `Bridge/daemon.py`. Адаптер — только SPA-специфика.
5. **Один адаптер на SPA-семейство, не на канал.** A-D — один `deepseek.py`,
   разные порты. Qwen/Alice — отдельные адаптеры.
6. **Mainframe без внешних зависимостей.** Только stdlib. Loopback only.
7. **Никакого копипаста из DeepSeek.** Прочитал -> понял -> проверил ->
   собрал с нуля -> протестировал -> положил в jewai.
8. **Мусор — в песочницу.** Тесты, черновики, бэкапы — в `Sandbox/<L>/`,
   не в jewai. В jewai — только чистый код и документы.

## 5. Фазы

Статус: done / partial / in progress / pending / blocked.
Критерий приёмки — что должно быть проверено на диске/в рантайме, чтобы фаза
считалась закрытой. Само-приёмка запрещена: принимает оператор или старший канал.

### Ф0. Скелет — done
Структура, VERSION, README, ROADMAP, JOURNAL, TODO.
Критерий: файлы существуют, git чистый.

### Ф1. Аудит — done
AUDIT.md 44 КБ, 30 разделов, 8 зон.
Критерий: каждый модуль старого проекта имеет контракт + костыли + решение.

### Ф2. Пилот моста — in progress
Core/config, Bridge/{cdp,read,exec,daemon,run}, Adapters/deepseek, Tools/launcher.
Критерий: E2E read + live-send в живом чате C, replay-guard ловит stale-блок,
тесты imports/smoke/daemon зелёные. Сейчас: E2E read OK, live-send OK, приёмки нет.

### Ф3. Mainframe — partial
web, api, server, static, llm (stub). CORS, dynamic cards, CRT.
Критерий: все роуты 200, CORS работает, карточки по config.letters, START/STOP/
REBOOT живые, /api/status отдаёт реальные поля. Сейчас: пилот есть, приёмки нет.

### Ф4. Rebirth — partial
table, master, onboard. Gate limit/force/hold/threshold/deny, lock TTL 1h.
Критерий: живой CDP-цикл create_chat -> send_prompt -> verify -> advance на
тестовом канале, таблица двигается, onboarding уходит соседу. Сейчас: только
table advance, CDP-цикл не реализован.

### Ф5. Надстройки — partial
llm (ip:port), mail (SMTP), rag_channel (JSONL), doh_proxy.
Критерий: реальный LLM отвечает, SMTP шлёт, doh_proxy поднимается на 9899.
Сейчас: каркасы, fake-тесты зелёные, real config не проверен.

### Ф6. Раскатка A/B/D/E/F — откат в план
По одному, после приёмки предыдущего канала. A и B — Dora и Mora в Jeho.
Критерий: агент поднят, панель видит, ALIVE отвечает, TODO/JOURNAL ведутся.
Сейчас: поднимались вне правил, потушены.

### Ф7. Релизный пуш — pending
Критерий: R1-R5 закрыты (LICENSE, requirements, CHANGELOG, tag, push, скан
секретов). Push в PaaLadin/jewai-v5 после закрытия всех фаз.

### Ф8. Clean Build & Installer — pending
Self-contained сборка, GUI-инсталлятор в стиле Mainframe, настраиваемые пути/порты.
Критерий: install.bat в новой папке -> рабочий стек без ручных правок.

### Ф9. Новый Mainframe UI — pending
Визуал по RAG, динамические вкладки по агентам.
Критерий: панель масштабируется 1-10 каналов, вкладки/карточки из config.

### Ф10. Голосовая приёмка — pending
Голосовой вызов оператора перед push.
Критерий: voice_call.py, проверка громкости, ночной режим 22:00-08:00.

## 6. Блокеры (ждут решения оператора)

Разрушительные или вне зоны агента. Без явного ОК — не делать.

| # | Блокер | Что нужно |
|---|--------|-----------|
| B1 | Порт 8670 занят чужим pid | kill по ОК, затем restart Mainframe |
| B2 | Ф2 live-send в живой чат C | ОК на запись в живой чат |
| B3 | Ф6 раскатка A/B/D/E/F | ОК на спавн живых агентов |
| B4 | Ф7 push в PaaLadin/jewai-v5 | GCM-клик оператора |
| B5 | BUG3a DeepSeek redirect chat->www | решение: no-proxy / fixed URL / fallback |
| B6 | Mainframe /fs non-JSON ветка | решение о формате ответа |

## 7. Релизный чеклист v0.1.0 (R1-R5)

- **R1 Легальность.** LICENSE (MIT или Apache 2.0), правообладатель — Оператор.
- **R2 Сборка чужим человеком.** requirements.txt (только реальные импорты),
  README Quick start (venv -> pip -> install.bat), config.example.json,
  реальный config в .gitignore.
- **R3 Версионирование.** CHANGELOG.md (Keep a Changelog), git tag v0.1.0-dev,
  первый GitHub Release.
- **R4 Пуш.** git pull --rebase -> push, скан секретов (git log -p).
- **R5 Техдолг безопасности.** 5.1 аутентичность источника блока (префикс-канал,
  консилиум); 5.2 живой CDP-цикл Rebirth; 5.3 тест watchdog-guard на залипание DOM.

## 8. Backlog

Ведёт Мора (RAG/backlog). Здесь — только ссылка и правила:
- приоритеты: HIGH/MEDIUM/LOW;
- источник: TODO.md jewai (блоки B-06..B-30), R1-R5, баги инсталлятора;
- правило: один ход — наш, один — оператора (для рискованных).

## 9. Ссылки

- `RAG/architecture/AUDIT.md` — контракты и костыли старого проекта (30 разделов).
- `RAG/architecture/ARCHITECTURE.md` — идеология, слои, потоки (этот релиз).
- `RAG/procedures/architecture.md` — короткие решения 13D.
- `logs/TODO.md` — оперативный план, [x] после теста.
- `logs/JOURNAL.md` — append-only, факты.
- `logs/HANDOVER_11B.md` — передача сессии 11B.
- `logs/LICENSE_REMINDER.md` — напоминание перед релизным пушем.

Dixi. Dora (A), 2026-11-04. Черновик v0.2, ждёт приёмки оператора.

## 10. Дополнительные фазы (по итогам аудита DeepSeek, 2026-11-04)

Источник: `logs/A/RAG/AUDIT_GAP.md`. DeepSeek содержал подсистемы, которых нет в v5.
Ниже — что перенести, с критериями приёмки. Все — после Ф4/Ф5 базовых.

### Ф4b. Rebirth-надзор — missing
Механика `la_rebirth_monitor.py`:
- Пороги напоминаний: info 500, warn 700, critical 850 (cmds_from_start).
- TTL: info — раз за серию, warn — 2 ч, critical — 30 мин. Без спама.
- Pending-артефакты: `pending_<CH>.json`, проверка mtime > since_ts и наличия next_series
  в TODO/HANDOVER/PROMPT. Эскалация через 30 мин, до 3 раз, потом оператор.
- Hold-режим: `hold_<CH>.flag` — порог отключён, ждём переполнения чата.
- Lock: `rebirth.lock`, TTL 1 ч, JSON {ts, ch}.
- Auto: `ready_<CH>.json` -> `rebirth_master --live`, одно перерождение за раз.
Критерий: канал A при cmds>=850 получает напоминание, готовит артефакты, master
перерождает, table двигается, новый чат получает PROMPT, сосед онбордит.

### Ф5b. Token counter — NOT PORTED

Решение (оператор, 2026-11-04): token counter НЕ переносить.
Причина: формула latin/4+cyr/2.5+other/4 по innerText — грубая эвристика,
не связанная с реальным токенизатором; лимит 3600 — эмпирика; innerText ≠ контекст.
Единственная метрика переполнения: **cmds_from_start** (леджер) + **chat_limit** (баннер).
См. marker_protocol §6: "Токены не смотрим".
Артефакты F5b перемещены в Archive/ (не использовать).

### Ф5c. Архивация бесед — missing
- `export_share`: scroll-loop до стабилизации, дедуп по строкам, NDA-redact.
- QC: final_url==source, тело начинается с «Shared Conversation», нет своих id.
- Хранение: `logs/<CH>/conversations/<series>_share.md` + README-таблица.
Критерий: share-URL -> файл, QC проходит, README обновлён.

### Ф5d. Session handover — partial
- Фаза 1 (за 100-150 id): SESSION_STATE, MILESTONE, INDEX, PROMPT_<next>.
- Фаза 2 (каждые 1000): commit+push, бэкап.
- Фаза 3 (приёмник): новый чат, корневой PROMPT, read RAG, сброс ledger.
- Фаза 4: прощание в старом чате.
Критерий: при cmds>=800 артефакты полные, приёмник восстанавливается по ним.

### Ф6a. Протоколы — missing
- `marker_protocol.md` (полный канон: маркер≠транспорт, p2p≠broadcast, персональные id).
- `roles_and_chain.md` (оператор -> A -> B/C/D, C — апрувер).
- `council_protocol.md` (threads vs chat.jsonl, cc, таймеры).
- `id_range_rule.md` (AAAA0000-9999, переполнение -> AAAB).
- `interface_reference.md` (CRT-эталон).
Критерий: 5 файлов в `RAG/procedures/`, ссылки из INDEX.

### Ф6b. Rescue/guard — missing
- `guard.py`: start --target --timeout, done, [GUARD-ALERT] при таймауте.
- `mutual_rescue.md`, `rescue_unified.md`: три раунда, потом голос оператору.
- `panel_recovery.md`, `self_recovery.md`: reload_chat, recover_chat, restart_via_b.
Критерий: guard start -> timeout -> [GUARD-ALERT] -> RESCUE -> done.

### Ф6c. Суперкнопка (paused) — partial
- Контракт в `PROMPT_ACTIVATION.md`: paused=true -> не пиши блоки, отвечай текстом.
- Правило в `behavior_rules.md`.
- Кнопка «Диалог/Работа» в Mainframe.
Критерий: paused=true -> агент шлёт только текст, мост не исполняет блоки.


---


---

## Статус после сессии 14D (2026-11-05, ночь)

### Сделано в этой сессии


---

---

## Status after 14D session (2026-11-05, night)

### Done this session
- B-45: Chrome 156+ fix in Tools/launcher.py.
- Activation: PROMPT_ACTIVATION.md 9K to 4K, real BEGIN/END markers.
- send_text: CDP Input.insertText. textarea.value check.
- Pause buffer: outbox_CH.jsonl on busy.
- Telemetry: cfg.channel_path (was cfg.path).
- Mnemo: 10-slot grid, placeholders, x1.4/x2/x1.75, card k=0.51, comet Tron.
- CRT: inset 14px, border 8px, outline 3px, radius 20px, Consolas.
- Chat: panels + feed + composer + mic. Glow + blink prompt.
- Pers: list + feed + /api/chat/CH.

### Open (for 15D)
- E2E: live DeepSeek to bridge to exec. Only direct HTTP tested.
- Mnemo buttons: target=agent:X, check launchpad.boot format.
- Comet on real ops (not inject).
- TTS voice call operator: not implemented.
- F5c/F5d/F6a-c: not started.

### Pitfalls for 15D
- web.py whitelist: new .js inline or STATIC_EXTS.
- CDP ws: suppress_origin=True (Chrome 111+ 403).
- CSS bump in index.html (style.css?v=X).
- op=write >200b loses body: staging + read.

Dixi. 14D, 2026-11-05.

---

## Status after 14D session (2026-11-05, night)

### Done this session
- B-45: Chrome 156+ fix in Tools/launcher.py.
- Activation: PROMPT_ACTIVATION.md 9K to 4K, real BEGIN/END markers.
- send_text: CDP Input.insertText. textarea.value check.
- Pause buffer: outbox_CH.jsonl on busy.
- Telemetry: cfg.channel_path (was cfg.path).
- Mnemo: 10-slot grid, placeholders, x1.4/x2/x1.75, card k=0.51, comet Tron.
- CRT: inset 14px, border 8px, outline 3px, radius 20px, Consolas.
- Chat: panels + feed + composer + mic. Glow + blink prompt.
- Pers: list + feed + /api/chat/CH.

### Open (for 15D)
- E2E: live DeepSeek to bridge to exec. Only direct HTTP tested.
- Mnemo buttons: target=agent:X, check launchpad.boot format.
- Comet on real ops (not inject).
- TTS voice call operator: not implemented.
- F5c/F5d/F6a-c: not started.

### Pitfalls for 15D
- web.py whitelist: new .js inline or STATIC_EXTS.
- CDP ws: suppress_origin=True (Chrome 111+ 403).
- CSS bump in index.html (style.css?v=X).
- op=write >200b loses body: staging + read.

Dixi. 14D, 2026-11-05.

---

## Status after 14D session (2026-11-05, night)

### Done this session
- B-45: Chrome 156+ fix in Tools/launcher.py.
- Activation: PROMPT_ACTIVATION.md 9K to 4K, real BEGIN/END markers.
- send_text: CDP Input.insertText. textarea.value check.
- Pause buffer: outbox_CH.jsonl on busy.
- Telemetry: cfg.channel_path (was cfg.path).
- Mnemo: 10-slot grid, placeholders, x1.4/x2/x1.75, card k=0.51, comet Tron.
- CRT: inset 14px, border 8px, outline 3px, radius 20px, Consolas.
- Chat: panels + feed + composer + mic. Glow + blink prompt.
- Pers: list + feed + /api/chat/CH.

### Open (for 15D)
- E2E: live DeepSeek to bridge to exec. Only direct HTTP tested.
- Mnemo buttons: target=agent:X, check launchpad.boot format.
- Comet on real ops (not inject).
- TTS voice call operator: not implemented.
- F5c/F5d/F6a-c: not started.

### Pitfalls for 15D
- web.py whitelist: new .js inline or STATIC_EXTS.
- CDP ws: suppress_origin=True (Chrome 111+ 403).
- CSS bump in index.html (style.css?v=X).
- op=write >200b loses body: staging + read.

Dixi. 14D, 2026-11-05.
