# JewAI v5 - RAG

База знаний проекта JewAI v5. Точка входа - этот файл.

## Что такое JewAI v5

JewAI v5 - переписанный с нуля мультиагентный мост между браузерными LLM-чатами
(DeepSeek, Qwen, Alice) и локальной файловой системой. Каждый агент - отдельный
канал (A..J), со своим Chrome-профилем, портом агента, CDP-портом и папкой
`Profiles/<L>/`. Панель оператора (Mainframe) показывает состояние всех каналов
и позволяет управлять ими.

## Быстрый старт

1. Установка: `Tools/installer/install.ps1` (или `install.bat`).
2. Запуск: `Tools/launchers/start-all.ps1` (или через кнопку Launch в инсталляторе).
3. Панель: http://127.0.0.1:8670 (по умолчанию).

## Карта документов

### Обязательно для агента (в этом порядке)

| Документ | Что там |
|---|---|
| `procedures/BEHAVIOR.md` | Правила поведения (общий) |
| `procedures/SYSTEM_MESSAGES.md` | Системные маркеры ([ALIVE?], [MEETING], [PAUSE-ALL], [AGENT REPORT]) - **не путать с оператором** |
| `procedures/KICK_PROTOCOL.md` | Как агенты общаются (p2p / broadcast / оператор) - **не путать транспорты** |
| `procedures/ALIVE_AND_SERVICES.md` | Watchdog, recovery, autorestart (не перебивают оператора) |
| `procedures/STOP_WORD.md` | Стоп-слово (только из живого чата) |

### Architecture

| Документ | Что там |
|---|---|
| `architecture/ARCHITECTURE.md` | Слои, порты, потоки данных |
| `architecture/MODULES.md` | Все модули (auto-generated) |
| `architecture/AUDIT.md` | Аудит старого проекта (44 КБ контрактов) |

### Установка и операции

| Документ | Что там |
|---|---|
| `procedures/INSTALL.md` | Установка с нуля |
| `procedures/OPERATIONS.md` | Команды, лаунчеры, API |
| `procedures/SYSTEM_KEYS.md` | Токены, порты, env, поля конфигов |
| `procedures/TROUBLESHOOTING.md` | Починка поломок |
| `procedures/current_state.md` | Текущее состояние |
| `procedures/agent_layout.md` | Структура Profiles/<L> |

### Мост и грабли

| Документ | Что там |
|---|---|
| `procedures/BRIDGE_LIMITS.md` | Лимиты моста (write >1.5K, литеральные ###, кириллица) |
| `procedures/PYTHON_PITFALLS.md` | Грабли Python (ASCII-only, sha LF/CRLF, DETACHED) |
| `procedures/REPLAY_STALE.md` | Повторное исполнение старых блоков |

### Сбои и перерождение

| Документ | Что там |
|---|---|
| `procedures/STUCK_STATES.md` | 5 типов стопоров SPA |
| `procedures/REBIRTH.md` | Перерождение (триггеры, гейт, lock, CDP cycle) |
| `procedures/CHAT_HANDOVER.md` | Бэкап старых чатов |

### Справочники

| Документ | Что там |
|---|---|
| `INDEX.md` | Оглавление |
| `knowledge/modules.md` | Индекс модулей (auto) |

## Главные принципы v5

- **Один источник правды** - `config.json` в корне.
- **Per-agent isolation** - всё про агента в `Profiles/<L>/`.
- **Никакого хардкода** - порты/пути из `config.json`.
- **Operator-first** - сервисы не перебивают оператора.
- **Replay-guard** - водяной знак + хэш защищают от повторного исполнения.
- **Python-исходники ASCII-only** - кириллица только в данных (JSON, md).

## С чего начать чтение

- **Агент** -> BEHAVIOR -> SYSTEM_MESSAGES -> KICK_PROTOCOL -> ALIVE_AND_SERVICES
- **Новичок** -> ARCHITECTURE -> INSTALL -> OPERATIONS
- **Оператор** -> OPERATIONS -> TROUBLESHOOTING
- **Разработчик** -> AUDIT -> MODULES -> ARCHITECTURE

## Текущая версия

- VERSION: 0.1.0-dev
- 21 тест / 0 fail
- 25 RAG-документов
- JewAI v5, 2026-10-29

