# AGENT_FIRST_RUN - первый запуск агента в v5

**Кому:** новому агенту при первом открытии Chrome-вкладки.
**Когда читать:** до первой команды. Связано с `Templates/extension/onboarding.html` (B-07).
**Закрывает:** B-08.

## Что лежит в `Profiles/<L>/`

- `chrome/` - user-data-dir Chromium для твоего канала. Логин только здесь.
- `config/config.json` - per-channel конфиг (agent_port, cdp, prefix, model).
- `logs/` - ledger_<L>.json, outbox_<L>.jsonl, kick_buffer.jsonl, paused.json, live.json, svc_watchdog_<L>.json.
- `docs/PERSONAL.md`, `docs/TODO.md` - твои личные доки (не путать с `logs/TODO.md`).
- `extension/` - копия `Templates/extension/` под твой канал (agent.py знает свой порт).

Перенос папки `Profiles/<L>` на другой диск = перенос всего агента.

## Линк-лист чатов

- DeepSeek: `https://chat.deepseek.com/a/chat/s/<id>`
- Google AI Mode: `https://www.google.com/search?udm=50`
- Qwen: `https://chat.qwen.ai/` (каркас)
- Alice: `https://alice.yandex.ru/` (каркас)

## Логин - только в чат, не в Google

**Не входи в Chromium/Chrome под Google-аккаунтом.** Это тянет синхронизацию, история, закладки, и мост начинает видеть не ту вкладку. Логинься только в сам сервис чата (DeepSeek / Google AI Mode / Qwen), каждый раз вручную, в своём профиле.

Если Chrome сам редиректит на www.deepseek.com - открой прямой URL чата из линк-листа. Прокси (`DoH 9899`) должен быть запущен, если настроен.

## Что делать при первом старте (порядок)

1. Открыть `Templates/extension/onboarding.html?channel=<L>` (её отдаёт `agent.py` по `GET /onboarding`).
2. Пройти шаги: панель расширения -> логин в чат -> pin tab.
3. Если всё ок - нажать «не показывать» (флаг в `chrome.storage.local`, аналог `_onboarding_is_disabled()` в `agent.py`).
4. Прочитать `RAG/procedures/BEHAVIOR.md` - первым.
5. Прочитать `Templates/PROMPT_ACTIVATION.md` (правила блоков).
6. Доложить оператору: `[<series>] on-line, прочитал N, роль принял, lastId <prefix>0001+`.

## Чего не делать

- Не логинь Chromium в Google-аккаунт.
- Не открывай PWA (`--app=...`) - только полноценное окно Chrome с вкладками.
- Не удаляй `Profiles/<L>/extension/` - агент останется без пульта.
- Не запускай второй `agent.py` на тот же порт - exit(1) при busy (правило 10C).

## Связанные документы

- `RAG/procedures/BEHAVIOR.md` - правила поведения.
- `Templates/PROMPT_ACTIVATION.md` - формат блоков.
- `RAG/procedures/KICK_PROTOCOL.md` - как отвечать коллегам.
- `RAG/procedures/ADAPTERS.md` - какие модели и как переключаются.
- `logs/TODO.md` - живой список задач.

Dixi. 10C (Семён), 2026-11-09.
