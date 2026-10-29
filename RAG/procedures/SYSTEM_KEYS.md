# Ключи, токены, порты, env

## Файлы с секретами

| Файл | Что | Кто создаёт |
|---|---|---|
| `<Root>/.agent_token` | X-Token (общий на все каналы) | Installer (если нет) |
| `<Root>/config.json` | **НЕ секрет**, конфиг | Installer |
| `Templates/config.llm.example.json` | шаблон LLM (host:port) | Templates |
| `Templates/config.mail.example.json` | шаблон SMTP | Templates |

## X-Token (`.agent_token`)

- Генерируется один раз при установке: `secrets.token_urlsafe(32)`.
- Один на всё приложение (не per-channel).
- Передаётся в заголовке `X-Token` при вызовах `/read`, `/write`, `/run`, `/ping`.
- Читается из `<Root>/.agent_token`.
- **Не коммитится в git** (`.gitignore`).
- Не переносится при установке (installer ignore_patterns).

## Env-переменные

| Переменная | Что | Значение по умолчанию |
|---|---|---|
| `JEWAI_CONFIG` | Путь к config.json | `<Core>/../config.json` |
| `JEWAI_ROOT` | Root для `Templates/extension/agent.py` | `__file__/../..` |

`JEWAI_CONFIG` выставляется лаунчерами и инсталлятором при каждом spawn.

## Порты (из config.json)

| Поле config | Что | Пример |
|---|---|---|
| `chat_port` | Mainframe | 8670 |
| `doh_proxy_port` | DoH-прокси | 9899 |
| `channels.<L>.agent` | HTTP-агент канала | 8666 (A), 8667 (B)... |
| `channels.<L>.cdp` | CDP-порт Chrome | 9122 (A), 9123 (B)... |

## Поля config.json

```
{
  "root": "C:\\JewAI",
  "bind": "127.0.0.1",
  "chat_port": 8670,
  "doh_proxy_port": 9899,
  "letters": ["A", "B", "C", "D"],
  "channels": {
    "A": {
      "name": "Arkady",
      "agent": 8666,
      "cdp": 9122,
      "prefix": "AAAA",
      "extension": "Profiles/A/extension",
      "model": "deepseek"
    }
  },
  "thresholds": {"rebirth_cmds": 850},
  "timeouts": {"cdp": 5, "poll_ms": 2000, "stable_ms": 1200},
  "version": "0.1.0-dev"
}
```

## Per-channel config (`Profiles/<L>/config/config.json`)

```
{
  "channel": "A",
  "name": "Arkady",
  "prefix": "AAAA",
  "agent_port": 8666,
  "cdp_port": 9122,
  "agent_url": "http://127.0.0.1:8666",
  "extension": "Profiles/A/extension",
  "model": "deepseek",
  "root": "C:\\JewAI",
  "chat_port": 8670
}
```

## chrome.storage.local (per Chrome profile)

Записывается автоматически `Tools/launcher.py` через CDP после старта Chrome:

```
{
  "agentUrl": "http://127.0.0.1:8666",
  "token": "...",
  "channel": "A",
  "name": "Arkady"
}
```

Если storage пустой - `sidepanel.html` сам определяет порт
перебором 8666-8675 (auto-detect).

## Что НЕ в git (через .gitignore)

- `.agent_token`
- `Profiles/`, `logs/`, `runtime/`, `Archive/`, `backups/`, `media/`
- `__pycache__/`, `*.pyc`, `*.bak_*`

