# ADAPTERS - адаптеры моделей в JewAI v5

Актуально 2026-11-09 (9C).

## deepseek (A-D, основной)

- Файл: `Adapters/deepseek.py`
- Host: `chat.deepseek.com`
- Дом: React SPA, `textarea[placeholder]`
- Блоки: в `pre`/`code`, парсинг `Bridge/exec.py::parse_blocks`
- Маркер BEGIN/END (с пробелами и без) ловится через `nl->_nl`
- Тройной Enter fix (иногда 2 прохода)

## qwen (E)

- Файл: `Adapters/qwen.py`
- Host: `chat.qwen.ai`
- Дом: Qwen SPA, React `_valueTracker`
- `_valueTracker.setValue('')` ОБЯЗАТЕЛЕН, иначе React не видит вставку
- Один Enter (двойной ломает)

## alice (F)

- Файл: `Adapters/alice.py`
- Host: `alice.yandex.ru`
- Дом: `.AliceInput-Textarea_clone`
- Send: кнопка, НЕ Enter
- Программный ввод ненадёжен (attach файла отбит)

## google (каркас, не в проде)

- Файл: `Adapters/google.py` (5607 b)
- Host: `google.com` (AI Mode)
- Два textarea: `role=textbox` (скрытый) + видимый AI Mode
- Вставка: `document.execCommand("insertText")`, НЕ setter
- Submit: CDP `Input.dispatchKeyEvent` VK13 keyDown+keyUp, не искать send-кнопку (открывает sidepanel)
- Reply DOM: `DIV.pWvJNd` (ACK), parent `DIV.Zkbeff`, запрос `H3.iMqumd`
- Надёжный парсинг: `document.body.innerText` + `parse_blocks`
- Проверено 2026-11-06: execCommand + CDP Enter, сообщение ушло, ACK получен

## Смена адаптера

- UI: Mainframe 8670, кнопка-шестерёнка в topbar
- API: `GET/POST /api/settings {channel, model}`
- Руками: `config.json channels.<L>.model` + рестарт Bridge канала
- Применение: `Bridge/run.py::_adapter_for(model)` при старте

## Добавить новый

1. `Adapters/M.py`: класс с `HOST` + `collect_blocks`/`send_text`/`new_chat`/`verify_prompt_hits`
2. `Bridge/run.py::ADAPTERS[M] = (Adapters.M, M)`
3. `Mainframe/settings.py::VALID_ADAPTERS += M`
4. `config.json channels.<L>.model = M`
5. Тест: `python Bridge/run.py --channel A --once`

## Ограничения

- qwen не работает на deepseek-адресе
- alice не принимает программный ввод
- google требует Google login и отдельный Chrome-профиль
- Если адаптер указан, но вкладка не на нужном HOST - daemon не найдёт target, будет reconnect loop. Открыть вкладку вручную.

## Связанное

- `RAG/architecture/ARCHITECTURE.md` §3 Adapters
- `Bridge/run.py::_adapter_for`
- `Mainframe/settings.py`
- `Templates/extension/manifest.json` (host_permissions)