# Модули JewAI v5

Автогенерация из реального дерева файлов. Размеры/строки - факт.

## Core

| Файл | Размер | Строк |
|---|---|---|
| `Core/__init__.py` | 0 b | 0 |
| `Core/config.py` | 4099 b | 118 |

## Bridge

| Файл | Размер | Строк |
|---|---|---|
| `Bridge/__init__.py` | 0 b | 0 |
| `Bridge/cdp.py` | 4067 b | 108 |
| `Bridge/daemon.py` | 7151 b | 180 |
| `Bridge/exec.py` | 9031 b | 277 |
| `Bridge/read.py` | 2941 b | 79 |
| `Bridge/run.py` | 2445 b | 84 |

## Adapters

| Файл | Размер | Строк |
|---|---|---|
| `Adapters/__init__.py` | 0 b | 0 |
| `Adapters/alice.py` | 3898 b | 95 |
| `Adapters/base.py` | 1287 b | 33 |
| `Adapters/deepseek.py` | 4085 b | 96 |
| `Adapters/qwen.py` | 5550 b | 132 |

## Mainframe

| Файл | Размер | Строк |
|---|---|---|
| `Mainframe/__init__.py` | 0 b | 0 |
| `Mainframe/api.py` | 3849 b | 110 |
| `Mainframe/controls.py` | 4516 b | 123 |
| `Mainframe/council.py` | 4844 b | 146 |
| `Mainframe/health.py` | 5693 b | 176 |
| `Mainframe/launchpad.py` | 8355 b | 232 |
| `Mainframe/llm.py` | 2852 b | 76 |
| `Mainframe/mail.py` | 1904 b | 56 |
| `Mainframe/rag_channel.py` | 1812 b | 55 |
| `Mainframe/server.py` | 3526 b | 65 |
| `Mainframe/svc_api.py` | 2907 b | 80 |
| `Mainframe/web.py` | 6159 b | 145 |

## Rebirth

| Файл | Размер | Строк |
|---|---|---|
| `Rebirth/__init__.py` | 0 b | 0 |
| `Rebirth/cycle.py` | 6199 b | 158 |
| `Rebirth/master.py` | 5479 b | 155 |
| `Rebirth/onboard.py` | 1621 b | 40 |
| `Rebirth/table.py` | 3999 b | 119 |

## Tools

| Файл | Размер | Строк |
|---|---|---|
| `Tools/__init__.py` | 0 b | 0 |
| `Tools/autorestart.py` | 6334 b | 178 |
| `Tools/boot.py` | 5433 b | 151 |
| `Tools/diagnose.py` | 4033 b | 125 |
| `Tools/doh_proxy.py` | 4946 b | 165 |
| `Tools/gen_launchers.py` | 7750 b | 155 |
| `Tools/launcher.py` | 6369 b | 171 |
| `Tools/recovery.py` | 4301 b | 129 |
| `Tools/run_all_tests.py` | 2568 b | 65 |
| `Tools/svc.py` | 7892 b | 218 |
| `Tools/watchdog.py` | 5164 b | 139 |

## Mainframe/static

| Файл | Размер |
|---|---|
| `app.js` | 5216 b |
| `app_audio.js` | 6105 b |
| `index.html` | 1545 b |
| `index.html.bak_11b` | 2745 b |
| `style.css` | 2697 b |

## Templates

- `Templates/extension/` - extension v5.0.0 (manifest, content_*.js, sidepanel.html, agent.py).
- `Templates/project/` - скелет нового проекта (README, ROADMAP.md, TODO.md, src/, docs/, tests/).
- `Templates/roadmap/` - шаблоны роадмапа (ROADMAP.template.html, ROADMAP.template.md).
- `Templates/config.llm.example.json`, `config.mail.example.json` - примеры конфигов.

## Тесты

Всего: 21 файлов.

Запуск: `python Tools/run_all_tests.py` (вывод в `logs/runtime/_v5_all_tests.txt`).

