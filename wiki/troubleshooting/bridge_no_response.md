---
title: Мост не отвечает
tags: [мост, agent-report]
related: [functions/bridge]
updated: 2026-11-09
---

# Мост не отвечает

Симптом: отправил блок, `[AGENT REPORT]` не приходит.

## Проверки

1. **Агент /ping** — `curl http://127.0.0.1:8680/ping`. Если нет — Chrome не запущен.
2. **Формат блока** — открывающая строка, `id/op/path` каждый на своей строке,
   закрывающая. Лишние теги (`tool_call`, `result`) — мост не парсит.
3. **Токен** — `.agent_token` в корне совпадает у агента и моста.
4. **Префикс id** — должен соответствовать каналу.

## Если ничего не помогло

Reload extension: `chrome://extensions/` → JewAI → Reload.

## См. также

- [[functions/bridge]]
- [[functions/keys]]