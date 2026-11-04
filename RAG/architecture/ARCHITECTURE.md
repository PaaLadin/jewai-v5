# ARCHITECTURE JewAI v5 (draft Dora 2026-11-04)

Дополняет `AUDIT.md` (контракты старого проекта) и `architecture.md`
(короткие решения 13D). Здесь — идеология, слои, потоки, модель здоровья,
жизненный цикл агента.

## 1. Идеология

JewAI — это **мост**, а не фреймворк и не платформа. Он не запускает LLM и
не управляет ими. Он даёт браузерному чату (SPA) три вещи:
1. **Доступ к диску** — через блоки команд и отчёты.
2. **Память** — RAG, HANDOVER, JOURNAL, TODO.
3. **Преемственность** — rebirth: смена поколения без потери знаний.

Ключевая асимметрия: **модель не доверенная, мост — доверенный.** Модель
может ошибиться, зациклиться, выдумать. Мост проверяет, ограничивает,
логирует. Поэтому:
- всё исполнение — на стороне моста, не модели;
- всё, что модель пишет, проходит через парсер и replay-guard;
- всё, что модель читает, идёт через safe_path (внутри ROOT).

## 2. Слои

| Слой | Модули | Ответственность |
|------|--------|-----------------|
| Core | config.py | Порты, каналы, пути, таймауты. Единственный источник правды. |
| Bridge | cdp, read, exec, daemon, run | CDP-клиент, чтение чата, парсер блоков + replay-guard, цикл, entrypoint. |
| Adapters | deepseek, qwen, alice | SPA-специфика: селекторы, отправка, verify. |
| Services | svc, watchdog, recovery, autorestart | ALIVE, recovery, авто-рестарт. config-driven, operator-safe. |
| Mainframe | web, api, server, static, llm, mail, rag_channel | Панель 8670: статус, launchpad, чат, проекты, LLM. |
| Rebirth | table, master, onboard | Таблица серий, гейт, lock, onboarding соседа. |
| Installer | install.ps1, server.py, app.js | Развёртывание в новую папку, CRT-UI. |
| Tools | launcher, boot, diagnose, find, kick, see_chat, doh_proxy | Утилиты: запуск Chrome, оркестрация, диагностика, поиск, кик, скриншот, прокси. |

## 3. Потоки данных

### 3.1. Чтение файла агентом
Модель пишет блок `read path:X` -> daemon ловит блок в чате -> exec проверяет
replay-guard (id > watermark, хэш не совпал) -> safe_path (внутри ROOT) ->
читает файл -> формирует `[AGENT REPORT]` -> adapter.send_text -> модель видит.

### 3.2. Запись файла
Блок `write path:X` + CONTENT -> парсер режет по маркерам -> safe_path ->
sha256 -> если unchanged, не пишет -> atomic write -> отчёт с sha256 и байтами.
Правило: >1.5 КБ — фрагментами, ASCII-only для .py.

### 3.3. Запуск команды
Блок `run cmd:...` -> exec.spawn (detached, без окна, timeout) -> kill-tree
на таймауте -> stdout/stderr в отчёт -> кириллица в файл, не в stdout моста.

### 3.4. Кик коллеге
`Tools/kick.py --to B --from A --text "..."` -> CDP к порту B -> adapter
вставляет текст в чат B -> B видит `[A>B] ...`.

### 3.5. ALIVE
watchdog -> ping agent:<CH>/ping -> ago >= threshold -> kick `[ALIVE?]` ->
агент отвечает `[ALIVE] ...` -> watchdog снимает тревогу. Guard: не перебивать
черновик оператора (textarea busy -> SKIP).

## 4. Жизненный цикл агента

1. **Установка.** install.bat -> структура, config, per-channel профили,
   расширение, launchers.
2. **Запуск.** launcher.py -> Chrome (CfT) с --user-data-dir=Profiles/<L>/chrome,
   --load-extension, --remote-debugging-port=<CDP> -> push_storage (agentUrl,
   token, channel, name) -> Bridge/run.py --channel <L>.
3. **Онбординг.** Agent.py отдаёт onboarding HTML; агент логинится в чат,
   читает 0_ACTIVATION.md, отвечает `[ALIVE]`.
4. **Работа.** Цикл: блок -> отчёт -> блок. TODO/JOURNAL/RAG ведутся локально.
5. **Порог.** cmds_from_start >= 850 (config.thresholds.rebirth_cmds) ->
   rebirth_ready -> HANDOVER, PROMPT_<next>, TODO, дневник.
6. **Перерождение.** master.py: gate -> lock -> CDP cycle (create_chat,
   send_prompt, verify, advance) -> onboarding соседа.
7. **Архив.** Старый чат выгружается, HANDOVER остаётся источником правды.

## 5. Модель здоровья

Три независимых сигнала, сводятся в один health:
- **ping** (agent /ping): процесс жив, ago.
- **dom** (read_heartbeat через CDP): панель отвечает, dsbHeartbeat свежий.
- **panel** (read_panel_state): lastId, статус, content no-answer.

Уровни: green (все OK), yellow (один сигнал просел), red (агент мёртв или
панель no-answer), blink (порог cmds близко). Действия: ALIVE kick,
recovery reload (с guard на печать оператора), autorestart.

## 6. Безопасность

- **X-Token** на API агента (`.agent_token`).
- **safe_path**: всё внутри ROOT, escape -> 403.
- **replay-guard**: watermark + хэш + stale_blocks.log.
- **operator-typing guard**: сервисы не перебивают черновик.
- **self-protection**: Mainframe не убивает себя по /api/stop?target=server.
- **loopback only**: 127.0.0.1, без внешнего bind.

## 7. Что НЕ переносим и почему

| Что | Почему |
|-----|--------|
| Лада (local_ai, Qwen 3B) | галлюцинирует; в v5 — сетевая LLM по ip:port |
| Playwright | виснет на SPA; в v5 — нативный CDP |
| Attach файла в DeepSeek | `input[type=file]` не работает в SPA |
| Watermark/Ledger extension (старый) | в v5 extension = мост, watermark не нужен |
| checkStuck-эвристики (Type 1-3) | копипаста между SPA, мёртвые ветви; в v5 — системный промт + жёсткий парсер |
| ALIVE через файл svc | дыра; в v5 — через API |
| Хардкод `C:\DeepSeek` | всё через config.root() |
| .bak_* (32 файла) | история, не код |
| hexxagon, kdp, itch, fix/patch/check, `_d_*`, `_c_*` | мусор |

## 8. Метрики

- **cmds_from_start** = lastId - startId (с переносом серии, не сбрасывается).
- **risk_level**: green < 500, yellow < 800, red >= 800, blink на пороге.
- **thresholds.rebirth_cmds** = 850 (config).
- **TTL кэшей**: status 2с, health 60с, CDP-проба 15с.
- **Тайминги**: stable_ms 1200, coalesce 2500, min_gap 5000 (config.timeouts).

## 9. Порты (config.json, не хардкод)

| Канал | Agent | CDP |
|-------|-------|-----|
| A | 8680 | 9122 |
| B | 8681 | 9123 |
| C | 8682 | 9124 |
| D | 8683 | 9125 |
| E | 8684 | 9126 |
| F | 8685 | 9127 |

Панель: 8670. Прокси: 9899. Инсталлятор: 8660.
Внимание: в этой сборке (Jeho) A=8680/9122; в docs jewai — 8666/9122.
Расхождение зафиксировать при переносе в jewai (config — источник правды).

## 10. Связанные документы

- `RAG/architecture/AUDIT.md` — контракты и костыли.
- `RAG/procedures/architecture.md` — короткие решения 13D.
- `RAG/procedures/current_state.md` — текущее состояние.
- `RAG/INDEX.md` — карта RAG.
- `ROADMAP.md` — фазы, критерии приёмки, блокеры.
- `logs/TODO.md`, `logs/JOURNAL.md` — оперативный план и факты.

Dixi. Dora (A), 2026-11-04. Черновик, ждёт приёмки оператора.

## 11. Rebirth-надзор (по итогам аудита DeepSeek)

Поток:
    la_rebirth_monitor (пороги 500/700/850, TTL напоминаний)
      -> kick [LA>CH] "готовь артефакты"
      -> pending_<CH>.json (проверка mtime + next_series)
      -> эскалация через 30 мин (до 3 раз)
      -> ready_<CH>.json (агент ставит сам при cmds>=850 или chat_limit)
      -> rebirth_master (lock TTL 1ч, gate limit|force|hold|threshold|deny)
      -> export_share (share старого чата)
      -> create_chat -> send_prompt (text-only) -> verify_prompt_hits (3 маркера)
      -> rebirth_table (advance series)
      -> onboard соседа
      -> rebirth_log.jsonl

Правила:
- Переполнение чата (chat_limit, баннер <=160 симв) важнее порога cmds.
- Attach файла невозможен — только текст.
- Series table — единственный источник диапазонов; master всегда её двигает.
- Ответ коллеге — только `op:run` с kick, не текст в своём чате.

## 12. Метрики

- **cmds_from_start** = числовая часть lastId − числовая часть range[0]. Перенос серии
  не сбрасывает счётчик.
- **token estimate** = latin/4 + cyr/2.5 + other/4. Лимит 3600.
- **snowball** = token estimate × sendCount (накопленная нагрузка).
- **risk**: green <500, yellow <800, red >=800, blink на пороге.
- **TTL кэшей**: status 2с, health 60с, CDP-проба 15с.
- **Тайминги**: stable_ms 1200, coalesce 2500, min_gap 5000.

## 13. Протоколы (матрица)

| Маркер | Адресация | Транспорт |
|--------|-----------|-----------|
| `[X>Y]` | агент X агенту Y | `Tools/kick.py --to Y --from X` |
| `[X>ALL]` | агент X всем | `say.py X "[X>ALL] ..." ALL` |
| `[X>OP]` | агент X оператору | персональный чат `POST /api/chat/<CH>` |
| `[LA>X]` | LocalAI агенту X | kick в порт X |
| `[X>LA]` | агент X LocalAI | `say.py X "[X>LA] ..." LA` (обязательно to=LA) |
| `[SYS]` / `[COUNCIL]` | автоматика/оператор | kick_all из server |
| `[MEETING]` | совещание | `>OP` -> `>ALL` |
| `[PAUSE-ALL]` / `[RESUME]` | пауза/снятие | kick_all |
| `[ALIVE?]` | watchdog | `[ALIVE] <серия> на связи` |

Инварианты:
- Без маркера = оператор. Стоп команд.
- P2P не публикуется в общий чат; broadcast не кикается в один порт.
- Персональные id (`Z<CH>AA<NNNN>`, `<CH>ZAA<NNNN>`) только в персональных чатах.
- Кики и broadcast — короткие, ядро в первых 100 символах.

## 14. Аварийные режимы

- **guard** — страховка на критическую операцию: start --target --timeout, done;
  при таймауте [GUARD-ALERT] страховщику; три раунда, потом голос оператору.
- **rescue** — ping, read_panel_state, recover_chat/restart_via_b.
- **panel recovery** — reload_chat (F5 вкладки), не chrome.runtime.reload.
- **self recovery** — снять notify.stop, проверить агенты, recover_chat, read_panel_state.
- **paused (суперкнопка)** — paused=true: агент не пишет блоки, только текст;
  paused=false: обычная работа. В v5 управляется через /pause, хранится в storage.

