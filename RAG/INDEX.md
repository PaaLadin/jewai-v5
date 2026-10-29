# INDEX RAG - JewAI v5

Карта знаний. Точка входа - `README.md`.

## Быстрый старт

- **Новичок** -> `architecture/ARCHITECTURE.md`
- **Оператор** -> `procedures/OPERATIONS.md` + `procedures/TROUBLESHOOTING.md`
- **Агент** -> `procedures/BEHAVIOR.md` (первым), потом `procedures/SYSTEM_MESSAGES.md`, `procedures/KICK_PROTOCOL.md`
- **Разработчик** -> `architecture/AUDIT.md` + `architecture/MODULES.md`

## architecture/

- `ARCHITECTURE.md` - общая схема, слои, порты, потоки данных
- `MODULES.md` - все модули (авто-генерация из файлов)
- `AUDIT.md` - аудит старого проекта (контракты + костыли)

## procedures/ - установка и операции

- `INSTALL.md` - установка с нуля
- `OPERATIONS.md` - команды, лаунчеры, API
- `SYSTEM_KEYS.md` - токены, порты, env, поля конфигов
- `current_state.md` - текущее состояние
- `agent_layout.md` - структура Profiles/<L>

## procedures/ - поведение и коммуникация (ОБЯЗАТЕЛЬНО для агентов)

- `BEHAVIOR.md` - правила поведения (общий)
- `SYSTEM_MESSAGES.md` - системные маркеры ([ALIVE?], [MEETING], [PAUSE-ALL], [AGENT REPORT])
- `KICK_PROTOCOL.md` - как агенты общаются (p2p / broadcast / operator)
- `ALIVE_AND_SERVICES.md` - watchdog, recovery, autorestart
- `STOP_WORD.md` - стоп-слово

## procedures/ - мост и грабли

- `BRIDGE_LIMITS.md` - лимиты моста (write >1.5K, литеральные ###, кириллица)
- `PYTHON_PITFALLS.md` - грабли Python (ASCII-only, sha LF/CRLF, DETACHED)
- `REPLAY_STALE.md` - повторное исполнение старых блоков (инцидент 22.10)

## procedures/ - сбои и перерождение

- `STUCK_STATES.md` - 5 типов стопоров SPA (Server unavailable, утечка тегов, Thinking, пустой ответ, Qwen feedback)
- `REBIRTH.md` - перерождение (триггеры, гейт, lock, CDP cycle, onboard)
- `CHAT_HANDOVER.md` - бэкап старых чатов (scroll-loop, export_share)
- `TROUBLESHOOTING.md` - починка поломок

## knowledge/

- `modules.md` - индекс модулей (auto-generated)

## Правило пополнения

Возникло "а как правильно" - файл в `procedures/`, строка здесь.

