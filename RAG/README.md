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

| Документ | Что там |
|---|---|
| `architecture/ARCHITECTURE.md` | Общая архитектура, потоки данных, порты |
| `architecture/MODULES.md` | Все модули с контрактами |
| `architecture/AUDIT.md` | Аудит старого проекта (контракты + костыли) |
| `procedures/INSTALL.md` | Установка с нуля |
| `procedures/OPERATIONS.md` | Команды запуска/остановки, лаунчеры |
| `procedures/SYSTEM_KEYS.md` | Токены, порты, env-переменные |
| `procedures/BEHAVIOR.md` | Правила поведения агентов |
| `procedures/TROUBLESHOOTING.md` | Починка типовых поломок |
| `procedures/current_state.md` | Текущее состояние (обновляется) |
| `procedures/agent_layout.md` | Структура папок агента |
| `knowledge/modules.md` | Индекс модулей (auto-generated) |

## Главные принципы v5

- **Один источник правды** - `config.json` в корне.
- **Per-agent isolation** - всё про агента в `Profiles/<L>/`.
- **Никакого хардкода** - порты/пути из `config.json`.
- **Operator-first** - сервисы не перебивают оператора.
- **Replay-guard** - водяной знак + хэш защищают от повторного исполнения.
- **Python-исходники ASCII-only** - кириллица только в данных (JSON, md).

## С чего начать чтение

- **Новичок** -> `architecture/ARCHITECTURE.md`, потом `procedures/INSTALL.md`.
- **Оператор** -> `procedures/OPERATIONS.md` + `procedures/TROUBLESHOOTING.md`.
- **Агент (LLM в чате)** -> `procedures/BEHAVIOR.md` (обязательно первым).
- **Разработчик** -> `architecture/AUDIT.md` + `architecture/MODULES.md`.

## Текущая версия

- VERSION: 0.1.0-dev
- 21 тест / 0 fail
- JewAI v5, 2026-10-29

