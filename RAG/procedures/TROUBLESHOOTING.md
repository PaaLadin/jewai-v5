# Починка типовых поломок

## Быстрая диагностика

```
python Tools\\diagnose.py
python Tools\\run_all_tests.py
python Tools\\svc.py status
```

## Панель не отвечает

1. Порт занят? `netstat -ano | findstr 8670`
2. `Get-Process pythonw` - есть Mainframe?
3. `python Mainframe\\server.py` вручную.
4. Логи: `logs/svc/*.log`.

## Панель открывается, но всё серое

1. `/api/status` вручную - отдаёт JSON?
2. F5.
3. Если нет - Mainframe упал, смотреть консоль.

## Агент не отвечает на /ping

1. `http://127.0.0.1:8666/ping` - refused?
2. `Tools/launcher.py --channel A` - Chrome поднят?
3. `Bridge/run.py --channel A` - агент запущен?
4. Порт занят? `netstat -ano | findstr 8666`.
5. `svc.py status --channel A`.

## Chrome не открывается / CDP refused

1. Chrome установлен? `where chrome`.
2. Порт 9122 занят? `netstat -ano | findstr 9122`.
3. Сироты: `Get-Process chrome | Where-Object { $_.CommandLine -like "*Profiles\\A*" } | Stop-Process -Force`.
4. Профиль повреждён: `rm -r Profiles\\A\\chrome` (при остановленном Chrome).

## Extension не грузится

1. `chrome://extensions` -> включён?
2. `--load-extension` в `Tools/launcher.py`?
3. Storage: `agentUrl` записан?
4. Вручную: sidepanel -> URL + Token -> Save + ping.

## Агент зависает

1. `python Tools\\diagnose.py` - что красное?
2. Ledger: `Profiles/<L>/logs/ledger_<L>.json`.
3. `svc.py status --channel L`.
4. Recovery: `svc.py start --channel L --kind recovery`.

## ALIVE перебивает черновик

**В v5 этого не должно быть.** Проверка:

1. `Tools/watchdog.py` - `_kick` с проверкой textarea?
2. `_operator_typing` в `recovery.py` - `busy` -> SKIP.
3. Временно: `svc.py stop --channel L --kind watchdog`.

## Recovery делает F5 при печати

1. `Tools/recovery.py` - `_operator_typing`?
2. Временно: `svc.py stop --channel L --kind recovery`.

## Autorestart ребутит при беседе

1. `Tools/autorestart.py` - `_operator_typing` guard?
2. Временно: `svc.py stop --kind autorestart`.

## Порт 8660 (installer) занят

1. `netstat -ano | findstr 8660` -> PID.
2. `Stop-Process -Id <PID> -Force` (если старый installer).

## Инсталлятор падает

1. `<Root>/install.log`.
2. `Tools/installer/server.py` вручную (без pythonw) - консоль.
3. Причины: нет Python, нет Chrome, нет прав.

## UI показывает «6 channels», а конфиг другой

1. F5.
2. `config.json -> letters`?
3. `Profiles/<L>/config/config.json` - для всех L?

## Совсем всё сломалось

1. `git log --oneline -5` - на каком коммите.
2. `git diff HEAD` - что ушло.
3. `git stash` (сохранит modified).
4. Если совсем плохо - переустановка через `install.ps1`.

## Логи: где смотреть

| Файл | Что |
|---|---|
| `<Root>/install.log` | Лог установки |
| `<Root>/logs/JOURNAL.md` | Журнал |
| `<Root>/logs/TODO.md` | TODO |
| `<Root>/logs/HANDOVER_*.md` | Передача |
| `<Root>/logs/runtime/_v5_all_tests.txt` | Тесты |
| `<Root>/logs/svc/autorestart.log` | Autorestart |
| `Profiles/<L>/logs/ledger_<L>.json` | Replay-guard |
| `Profiles/<L>/logs/stale_<L>.log` | Stale |

