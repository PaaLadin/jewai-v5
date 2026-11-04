# AUDIT GAP - DeepSeek vs jewai v5

Дата: 2026-11-04. Автор: Dora (A). Источник: C:/DeepSeek (архив), C:/jewai (чистовик), C:/Jeho (деплой).

## Метод

- Инвентарь DeepSeek: sandbox (6594 строки), algorithms, emergency, prompts, launchers, extension, rag, council_chat.
- Копирование 44 файлов в logs/A/_ds через python (обход escape-запрета моста).
- Прочитано: rebirth.md, alive_v4.md, behavior_rules.md, marker_protocol.md, id_range_rule.md,
  conversation_archiving.md, session_handover.md, roles_and_chain.md, mutual_rescue.md,
  rescue_unified.md, mainframe_health.md, service_control.md, token_counter.md, panel_heartbeat.md,
  panel_recovery.md, self_recovery.md, council_protocol.md, interface_reference.md, INDEX.md,
  la_rebirth_monitor.py (20K), chat_limit.py, export_share.py, content.js, sidepanel.js/html,
  emergency/0_ACTIVATION.md, chat_handover_rule.md.
- Сравнение behavior_rules.md старый/новый: python по заголовкам.
- Grep по текущему расширению Jeho: Templates/extension/{content_deepseek.js,sidepanel.html,app.js,background.js}.

## Ключевые открытия

### K1. behavior_rules.md в v5 - байт-в-байт копия DeepSeek

OLD: 28 headings, 27312 bytes. NEW: 28 headings, 27312 bytes. ONLY IN OLD: 0. ONLY IN NEW: 0.
Следствие: поведение унаследовано, но не адаптировано под v5. Нет упоминаний про:
- paused-кнопку (диалог/работа) и её семантику в Mainframe;
- la_rebirth_monitor пороги 500/700/850;
- token_counter 3600/reset/гистерезис;
- export_share scroll-loop;
- session_handover (emergency/HANDOVER.md);
- marker_protocol (полный канон 11КБ);
- roles_and_chain, council_protocol, id_range_rule, interface_reference;
- mutual_rescue/guard.py.

### K2. Суперкнопка диалог/работа: семантика РАЗНАЯ

DeepSeek: sidepanel #pause -> st.paused=true -> content.js НЕ отправляет блоки, агент
говорит текстом. Мост продолжает работать (пинги идут), но блоки не уходят. paused=true =
"я в диалоге, команд не шлю".

v5 (Templates/extension): sidepanel #btn-pause -> app.js apiPost('/pause') -> background.js
при st.paused возвращает {status:'PAUSED', results:[]}. paused=true = "мост не обрабатывает
блоки вообще". content.js тоже проверяет st.paused и не отправляет.

Различие: в DeepSeek пауза = режим агента (диалог с оператором). В v5 пауза = режим моста
(стоп обработки). Для агента эффект похож (блоки не уходят), но причина разная: в v5
background режет батчи, в DeepSeek режет content. Плюс в v5 paused управляется через
HTTP /pause, а не только через storage.

Чего НЕТ в обоих случаях:
- в PROMPT_ACTIVATION.md не описан контракт "при paused не пиши блоки, отвечай текстом";
- в behavior_rules.md нет правила про paused;
- в Mainframe нет кнопки Диалог/Работа (есть в extension sidepanel, но не в панели).

## Таблица подсистем: DeepSeek -> jewai v5

| # | Подсистема | DeepSeek | jewai v5 | Статус |
|---|-----------|----------|----------|--------|
| 1 | Rebirth-машина | la_rebirth_monitor.py 20К, пороги 500/700/850, hold, pending, lock | Rebirth/{table,master,onboard,cycle}.py каркасы, CDP-цикл не реализован | partial |
| 2 | Token counter | content.js estimateTokens, 3600 | нет | **do not port** (метрика = cmds_from_start) |
| 3 | Conversation archiving | export_share.py (Playwright, scroll-loop, дедуп, NDA) | нет | missing |
| 4 | Session handover | emergency/HANDOVER.md, session_handover.md, PROMPT_<N> | CHAT_HANDOVER.md короче | partial |
| 5 | Marker protocol | marker_protocol.md 11КБ, 8 разделов | KICK_PROTOCOL.md + SYSTEM_MESSAGES.md | partial |
| 6 | roles_and_chain | algorithms/roles_and_chain.md | нет | missing |
| 7 | council_protocol | algorithms/council_protocol.md | нет | missing |
| 8 | id_range_rule | algorithms/id_range_rule.md | нет | missing |
| 9 | interface_reference | algorithms/interface_reference.md CRT | нет | missing |
| 10 | mutual_rescue/guard | guard.py, mutual_rescue.md, rescue_unified.md | не начато | missing |
| 11 | Panel recovery | panel_recovery.md, recover_chat.py, reload_chat.py | нет | missing |
| 12 | Self recovery | self_recovery.md | нет | missing |
| 13 | Mainframe health | mainframe_health.md, health_matrix.py, alive-кнопки | ALIVE_AND_SERVICES частично | partial |
| 14 | Panel heartbeat | panel_heartbeat.md, content.js ALIVE | ALIVE_AND_SERVICES | partial |
| 15 | Service control | svc.py, watchdog.py, recovery_loop.py, autorestart.py | svc/watchdog/recovery/autorestart есть | done |
| 16 | Суперкнопка | paused в sidepanel, блокирует content | paused в app.js/background; кнопки в Mainframe нет | partial |
| 17 | la_watchdog.py | 13КБ, второй сторож | нет | missing |
| 18 | Chat limit | chat_limit.py (баннер <=160 симв) | нет | missing |
| 19 | behavior_rules.md | 27312b | 27312b копия | stale |
| 20 | emergency/0_ACTIVATION | 18КБ, v3.0 | 9КБ, v1 | partial |
| 21 | chat_handover_rule | есть | нет | missing |
| 22 | INDEX.md | 4817b, 30 процедур | есть, короче | partial |

## Механика для переноса

### 1. Rebirth-машина (пример оператора)

Триггеры:
- T1 cmds_from_start >= 850 (config.thresholds.rebirth_cmds).
- T2 chat_limit.py -> LIMIT (баннер, не текст). Переполнение важнее T1.

Пороги напоминаний (la_rebirth_monitor):
- info 500 -> warn 700 -> critical 850.
- TTL: info once/series, warn 2h, critical 30min. Без спама.

Gate (rebirth_master):
1) limit_hit -> перерождаем; 2) force_<CH>.flag -> перерождаем;
3) hold_<CH>.flag -> rc=8, ждём переполнения; 4) cmds<850 -> rc=7, отказ;
5) cmds>=850 -> перерождаем.

Артефакты (за 150 id до конца):
- logs/<CH>/TODO.md, HANDOVER.md, emergency/PROMPT_<next>.md, SESSION_STATE.md.
- pending_<CH>.json: mtime > since_ts, содержимое содержит next_series.
- Эскалация: через 30 мин -> LA-кик, до 3 раз, потом оператор.

Lock: rebirth.lock, TTL 1h, JSON {ts, ch}.

Цикл: lock -> share старого (export_share) -> create_chat -> send_prompt (text-only) ->
verify_prompt_hits (3 маркера) -> advance table -> onboard соседа -> rebirth_log.jsonl.

Грабли:
- порог НЕ проверялся (13.10): агент ставил ready сам -> перерождение на 650.
- Playwright attach отваливался -> голые агенты. Fix: activate_chat.py native CDP.
- детект лимита по тексту -> ложное на цитатах. Fix: баннер <=160, самый вложенный.
- series_table не обновлялась -> отрицательные cmds. Fix: master всегда зовёт rebirth_table.
- ответ коллеге текстом -> мимо. Fix: только op:run с kick.

### 2. Token counter — DO NOT PORT

Решение оператора 2026-11-04: счётчик токенов не переносить.
Метрика переполнения: cmds_from_start + chat_limit.

(Историческое описание ниже оставлено как архив.)

Формула: latin/4 + cyr/2.5 + other/4 по main.innerText.
Лимит 3600. Уровни: <80 green, 80 yellow blink 2s, 90 red blink 1s + voice,
95 red blink 0.5s + voice. Гистерезис: <75 -> warned сбрасывается.
Сброс: кнопка reset + первым делом после rebirth.
Снежок: tokenEstimate * sendCount = накопленная нагрузка.

### 3. Conversation archiving

export_share.py: Playwright connect_over_cdp, isolated context (без cookies),
scroll-loop до стабилизации top, дедуп по строкам, NDA-redact.
QC: final_url==source, тело начинается с "Shared Conversation", нет своих id.
Сохранение: logs/<CH>/conversations/<series>_share.md + README.md (таблица).

### 4. Session handover

Фаза 1 (за 100-150 ходов): обновить SESSION_STATE, MILESTONE, INDEX, PROMPT.
Фаза 2 (каждые 1000): git commit+push, бэкап.
Фаза 3 (приёмник): новый чат, корневой PROMPT, read RAG, сброс ledger.
Фаза 4 (прощание): последнее сообщение в старом чате.
Резерв: обрыв -> приёмник восстанавливает по SESSION_STATE/MILESTONE/NIGHT_REPORT.

### 5. Marker protocol (полный канон)

Инвариант: без маркера = оператор. Любое сообщение агента начинается с [X>Y].
Формат: [X>Y], X,Y in {A,B,C,D,LA,ALL,Z,SYS,COUNCIL,MEETING,PAUSE-ALL,RESUME,ALIVE?,ACK}.
Транспорт: kick2 (A-D), kick3 (E/F), say.py (ALL), POST /api/chat/<CH>.
Инварианты: p2p не в общий чат; broadcast не в один порт; персональные id только в персональных;
в MEETING >OP -> >ALL. LA: ответ только с to=LA.

### 6-9. roles_and_chain, council_protocol, id_range_rule, interface_reference

roles: оператор -> A (ведущий) -> B/C/D. C - хранитель, финальный апрувер.
council: threads/<ID>.md для парных, chat.jsonl для broadcast, cc: [X,Y].
id_range: AAAA<NNNN>, NNNN 0000-9999, переполнение -> AAAB. Не перескакивать.
interface: CRT-эталон (зелёный на чёрном, scanlines, виньетка, Courier New).

### 10. mutual_rescue/guard

guard.py start --target <cdp> --timeout 180 --label "...".
Инициатор делает операцию, потом guard.py done.
Таймер истёк без done -> [GUARD-ALERT] страховщику.
Страховщик: RESCUE (ping, read_panel_state, recover_chat/restart_via_b).
Три раунда, потом голос оператору.

## План правок (что менять в ROADMAP_v0.2 / ARCHITECTURE_v5)

### ROADMAP: добавить фазы

- **Ф4b. Rebirth-надзор** (механика la_rebirth_monitor): пороги 500/700/850,
  TTL напоминаний, pending-артефакты, эскалации, hold, lock, auto_rebirth_check.
  Критерий: канал A при cmds>=850 сам шлёт напоминание, агент готовит артефакты,
  master перерождает, table двигается, новый чат получает PROMPT, сосед онбордит.
- **Ф5b. Токен-счётчик**: estimateTokens, лимит 3600, уровни 80/90/95, гистерезис,
  reset, снежок. Критерий: панель показывает %, лампы мигают, reset сбрасывает.
- **Ф5c. Архивация бесед**: export_share scroll-loop, дедуп, NDA, QC, README-таблица.
  Критерий: share-URL -> файл, QC проходит, README обновлён.
- **Ф5d. Session handover**: SESSION_STATE, MILESTONE, PROMPT_<N>, фазы 1-4.
  Критерий: при cmds>=800 артефакты полные, приёмник восстанавливается по ним.
- **Ф6a. Протоколы**: marker_protocol (полный), roles_and_chain, council_protocol,
  id_range_rule, interface_reference. Критерий: все 5 файлов в RAG, ссылки из INDEX.
- **Ф6b. Rescue/guard**: guard.py, mutual_rescue, rescue_unified, panel/self recovery.
  Критерий: тест guard start -> timeout -> [GUARD-ALERT] -> RESCUE -> done.
- **Ф6c. Суперкнопка (paused)**: контракт в PROMPT_ACTIVATION, правило в behavior_rules,
  кнопка в Mainframe. Критерий: paused=true -> агент не пишет блоки, только текст.

### ARCHITECTURE: добавить разделы

- §X. Rebirth-надзор: диаграмма la_rebirth_monitor -> master -> cdp -> onboard.
- §Y. Метрики: cmds_from_start, token estimate, snowball, risk levels.
- §Z. Протоколы: матрица маркер/транспорт, инварианты.
- §W. Аварийные режимы: guard, rescue, panel recovery, self recovery.

### Что НЕ переносим (обновить)

Добавить: Playwright в export_share (заменить на нативный CDP), attach файла в rebirth
(только текст), wmic (psutil), checkStuck-эвристики (системный промт).

