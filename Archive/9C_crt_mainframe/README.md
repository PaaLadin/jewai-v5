# 9C CRT Mainframe (archived 2026-11-08)

**Why archived:** оператор выбрал 15D-версию (мнемосхема совмещена с панелью управления), эта — плоская сетка карточек без связей.

**What's inside:**
- index.html (3422 b) — 5 табов: АГЕНТЫ / ЧАТ / ПРОЕКТЫ / ЛОГИ / ROADMAP.
- style.css (8977 b) — CRT-стиль (зелёный на чёрном), кнопки, лампы, логи.
- app.js (11050 b) — jget/jpost, карточки каналов, чат, логи, roadmap.

**When written:** 2026-11-03/04 (9C, Семён).
**Archived by:** 9C, 2026-11-08.

**Valuable bits (по запросу оператора «вдруг под капотом что-то важное»):**
- Чистая структура: 3 файла, минимум зависимостей, читается за 5 минут.
- Логика ламп: AG/CH/WD/RC — единый lamp() helper (led on / err / warn / unk).
- B-09 auth_status: `needs_login` → LOGIN-кнопка с `chat_url`.
- Булк-кнопки: ПАУЗА ВСЕМ / ПРОДОЛЖИТЬ ВСЕМ / SELF-TEST (по одному вызову на канал).
- API-контракт v5: /api/status, /api/pause, /api/restart, /api/diagnose, /api/messages, /api/send, /api/projects, /api/logs, /api/roadmap.
- Без внешних зависимостей (no frameworks).
