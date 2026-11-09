# Перерождение (rebirth)

## 1. Что такое перерождение

Агент в чате имеет ограничение: **cmds** (число исполненных команд) и объём контекста.
Когда cmds >= порога (default 850) **или** чат переполнен - агент "умирает" (перестаёт отвечать)
и на его место приходит **преемник** с новым диапазоном id.

**Модули:** Rebirth/table.py, master.py, cycle.py, onboard.py.

## 2. Два триггера

1. **cmds >= 850** - плановое перерождение по метрике.
2. **Переполнение чата** (limit баннер) - экстренное перерождение.

**Метрика cmds:** `cmds_from_start` из `/api/status`. Единственная метрика, токены не смотрим.

## 3. Гейт (check_gate)

Перед перерождением - проверка, что оно разрешено:

| Условие | Что означает |
|---|---|
| `limit` | Чат переполнен - форс |
| `force` | Флаг `force_<CH>.flag` - оператор дал ОК |
| `hold` | `hold_<CH>.flag` - порог отключён, ждём переполнения |
| `threshold` | `cmds >= 850` |
| `deny` | Всё остальное - отказ |

## 4. Lock (TTL 1 час)

Один файл `Rebirth/rebirth.lock` - атомарный, TTL 1 час.

Пока lock активен - другой rebirth не запустится.

## 5. CDP-цикл (cycle.py)

1. `create_chat` - создать новый чат в SPA.
2. `send_prompt` - отправить PROMPT_<next>.md в новый чат.
3. `verify_prompt_hits` - проверить 3 маркера из PROMPT в теле чата (>= 1 = delivered).
4. `advance` - сдвинуть `series_table.json` (current_series -> next_series).

**Если verify fail:** таблица НЕ двигается, лог `rebirth_log.jsonl` с FAIL.

## 6. Onboard (onboard.py)

После успешного rebirth - приветствие новичка от соседа по кругу (A -> B, B -> C, ...).

Кик с `ONBOARD_MSG`: представиться, познакомиться, через 5 мин - инструкция.

## 7. Артефакты передачи

Перед перерождением текущий агент обязан подготовить:

| Файл | Что |
|---|---|
| `logs/<CH>/HANDOVER_<next>.md` | Передача (что сделано, что открыто) |
| `logs/<CH>/TODO.md` | Открытые задачи |
| `emergency/PROMPT_<next>.md` | Промт преемника (роль, диапазон, что читать) |
| `logs/<CH>/JOURNAL.md` | Итоговая запись |

**Порог подготовки:** за 150 id до конца серии (например, `AAAA8850` для `AAAA8000-8999`).

## 7.5. Экспорт старого чата (export_share)

Перед rebirth нужно сохранить текущий диалог. Инструмент: `Tools/export_share.py`.

```
python Tools/export_share.py --url <share_url> --out logs/<CH>/conversations/<series>_share.md --port <CDP>
```

Механика: CDP-only (без Playwright), изолированный browser context (cookies не передаются),
scroll-loop с дедупом, NDA-блоки вырезаются в `[NDA-REDACTED]`. Добавлен 10C (2026-11-09,
закрывает BUG-006).

## 8. Проверка через `see_chat` (глазами новичка)

После подъёма преемника - **смотреть скриншотом** через CDP:

```
python Tools/see_chat.py --cdp 9222 --out logs/A/see_A.png
python Tools/see_chat.py --cdp 9222 --text-only --out logs/A/see_A.txt
```

Искать:

- Принял ли роль (пишет `[Nx] on-line`).
- Шлёт ли блоки (правильные обёртки).
- Не застрял ли черновик.
- Не рассуждает ли «не могу».

## 9. Чего НЕ делать

- Не хардкодить range (таблица - единственный источник).
- Не сдвигать таблицу при fail (rebirth_log FAIL).
- Не перерождать E/F (Qwen/Alice - тестовые, rebirth только A-D).

## 10. Файлы состояния

| Файл | Что |
|---|---|
| `logs/rebirth/series_table.json` | Таблица серий (current, next, ranges) |
| `logs/rebirth/ready_<CH>.json` | Флаг готовности к rebirth |
| `logs/rebirth/force_<CH>.flag` | Форс-флаг от оператора |
| `logs/rebirth/hold_<CH>.flag` | Hold-режим |
| `logs/rebirth/rebirth.lock` | Lock (TTL 1h) |
| `logs/rebirth/rebirth_log.jsonl` | Лог циклов (OK и FAIL) |

## 11. Фиксы 9C (2026-11-08) — rebirth

### 11.1. Single-instance guard (Monitor)

**Проблема:** одновременно жили 8 копий `Tools/rebirth_monitor.py` — каждая кикала свои reminders. Спам «Пора перерождаться» на каждом тике.

**Решение:** при старте Monitor — Windows `CreateFileW` exclusive lock на `logs/rebirth/monitor.lock`. Если файл уже занят — `sys.exit(0)` с сообщением `already running`.

**Когда срабатывает:** только на старте процесса. Не блокирует dry-run `--once` внутри уже запущенного демона.

**Проверка:** `python Tools/rebirth_monitor.py --once` при живом демоне → `already running, exit`.

### 11.2. Cooldown между киками (10 мин)

**Проблема:** если уровень меняется (warn→critical) или lastId растёт каждый тик, Monitor кикал на каждый новый `lastId`.

**Решение:** `_recent_kick(ch, 600)` — глобальный словарь `_LAST_KICK`. После кика по каналу — 10 минут тишины для этого канала. Остальные каналы не блокируются.

### 11.3. TABLE STALE guard

**Проблема:** если `series_table.json` устарел (например, `range=BBAB2000-2999`, а реально `lastId=BBAB3162`), Monitor считает `cmds = 3162-2000 = 1162` → «critical». Хотя реально `cmds = 162`.

**Решение:** перед подсчётом `cmds` — проверка `n > range_end`. Если true → не кикать, писать `TABLE STALE <CH> lastId=X > range_end=Y` в `watchdog.log`. Оператор должен обновить таблицу.

### 11.4. Формат handover — PROMPT_ACTIVATION

**Проблема:** новый агент получал PROMPT_<next>.md без шапки про формат блоков. В старом DeepSeek `rebirth_send_prompt.py` давал литеральные `|` (модель понимала как одну строку) и не оборачивал в бэктики.

**Решение:**
- `Templates/PROMPT_ACTIVATION.md` — шапка, которая приклеивается к PROMPT.
- `Rebirth/cycle.py` — при формировании body читает этот файл (если есть) и вставляет между header и prompt_text.
- Явные правила: оборачивать в бэктики, каждое поле на своей строке, никаких `|`.

### 11.5. `rebirth_table.update()` — только после `cycle`

**Проблема (инцидент 08.11):** кто-то вызвал `rebirth_table.update('B')` напрямую, минуя master. Таблица B ушла в 14B, хотя агент был в 13B. Ложное перерождение.

**Рекомендация (не реализовано в v5):** `update()` не должен двигать таблицу, если последняя запись в `rebirth_log.jsonl` для канала не `result=OK`. Проверять в начале `update()`, отказывать при отсутствии.

### 11.6. Гейт 850 (проверка)

**Проверено в v5:**
- `Tools/rebirth_monitor.py` — при `cmds < 850` не кикает, в логах только `monitor ok: A=X B=Y C=Z`.
- `Rebirth/master.py` — без `ready_<CH>.json` не запускается.
- `Master.check_gate()` → verdict `threshold` только при `cmds >= threshold`.
- `Master.run(live=False)` — dry_run_ok, без изменений.

### 11.7. `series_table.json` для v5

**Создан:** 2026-11-08, 9C.
**Содержание:** A=1A (AAAA0001), B=1B (BBAA0001), C=1C (CCAA0001), D=1D (DDAA0001).
**Смысл:** v5 чистый проект, начинаем с 1-й серии. По мере роста (850 команд) — rebirth сдвигает в 2A/2B/2C/2D, потом 3A... После 9999 — следующая буква префикса (AAAA→AAAB).

### 11.8. Архитектурная заметка про `no_last_id`

**Симптом в v5:** Monitor возвращает `no_last_id` по всем каналам A/B/C/D.

**Причина:** `Monitor.last_id_of()` делает GET `http://127.0.0.1:<agent_port>/status`, ожидая поле `lastId` в JSON-ответе. Агент v5 (`Templates/extension/agent.py`) отдаёт `/ping`, `/svc_status`, `/live`, но **не `/status`**.

**Варианты для будущего:**
- (а) Агент v5 добавить `/status` с полем `lastId` (из ledger).
- (б) Monitor изменить: `last_id_of()` читает `Profiles/<CH>/logs/ledger_<CH>.json` напрямую (файл).
- (в) `last_id_of()` фолбэк: probe панели через CDP (как в DeepSeek).

**Реализовано 10C (2026-11-09), вариант (б):** в `Tools/rebirth_monitor.py::last_id_of` добавлен fallback на файл `Profiles/<L>/logs/ledger_<L>.json` (поле `watermark`, пишет `Bridge/exec.py::Ledger`). Порядок: HTTP `/status` (legacy) -> ledger -> None. Порог 850 теперь работает по ledger без правок `Templates/extension/agent.py` (вариант (а) не понадобился). Проверено: песочница 5/5, `test_rebirth_monitor.py` 12/12, `test_cycle.py` fails=0.

---

Dixi. 9C (Семён), 2026-11-08.
