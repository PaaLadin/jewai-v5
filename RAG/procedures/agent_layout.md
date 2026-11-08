# Agent layout - где что лежит (v5)

## Структура

```
C:/JewAI/
  Templates/extension/       <- эталон
  Agents/<L>/extension/      <- копия для канала
  Profiles/<L>/              <- Chrome user-data
  Core/ Bridge/ Adapters/ Mainframe/ Rebirth/ Tools/
```

## Три пути

| Путь | Что |
|---|---|
| Templates/extension/ | эталон, источник |
| Agents/<L>/extension/ | копия для канала (кастомизация) |
| Profiles/<L>/ | данные Chrome, НЕ трогать |

## Chrome загружает extension откуда?

--load-extension=Agents/<L>/extension. НЕ из Templates, НЕ из Profiles.

## Синхронизация

1. Правим Templates/extension/file.
2. Копируем в Agents/<L>/extension/file.
3. Reload extension (chrome://extensions -> Reload) или рестарт Chrome.

Скрипта синка в v5 нет. TODO: Tools/sync_extension.py.

## Extension vs Bridge

ОБА есть в v5:
- Extension (JS в браузере): парсит DOM, шлёт в agent.py.
- Bridge (Python): альтернатива через CDP.

Конфликт: если оба активны - двойная отправка. Либо один, либо другой.
