# CDP транспорт v5

**Статус:** заглушка, наполняется в Ф2.

## Принципы

- Только нативный CDP через websocket-client. Playwright на SPA (DeepSeek, Qwen, Alice) виснет 30с — не использовать.
- HTTP /json/list быстрый (<0.1с) — использовать для получения списка target'ов.
- Порты: A=9122, B=9123, C=9124, D=9125, E=9126, F=9127.
- Page.bringToFront перед Runtime.evaluate — фоновая вкладка морозит JS-контекст.
- Runtime.evaluate с awaitPromise=True для промисов.

## Инструменты

- cdp_client.py — базовый клиент (eval, call).
- read_panel_state2.py — состояние панели (0.1–3с vs 30с).
- bridge_kick3.py — кик в чат с fallback Enter (для SPA).
- rebirth_open.py — создание чата + отправка PROMPT текстом.

## Грабли

- Runtime.evaluate без awaitPromise -> {}.
- Кириллица в stdout моста бьётся (cp1251) — писать в файл.
- Вкладка DeepSeek в фоне -> Runtime.evaluate висит 30с.

Dixi. 12D, 2026-10-27.