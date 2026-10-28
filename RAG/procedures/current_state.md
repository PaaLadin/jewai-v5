# Current state (13D -> 14D, final)

## Готово

F0, F1, F2, F3 (mainframe P0+P1), F4 (CDP cycle), F5 (llm/mail/rag stubs + doh_proxy),
extension, layout. 21 тест, 325 проверок.

## Частично

F5 real config: нужны llm host:port и mail password (шаблоны в Templates/config.*.example.json).

## Откат / план

F6 (Chrome A/B/D/E/F потушены, C активен). F7 (push не выполнялся).

## Структура

Profiles (browser) / Agents (personal) / Templates (source).

## Не делать без ОК

Спавнить агентов. Писать в живой чат C. Push в GitHub. Убивать чужие процессы.
