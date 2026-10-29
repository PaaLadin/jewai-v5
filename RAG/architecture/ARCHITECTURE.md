# Архитектура JewAI v5

## Общая схема

```
   [Chat SPA]           [Bridge]              [Agent HTTP]        [Filesystem]
   DeepSeek/Qwen  <-->  Bridge/run.py  <-->  extension/agent.py  <-->  Profiles/<L>/
   (Chrome CDP)         (per-channel)        (per-channel)
                              |
                              v
   [Mainframe 8670]  <--  [config.json]  <--  [Templates/]
   (operator panel)
```

## Слои

### 1. Config (Core/)

- `Core/config.py` - единственный источник правды. Загружает `config.json`.
- Даёт: каналы, порты, пути, thresholds, timeouts.
- Методы: `channel(L)`, `path(*parts)`, `channel_path(L, *parts)`, `channel_config(L)`.

### 2. Bridge (Bridge/)

- `Bridge/cdp.py` - нативный CDP-клиент (WebSocket).
- `Bridge/read.py` - чтение состояния страницы (lastId, content).
- `Bridge/exec.py` - парсер блоков, ops (read/write/run/list/mkdir/hash), replay-guard (Ledger).
- `Bridge/daemon.py` - цикл: poll -> collect -> ledger -> exec -> report.
- `Bridge/run.py` - entrypoint per channel: `python Bridge/run.py --channel C`.

### 3. Adapters (Adapters/)

- Один адаптер на SPA-семейство, не на канал.
- `deepseek.py` (A-D), `qwen.py` (E), `alice.py` (F).
- Селекторы, парсинг блоков, отправка текста - вся SPA-специфика.

### 4. Agent HTTP (Templates/extension/agent.py)

- HTTP-сервер на порту канала (8666+i), X-Token auth.
- `/ping`, `/read`, `/write`, `/list`, `/mkdir`, `/hash`, `/run` (kill-tree).
- safe_path: всё внутри ROOT.

### 5. Mainframe (Mainframe/)

- `server.py` - entrypoint, порт 8670 (из config).
- `web.py` - HTTP + роутинг (stdlib, без Flask).
- `api.py` - status, projects, chat_url, health.
- `controls.py` - meeting, pause_all, fs, logs, roadmap state.
- `launchpad.py` - boot/stop/restart блоков (agent:<L>, chrome:<L>, server).
- `svc_api.py` - API для сервисов (обёртка над Tools/svc.py).
- `council.py` - чат (общий + персональные).
- `static/` - UI (CRT, зелёный на чёрном).

### 6. Rebirth (Rebirth/)

- `table.py` - таблица серий (A -> B -> C...), atomic write.
- `master.py` - оркестратор (gate + lock + run).
- `cycle.py` - реальный CDP-цикл (create_chat -> send_prompt -> verify -> advance).
- `onboard.py` - приветствие новичка от соседа.

### 7. Tools (Tools/)

- `launcher.py` - запуск Chrome для канала (профиль + extension).
- `boot.py` - оркестратор: Mainframe + Chrome + Bridge.
- `gen_launchers.py` - генератор `.ps1` из config.
- `svc.py` - контроллер сервисов (watchdog/recovery/autorestart).
- `watchdog.py` - ALIVE (silence ping).
- `recovery.py` - восстановление панели (F5 без потери черновика).
- `autorestart.py` - глобальный сторож (по ledger + guard).
- `diagnose.py` - быстрый health-отчёт.
- `run_all_tests.py` - прогон всех тестов.
- `doh_proxy.py` - локальный DoH-прокси.
- `installer/` - GUI-инсталлятор (server.py + app.js + install.ps1).

## Потоки данных

### Блок команды (агент -> диск)

```
1. Агент пишет блок в чат DeepSeek.
2. Bridge/daemon читает DOM через CDP (Bridge/read.py).
3. Парсер (Bridge/exec.py) собирает блоки (fence + BEGIN/END).
4. Ledger (replay-guard): проверка id <= watermark, хэш контента.
5. exec: read/write/run/list/mkdir/hash.
6. Отчёт [AGENT REPORT] пишется в чат через адаптер.
```

### Оператор -> агент (kick)

```
1. Оператор пишет в панели (или через API /api/send).
2. Mainframe council.py пушит в chat.jsonl.
3. Если адресовано конкретному каналу - kick через CDP (bridge_kick2/3).
4. Агент читает кик как новое сообщение в своём чате.
```

### ALIVE (watchdog)

```
1. Tools/watchdog.py --channel L (per-channel) в цикле.
2. GET <agent>/ping -> поле ago (сколько секунд назад агент был активен).
3. Если ago >= interval AND state=on -> отправляет ALIVE через kick.
4. Guard: alive_repeat (30 мин), kick fail если textarea busy (оператор печатает).
5. Если оператор отправил - ago сбрасывается, silence_pinged сбрасывается.
```

## Порты (по умолчанию)

| Компонент | Порт |
|---|---|
| Mainframe (панель) | 8670 |
| Installer (GUI) | 8660 |
| doh_proxy | 9899 |
| Agent A | 8666 |
| Agent B | 8667 |
| Agent C | 8668 |
| Agent D | 8669 |
| Agent E | 8671 |
| Agent F | 8672 |
| CDP A | 9122 |
| CDP B | 9123 |
| CDP C | 9124 |
| CDP D | 9125 |
| CDP E | 9126 |
| CDP F | 9127 |

Порты можно менять в инсталляторе (basePort, chatPort, proxyPort).

## Файловая структура

```
C:/JewAI_v5/
  config.json              # главный конфиг
  .agent_token             # X-Token (общий)
  Core/                    # Config
  Bridge/                  # cdp, read, exec, daemon, run
  Adapters/                # deepseek, qwen, alice
  Mainframe/               # server, web, api, council, launchpad, svc_api, static/
  Rebirth/                 # table, master, cycle, onboard
  Tools/                   # launcher, boot, svc, watchdog, recovery, autorestart,
                           # gen_launchers, diagnose, doh_proxy, installer/, launchers/
  Templates/               # extension/, project/, roadmap/, config.*.example.json
  Profiles/
    A/
      chrome/              # Chrome user-data-dir
      config/config.json   # per-channel конфиг
      logs/                # ledger, stale, svc state
      docs/                # PERSONAL, TODO
      extension/           # копия Templates/extension
    B/ ... J/
  Projects/                # проекты (ROADMAP.html)
  logs/                    # общие логи
    JOURNAL.md
    TODO.md
    HANDOVER_*.md
  RAG/                     # эта документация
```

## Главный принцип

**Один Profiles/<L> = весь агент.** Унёс папку - унёс всё: Chrome-профиль,
конфиг, логи, extension, docs. Миграция агента = копирование одной папки.

