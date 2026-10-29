# Операции: запуск, остановка, управление

## Лаунчеры (корень + Tools/launchers/)

Генерируются `Tools/gen_launchers.py` из `config.json`.

| Файл | Что делает |
|---|---|
| `start-all.ps1` | Mainframe + все агенты + все Chrome |
| `stop-all.ps1` | Остановить всё (graceful) |
| `start-<L>.ps1` | Один канал: Chrome + агент |
| `stop-<L>.ps1` | Остановить канал |
| `restart-<L>.ps1` | stop + start канала |
| `server-start.ps1` | Только Mainframe |
| `server-stop.ps1` | Только Mainframe |
| `create-shortcut.ps1` | Ярлык на рабочем столе -> start-all.ps1 |

## Ручной запуск (если лаунчеров нет)

```
cd <Root>
python Tools\boot.py --all           # всё
python Tools\launcher.py --channel C  # только Chrome C
python Bridge\run.py --channel C      # только агент C
python Mainframe\server.py            # только панель
```

## Сервисы (Tools/svc.py)

```
# watchdog (ALIVE) для канала A
python Tools\svc.py start --channel A --kind watchdog --interval 300 --threshold 3

# recovery (F5 при зависании) для канала A
python Tools\svc.py start --channel A --kind recovery --cooldown 300

# autorestart (глобальный сторож)
python Tools\svc.py start --kind autorestart --interval 600

# статус
python Tools\svc.py status
python Tools\svc.py status --channel A

# стоп
python Tools\svc.py stop --channel A --kind watchdog
```

## API панели (8670)

| Метод | Путь | Что |
|---|---|---|
| GET | `/api/health` | ok, ts, matrix (по каналам) |
| GET | `/api/status` | каналы + порты + alive |
| GET | `/api/projects` | список проектов (ROADMAP.html) |
| GET | `/api/roadmap?name=X` | state роадмапа (json) |
| POST | `/api/roadmap` | записать state |
| GET | `/roadmap/<name>` | отдать ROADMAP.html/md |
| GET | `/api/messages` | общий чат |
| POST | `/api/send` | {from, to, text} |
| GET | `/api/chat/<CH>` | персональный чат канала |
| POST | `/api/chat/<CH>` | запись |
| POST | `/api/boot` | {target} (agent:<L>, chrome:<L>, server) |
| POST | `/api/stop` | {target} |
| POST | `/api/restart` | {target} |
| GET | `/api/svc` | статус сервисов |
| POST | `/api/svc` | {channel, kind, action} |
| GET | `/api/llm` | stub |
| GET | `/api/logs?name=chat|agent|svc|server` | хвост лога |
| GET | `/fs/<rel>` | файловый браузер (внутри ROOT) |

## Диагностика

```
python Tools\diagnose.py        # быстрый отчёт
python Tools\run_all_tests.py   # все тесты (~60 сек)
```

## Git

```
cd C:\jewai
git status
git add -A
git commit -m "..."
# push в origin (если настроен)
git push
```

## Регулярные задачи

- Раз в день: `git status`, `git add -A`, `git commit`.
- При изменении config: `python Tools\gen_launchers.py` (регенерация лаунчеров).
- При подозрении на зависание: `python Tools\diagnose.py`, потом `svc.py status`.

