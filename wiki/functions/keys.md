---
title: Ключи и токены
tags: [безопасность, токены, ключи]
related: [functions/install]
updated: 2026-11-09
---

# Ключи и токены

## Где лежат

- `config.json` — порты, каналы, имена (не коммитится, в .gitignore)
- `.agent_token` — токен агента, генерируется при install
- `.secret` — секретные ключи (SMTP, API)
- `Profiles/<L>/config/config.json` — конфиг агента

## Правила

- **Секреты НЕ в git.** Проверено `.gitignore`.
- Токен один на install (root), не per-channel.
- При смене токена — рестарт всех агентов.

## См. также

- [[functions/install]]