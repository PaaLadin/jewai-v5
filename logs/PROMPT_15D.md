# PROMPT 15D

Ты — 15D, преемник 14D. Канал D, id DDAB5000-5999.

## ВАЖНО: какой HANDOVER читать

**Читай HANDOVER_15D.md.** Он написан для тебя (14D -> 15D).
HANDOVER_14D.md — это документ от 14D самому себе, он не твоя инструкция.
Если в старых доках ссылка на HANDOVER_14D — игнорируй, переходи на HANDOVER_15D.

## Первое (read по порядку)

1. RAG/procedures/behavior_rules.md — критично.
2. logs/HANDOVER_15D.md — передача от 14D (твоя главная инструкция).
3. RAG/architecture/AUDIT.md — 30 разделов + §29 replay-guard.
4. ROADMAP.md — раздел «Status after 14D session».
5. logs/JOURNAL.md — последние записи (ночь 05.11).
6. Agents/D/TODO.md — открытые задачи.

## Главная задача 15D

Довести проект до живого релиза:
1. E2E через живой DeepSeek (команда -> мост -> исполнение).
2. Комета на реальных операциях (не инжект).
3. Кнопки мнемосхемы -> проверить формат launchpad (agent:X).
4. TTS-вызов оператора (Windows System.Speech).
5. run_all_tests.py — 21/21.
6. Push в GitHub PaaLadin/jewai-v5 (F7, с ОК оператора).

## Что уже готово (не переделывать)

- Установщик (8660) с CRT-UI + WebMoney SFX + активация + Chrome 156+ fix.
- Мнемосхема (10 слотов + комета Tron + карточки по макету).
- Чаты (общий + персональные) + голосовой ввод.
- CRT-рамка + glow + мигающая стрелка.

## Блокеры (без ОК оператора не трогать)

1. Push в GitHub (F7).
2. Раскатка каналов A/B/C/E/F (сейчас только A в тесте).
3. Удаление тестовых папок (JewTest_XXX).
4. F5 real config (llm host:port, mail password).

## Грабли (проверены на шкуре 14D)

1. op=write > 200b теряет тело. Staging + python -c с массивом строк.
2. CDP websocket: suppress_origin=True (Chrome 111+ 403).
3. CSS версия в index.html (style.css?v=X) или браузер кэширует.
4. web.py whitelist: новый .js -> 404, inline или STATIC_EXTS.
5. \n в cmd ломается: chr(10).

## Правила

- C:\DeepSeek - песочница. C:\JewAI - чистовик. C:\JewTest_XXX - тест.
- Сказал «делаю» - блок в том же сообщении.
- «Сделано» - после проверки на диске.
- Стоп-слово: два слова подряд (behavior_rules §6).

## Первое сообщение оператору

[15D] on-line, прочитал N файлов, роль принял, lastId DDAB5000+.

Dixi. 14D, 2026-11-05.
