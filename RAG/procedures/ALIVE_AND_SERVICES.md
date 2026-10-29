# ALIVE и сервисы

## 1. Что такое ALIVE

**ALIVE** - механизм проверки, жив ли агент. Реализован в `Tools/watchdog.py`.

## 2. Как работает

1. `watchdog.py --channel L --interval 300 --threshold 3` - per-channel.
2. Каждые `interval//3` секунд: `GET <agent>/ping` -> поле `ago` (сколько секунд назад агент был активен).
3. Если `ago >= interval` (агент молчит дольше порога) **и** `state=on` -> отправить `[ALIVE?]` в чат через kick.
4. `alive_repeat=1800` (30 мин) - повтор не чаще.
5. `kick` refuses if `textarea busy` - оператор печатает, не перебиваем.

## 3. Правила для агента (П1.6)

**Получил задачу:**

1. Включить watchdog канала:

```
python Tools/svc.py start --channel L --kind watchdog --interval 300 --threshold 3
```

2. Записать задачу в `logs/<CH>/TODO.md` (append, не «в голове»).
3. Только потом - работа.

**Задача закрыта и принята:**

- `python Tools/svc.py stop --channel L --kind watchdog`
- Не раньше приёмки (если задача не закрыта - watchdog ON).

**Исключение:** оператор сказал «watchdog ON надолго» - держать.

## 4. При получении `[ALIVE?]`

1. Немедленно ответить `[ALIVE] <серия> на связи` (одна строка).
2. Проверить TODO:
   - Пусто -> короткая реплика + `svc.py stop` (по правилам v5).
   - Не пусто -> вернуться к работе.
3. Не молчать, не удивляться, не «докладывать» развёрнуто.

## 5. Сервисы v5

### Watchdog (per-channel)

- Порт: `<agent>/ping`.
- Файл состояния: `Profiles/<L>/logs/svc_watchdog_<L>.json`.
- Запуск: `svc.py start --channel L --kind watchdog`.

### Recovery (per-channel)

- Проверяет панель (sidepanel) через CDP.
- Если панель «мертва» (нет ответа, `no-answer`, `content bad`) - **F5 (reload)**.
- **Guard:** `_operator_typing` - если оператор печатает -> SKIP.
- Файл состояния: `Profiles/<L>/logs/svc_recovery_<L>.json`.
- Запуск: `svc.py start --channel L --kind recovery`.

### Autorestart (глобальный)

- Для каждого канала с `enabled.flag`:
  1. `/ping` жив? CDP жив?
  2. Ledger двигался за `ledger_stale` (default 600 с)?
  3. Если агент висит + нет движения -> restart через `Bridge/run.py --channel L`.
- **Guard:** `_operator_typing` - если оператор печатает -> SKIP.
- Лог: `logs/svc/autorestart.log`.
- Запуск: `svc.py start --kind autorestart --interval 600`.

## 6. Почему сервисы не перебивают оператора

**Старый проект (грябли):**

- ALIVE перебивал текст в textarea (operator печатал - ALIVE стирал).
- Recovery делал F5 при печати (черновик терялся).
- Autorestart ребутил агента во время беседы.

**v5:**

- `watchdog._kick` - `bridge_kick2` refuses if busy (не стирает).
- `recovery._operator_typing` - проверка всех textarea -> `busy` -> SKIP.
- `autorestart._operator_typing` - то же -> SKIP.

**Проверка (если подозрение на баг):**

1. `Tools/watchdog.py` - есть `_kick` с проверкой?
2. `Tools/recovery.py` - есть `_operator_typing`?
3. `Tools/autorestart.py` - есть `_operator_typing`?
4. Если старое - обновить.

## 7. Файлы состояния

| Файл | Что |
|---|---|
| `Profiles/<L>/logs/svc_watchdog_<L>.json` | {state: on/off, pid, by, at} |
| `Profiles/<L>/logs/svc_watchdog_<L>.pid` | {pid, started, by} |
| `Profiles/<L>/logs/svc_recovery_<L>.json` | то же |
| `logs/svc/svc_autorestart.json` | глобальный |
| `logs/svc/autorestart.log` | действия |

## 8. Управление

```
# статус всех
python Tools/svc.py status

# статус канала
python Tools/svc.py status --channel A

# старт
python Tools/svc.py start --channel A --kind watchdog --interval 300

# стоп
python Tools/svc.py stop --channel A --kind watchdog
```

## 9. Что делать если ALIVE спамит

Симптом: `[ALIVE?]` каждые 30 секунд.

**Причина:** `silence_pinged` сбрасывается на каждый ответ агента.

**v5:** `alive_repeat=1800` (30 мин) - повтор не чаще.

**Если всё равно спамит:**

1. `svc.py stop --channel L --kind watchdog`.
2. Проверить `watchdog.py` - есть ли `alive_repeat`?
3. Если нет - обновить.

