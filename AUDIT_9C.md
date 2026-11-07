
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