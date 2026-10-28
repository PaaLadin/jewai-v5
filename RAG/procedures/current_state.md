# Current state (13D -> 14D, final)

## Готово

F0, F1, F2, F3 (mainframe P0+P1), F4 (CDP cycle + tests), F5 partial (stubs+doh_proxy),
extension, layout. 21 тест, 325 проверок.

## Частично

F5: real config (llm host:port, mail password). Шаблоны в Templates/*.example.json.

## Откат / план

F6: Chrome A/B/D/E/F потушены, активен C (9124). Агенты не запускались.
F7: git 2 коммита, push не выполнялся.

## Структура

Profiles (browser) / Agents (personal) / Templates (source).
Core/, Bridge/, Adapters/, Mainframe/, Rebirth/, Tools/.

## Не делать без ОК

1. Спавнить агентов Bridge/run --channel.
2. Писать в живой чат C.
3. Push в GitHub.
4. Убивать чужие процессы.
5. Раскатывать A/B/D/E/F не по одному.
