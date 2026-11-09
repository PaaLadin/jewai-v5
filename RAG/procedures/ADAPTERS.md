# ADAPTERS - адаптеры моделей в v5

**Актуально:** 2026-11-09 (10C).
**Закрывает:** BUG-004 (google не описан).

## Что такое адаптер

Адаптер - класс в `Adapters/<name>.py`, реализующий контракт:

- `HOST` - подстрока URL, по которой искать вкладку чата в CDP.
- `MARKER` - подстрока URL, означающая "это чат, не поиск" (по умолчанию `/a/chat/s/`).
- `collect_blocks(cdp, last_n)` -> list[Block] - читать новые блоки из DOM.
- `send_text(cdp, text)` -> bool - вставить текст и отправить; True если textarea опустела.
- `verify_prompt_hits(cdp, markers)` -> int - сколько маркеров нашлось в body.
- `new_chat(cdp)` -> bool - перейти на главную и подождать textarea.

`Bridge/run.py` выбирает адаптер по `config.channels.<L>.model`.
Поддерживаемые значения: `deepseek`, `qwen`, `alice`, `google`.

## deepseek

- Файл: `Adapters/deepseek.py`.
- HOST: `chat.deepseek.com`.
- MARKER: `/a/chat/s/`.
- collect_blocks: `.ds-message` -> `.ds-assistant-message-main-content` -> `pre, code`.
- send_text: `Input.insertText` + CDP `Input.dispatchKeyEvent` Enter x3 (10C: было JS dispatchEvent, unreliable).
- verify_prompt_hits: 10C - если textarea непусто, return 0 (черновик = не отправлено).
- new_chat: 10C - поллинг URL+textarea до 10с.
- Статус: рабочий. Порт по умолчанию: 9122-9125 (CDP A-D).

## qwen

- Файл: `Adapters/qwen.py`.
- HOST: `chat.qwen.ai` (по коду).
- collect_blocks: селекторы SPA + нормализация gutter+NBSP.
- send_text: React `_valueTracker` reset + native click + Enter fallback.
- Статус: каркас, live-тест не проводился. Покрыт `test_adapters_qwen_alice.py`.
- Известное: копипаста checkStuck из deepseek -> мёртвые ветви (урок AUDIT §22).

## alice

- Файл: `Adapters/alice.py`.
- HOST: `alice.yandex.ru` (по коду).
- collect_blocks: нормализация NBSP+CRLF.
- send_text: Enter x2.
- Статус: каркас, live-тест не проводился. Покрыт `test_adapters_qwen_alice.py`.

## google (BUG-004)

- Файл: `Adapters/google.py` (5465 б).
- HOST: `google.com`.
- MARKER: `/search` (не `/a/chat/s/`, как у остальных).
- URL чата: `https://www.google.com/search?udm=50` (AI Mode).
- Механика (из `C:/DeepSeek/AI-Swing-Bridge` content.js + background.js):
  1. Найти видимую textarea (две: скрытая search и видимая AI Mode input).
  2. `focus` -> clear -> `execCommand("insertText")` -> `input/change` -> `focus`.
  3. Отправка: CDP `Input.dispatchKeyEvent` keyDown+keyUp VK 13 (Enter), БЕЗ клика по send.
     Причина: клик по send открывает боковую панель - старая боль.
- collect_blocks: `document.body.innerText` + `parse_blocks()` (DOM AI Mode нестабилен, ledger защищает от replay).
- verify_prompt_hits: body.innerText + markers.
- Статус: каркас, live-проверен один раз (15D, 2026-11-06) на вкладке 9225, ACK получен.
- Покрыт `Tools/tests/test_google_adapter.py` (10 проверок: execCommand, CDP Enter x2, NO Mouse click, busy guard).

## Как подключить google

1. Открыть Chrome с CDP на нужном порту, вкладка `google.com/search?udm=50`.
2. В `config.json`: `channels.<L>.model = "google"`, `channels.<L>.agent_port` - свободный порт канала, `channels.<L>.cdp` - порт Chrome.
3. Перезапустить `Bridge/run.py --channel <L>`.

Сейчас A-D все на `deepseek`. Google - опция, не по умолчанию.

## Переключение через UI

Mainframe 8670 -> ⚙ (в topbar) -> `POST /api/settings {"channel":"A","model":"google"}`.
Или напрямую: `GET /api/settings` / `POST /api/settings`.

## Что НЕ адаптер

- `Adapters/base.py` - Protocol-контракт, не реализация.
- `Bridge/cdp.py` - низкоуровневый CDP, используется адаптерами.
- `Bridge/exec.py::parse_blocks` - общий парсер, не адаптер.

## История

- 2026-11-06 (15D): google адаптер создан по мотивам AI-Swing-Bridge, live-проверен один раз.
- 2026-11-09 (10C): google формально описан в этом файле (BUG-004). deepseek обновлён (verify/Enter/new_chat).

Dixi. 10C (Семён), 2026-11-09.
