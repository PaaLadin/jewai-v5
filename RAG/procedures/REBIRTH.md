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

