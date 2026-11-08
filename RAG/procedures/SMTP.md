# SMTP (email) - настройка

## Где хранится

`.secret/smtp.json` — НЕ в config.json (config в git → пароль утёк бы).

## Формат

    {
      "smtp_host": "smtp.yandex.ru",
      "smtp_port": 465,
      "from_addr": "you@yandex.ru",
      "password": "<app-password>",
      "to_addr": "operator@example.com",
      "use_tls": true
    }

## Как создать

1. Скопировать `Templates/.secret/smtp.example.json` в `.secret/smtp.json`.
2. Заполнить реальными значениями.
3. Проверить через `mail.status()`.

## Провайдеры

- Yandex: smtp.yandex.ru:465 SSL, пароль приложения (не основной).
- Gmail: smtp.gmail.com:587 STARTTLS, App Password (нужен 2FA).
- Mail.ru: smtp.mail.ru:465 SSL.

## Для оператора

- При инсталляции SMTP не спрашивается (TODO: добавить в installer).
- Настраивается вручную после запуска.
- Файл: <root>/.secret/smtp.json (рядом с github_token).

## Для агентов

- Отправка: POST /api/mail/send {"subject":"...","body":"..."} на 8670.
- Проверка: GET /api/mail → {configured, source}.
- НЕ логировать пароль. НЕ печатать .secret/smtp.json.

## Безопасность

- .secret/ в .gitignore — не коммитить.
- Пароль попал в git — сменить + git filter-repo.

## Изменения 9C (2026-11-09)

- config.json убран из git (git rm --cached), добавлен в .gitignore.
- Mainframe/mail.py: читает .secret/smtp.json, fallback на config.mail (legacy).
- Templates/.secret/smtp.example.json — пример.