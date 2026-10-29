# Установка JewAI v5 с нуля

## Требования

- Windows 10/11 (x64).
- Python 3.12 (install.ps1 сам предложит скачать, если нет).
- Google Chrome (install.ps1 сам предложит скачать, если нет).
- Свободные порты: 8660 (installer), 8666-8675 (агенты), 8670 (панель),
  9899 (doh_proxy), 9122-9131 (CDP).

## Шаг 1. Запуск инсталлятора

```
C:\jewai\Tools\installer\install.bat
```

или напрямую:

```
powershell -NoProfile -ExecutionPolicy Bypass -File C:\jewai\Tools\installer\install.ps1
```

Что делает install.ps1:

1. Проверяет Python. Если нет - предлагает скачать (python.org, тихая установка).
2. Проверяет Chrome. Если нет - предлагает скачать (dl.google.com, тихая установка).
3. Запускает локальный HTTP-сервер на **8660** (GUI-инсталлятор).
4. Открывает браузер на http://127.0.0.1:8660.

## Шаг 2. Заполнить поля в GUI

| Поле | Что | Пример |
|---|---|---|
| Root | Целевая папка | `C:\JewAI_v5_test_20261029` |
| Base port | Порт первого агента (A) | `8666` |
| Agent count | Сколько агентов (1-10) | `2` (для теста) или `4` |
| Chat port | Порт панели | `8670` |
| Proxy port | Порт doh_proxy | `9999` или `9899` |
| Names | Имена через запятую | `Arkady, Boris` |

## Шаг 3. Install

Инсталлятор:

1. Копирует проект (`copytree`) в Root.
2. Создаёт `Profiles/<L>/{chrome,config,logs,docs,extension}` для каждого канала.
3. Копирует `Templates/extension` в `Profiles/<L>/extension`.
4. Инициализирует Chrome-профиль (2 сек, `--load-extension`, `--hide-crash-restore-bubble`).
5. Пишет `config.json` (главный) и `Profiles/<L>/config/config.json` (per-channel).
6. Генерирует `Tools/launchers/*.ps1` (start/stop/restart per channel + server + shortcut).
7. Создаёт `.agent_token` (если нет).
8. Пишет `install.log` в Root.

**Ничего не запускает** (только Install). Логи: `<Root>/install.log`.

## Шаг 4. Launch

Кнопка Launch (POST /api/launch) или вручную:

```
cd C:\JewAI_v5_test_20261029
powershell -NoProfile -ExecutionPolicy Bypass -File Tools\launchers\start-all.ps1
```

Что поднимается:

1. `Tools/doh_proxy.py` (порт 9999/9899).
2. `Mainframe/server.py` (порт 8670).
3. `Bridge/run.py --channel L` для каждого канала.
4. `Tools/launcher.py --channel L` для каждого канала (Chrome + extension + push storage).

## Шаг 5. Проверка

```
http://127.0.0.1:8670/api/health
http://127.0.0.1:8670/api/status
```

Ожидаемо: `{"ok": true, ...}`, status - все каналы, каждый с `agent_alive` и `cdp_alive`.

## Шаг 6. Первый чат

1. Откройте Chrome каждого канала (откроется на `https://chat.deepseek.com`).
2. Залогиньтесь (один раз, сохранится в `Profiles/<L>/chrome`).
3. Панель -> ПУЛЬТ -> блоки A/B/C/D -> проверьте индикаторы.
4. Если CDP не поднялся - `Tools/launchers/restart-<L>.ps1`.

## Откат / удаление

Просто удалите целевую папку. Все данные (профили, конфиги, логи) внутри неё.

## Что если install.ps1 упал

- Смотреть `<Root>/install.log`.
- Частые причины: порт 8660 занят, нет прав на запись в Root, Chrome не установился.
- Подробнее - `procedures/TROUBLESHOOTING.md`.

