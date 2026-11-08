# Голосовой вызов (voice_call)

**Файл:** `Tools/voice_call.py`.
**Назначение:** голосовое оповещение оператора о завершении задачи.

## Логика работы
1. **Снятие mute:** Скрипт принудительно снимает флаг Mute (через Windows Core API).
2. **Проверка громкости:** Читает текущую громкость.
3. **Ночной режим:** Если время с 22:00 до 08:00 и громкость < 5%, вызов отменяется (чтобы не будить).
4. **Дневной режим:** Если время с 08:00 до 22:00 и громкость < 5%, громкость поднимается до 15%.
5. **Синтез речи:** Использует `System.Speech` для произнесения фразы.

## Зависимости
- Нет сторонних библиотек (используется встроенный C# через PowerShell и `System.Speech`).

## 9. TTS notify + stop (9C, 2026-11-08)

### Что это

Голосовое уведомление оператора: агент/UI зовёт `/notify` → `notify_me.py` говорит фразу N раз с интервалом. Если оператор печатает в чате (или коллега кикает не с `[`) — TTS должен **замолкнуть** до следующего повтора.

### Компоненты v5

| Файл | Роль |
|---|---|
| `Tools/notify_me.py` | TTS через PowerShell SAPI + SSML. Читает `--file`/`--text`, крутит `--repeat` раз, проверяет `runtime/notify.stop` перед каждым повтором и каждые 5с в паузе. |
| `Templates/extension/agent.py` | `/notify` — запускает `notify_me.py` detached (PID возвращает, `-B` флаг). `/notify-stop` — пишет `runtime/notify.stop`. |
| `Templates/extension/background.js` | `notify` → `agent /notify`. `notify-stop` → fire-and-forget fetch `/notify-stop` с AbortController 5 мин. |
| `Templates/extension/content_deepseek.js` | `setInterval(_voiceStopCheck, 1000)`: видит новый текст в textarea (не `[`, не наш), → `sendMessage({type: 'notify-stop'})`. |

### Ключевые правила

1. **Stop-файл один:** `runtime/notify.stop`. И agent, и notify_me смотрят туда.
2. **Fire-and-forget:** background.js НЕ ждёт ответа `/notify-stop` — `onMessage` никогда не блокируется. Это убрало корень залипаний панели.
3. **Фильтр `[`:** content.js не считает «оператор печатает», если текст начинается с `[`. Это `[AGENT REPORT]`, `[A>B]`, `[SYS]` — их bridge и кики.
4. **Один экземпляр notify_me:** `runtime/notify.lock` (O_EXCL + PID check + 120с stale).
5. **Activity backoff:** если `runtime/watchdog_indep.heartbeat` свежий (<60с) — пауза 5 мин, потом проверка снова.

### Тест (прожит 2026-11-08)

1. `POST /notify` на C (repeat=3, interval=30, гимн).
2. Оператор печатает после 1-го повтора.
3. `_voiceStopCheck` видит текст, шлёт `notify-stop`.
4. background fire-and-forget → agent → `runtime/notify.stop`.
5. `notify_me.py` в цикле паузы видит stop-файл → `stop file, exit`.
6. **Итог:** 2-го и 3-го повтора не было. Тест принят.

### Грабли (кровью)

1. **`ROOT / "notify.stop"` vs `runtime/notify.stop`** — первая версия писала в корень, а `notify_me.py` смотрел в `runtime/`. Stop не работал. Исправлено.
2. **`voiceActive` флаг в background** — первая версия блокировала `notify-stop` если TTS не запущен через UI. Но `/notify` может прийти от агента/оператора напрямую, минуя UI. Убрали проверку — всегда шлём.
3. **`__pycache__` в extension** — Chrome отказывается грузить расширение, если в папке есть `__pycache__`. Фикс: `sys.dont_write_bytecode = True` в каждом `agent.py` + `pythonw -B`.
4. **Кириллица в `--text`** — не передавать как аргумент cmd (cp1251). Только через `--file` (UTF-8).

### Связанное

- `Tools/voice_call.py` — Windows SAPI wrapper (speak/mute/volume). НЕ notify_me.
- `runtime/notify.txt` — текст фразы (UTF-8).
- `runtime/notify.stop` — флаг остановки.
- `runtime/notify.lock` — lock процесса.
- `logs/runtime/notify.log` — лог (start/speak/stop/done).
