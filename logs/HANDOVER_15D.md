# HANDOVER 14D -> 15D

**Дата:** 2026-11-05 (ночь). **Канал:** D.
**14D:** DDAB4000-DDAB4999. **15D:** DDAB5000+

## Контекст

13D оборвался ~28.10. Работали 7C, 8C, 10B, 11B, Мора/Дора.
14D подхватил 04.11, в ночь 05.11 сделал UI-блок целиком.

## Инфраструктура (B-45 и фиксы)

- **B-45 (Chrome 156+):** заблокирован --load-extension для unpacked, Ext ID больше не из хеша пути.
  Fix в Tools/launcher.py: _get_loaded_ext_id (CDP chrome://extensions shadow DOM),
  _open_ext_sidepanel (будит SW), _push_storage (awaitPromise).
- **send_text:** CDP.call(Input.insertText) вместо JS-setter (React резал 9KB).
  Проверка textarea.value перед вставкой, если занято -> False.
- **Pause buffer:** daemon._send_or_buffer -> outbox_CH.jsonl на busy.
- **Telemetry:** cfg.channel_path (было cfg.path, count=0).

## Инфраструктура (B-45 и фиксы)

- **B-45 (Chrome 156+):** заблокирован --load-extension для unpacked, Ext ID больше не из хеша пути.
  Fix в Tools/launcher.py: _get_loaded_ext_id (CDP chrome://extensions shadow DOM),
  _open_ext_sidepanel (будит SW), _push_storage (awaitPromise).
- **send_text:** CDP.call(Input.insertText) вместо JS-setter (React резал 9KB).
  Проверка textarea.value перед вставкой, если занято -> False.
- **Pause buffer:** daemon._send_or_buffer -> outbox_CH.jsonl на busy.
- **Telemetry:** cfg.channel_path (было cfg.path, count=0).

## Мнемосхема (JewAI/Mainframe/static/mnemo.js)

- Inline в index.html (внешний /mnemo.js не отдавался через web.py — 404, web.py имеет whitelist).
- 10-слотовый grid (A/B/C/D/E/F/J/H/K/L). Активные — из agentOrder (/api/status).
- Неактивные — серые заглушки SLOT X: opacity 10%, z-index 1, pointer-events none.
- Размеры: agent 308x154 (x1.4), mainframe 560x240 (x2), control 262x140 (x1.75), resource 210x80.
- Карточка агента (k=0.51 от редактора 600x320): буква 56px, имя 28px, статус 18px, порт 17px, лампы 14px, кнопки reb 14px, main 18px.
- Комета Tron: A* по grid 10px, 20% линия ЗА точкой, точка 100%, хвост 0.5с, вспышка 2с. Проверено: read->rag, write->sandbox.

## Чаты (chat.js и pers.js)

- **ЧАТ:** левая панель КАНАЛЫ / МЕТРИКИ / ПУЛЬТ / УЧАСТНИКИ.
  Правая: feed + composer с микрофоном (Web Speech API ru-RU) и кнопкой >_.
  Поллинг /api/messages 1.5с. Отправка /api/send.
  Кнопки: СОВЕЩАНИЕ / ПАУЗА ВСЕМ / ПРОДОЛЖИТЬ / ОЧИСТИТЬ.
- **ПЕРСОНАЛЬНЫЕ:** список каналов слева, переписка справа.
  Поллинг /api/chat/CH 3с. Отправка POST /api/chat/CH.
- Glow на тексте, стрелка > мигает (promptBlink 1.2с).

## Чаты (chat.js и pers.js)

- **ЧАТ:** левая панель КАНАЛЫ / МЕТРИКИ / ПУЛЬТ / УЧАСТНИКИ.
  Правая: feed + composer с микрофоном (Web Speech API ru-RU) и кнопкой >_.
  Поллинг /api/messages 1.5с. Отправка /api/send.
  Кнопки: СОВЕЩАНИЕ / ПАУЗА ВСЕМ / ПРОДОЛЖИТЬ / ОЧИСТИТЬ.
- **ПЕРСОНАЛЬНЫЕ:** список каналов слева, переписка справа.
  Поллинг /api/chat/CH 3с. Отправка POST /api/chat/CH.
- Glow на тексте, стрелка > мигает (promptBlink 1.2с).

## Чаты (chat.js и pers.js)

- **ЧАТ:** левая панель КАНАЛЫ / МЕТРИКИ / ПУЛЬТ / УЧАСТНИКИ.
  Правая: feed + composer с микрофоном (Web Speech API ru-RU) и кнопкой >_.
  Поллинг /api/messages 1.5с. Отправка /api/send.
  Кнопки: СОВЕЩАНИЕ / ПАУЗА ВСЕМ / ПРОДОЛЖИТЬ / ОЧИСТИТЬ.
- **ПЕРСОНАЛЬНЫЕ:** список каналов слева, переписка справа.
  Поллинг /api/chat/CH 3с. Отправка POST /api/chat/CH.
- Glow на тексте, стрелка > мигает (promptBlink 1.2с).

## Что делать 15D

1. **E2E через живой AI:** команда в DeepSeek -> мост -> исполнение. Проверялся только прямой HTTP к agent.py.
2. **Кнопки мнемосхемы:** target=agent:X, инспектировать ответ launchpad.boot. Возможно нужен префикс agent: или отдельный handler.
3. **Комета на реальных операциях** (не инжект в live.json): запустить агента A, отправить задачу в чат, смотреть полёт.
4. **TTS-вызов оператора** (Windows System.Speech): не реализовано в новой сборке.
5. **Прогнать run_all_tests.py** — 21/21 после B-45 не проверялось.
6. **F5c/F5d/F6a-c:** export_share, handover, протоколы — не начато.
7. **Push в GitHub** (F7): 14D закоммитил локально, push не делал.

## Грабли (проверены на своей шкуре)

1. **op=write > 200b теряет тело.** Крупные файлы: staging-файл + чтение через python -c, или массив строк в op=run.
2. **CDP websocket требует suppress_origin=True.** Chrome 111+ отдаёт 403 без него.
3. **CSS-версия в index.html:** style.css?v=X. Иначе браузер держит старый файл, правки не видны.
4. **web.py whitelist:** новый .js не отдаётся (404). Inline в index.html или добавить в STATIC_EXTS.
5. **\n в cmd ломается.** Использовать chr(10) в python -c.
6. **Python-исходники ASCII-only** (кириллица в docstring ломает op=write).
7. **Replay stale:** водяной знак + хэш в файле (см. AUDIT §29).
8. **Chrome 156+:** --load-extension игнорируется для unpacked, ID не из хеша.

## Состояние на момент передачи

- Git: локальные коммиты 773ea5d, 3198d71, ddd2a54, f5dec41, e6042da. Push не делался.
- JewAI = JewTest_Final по static/ и Mainframe/ (побайтово).
- Тестовая установка: C:\JewTest_Final, mainframe 8710, agent A 8700, cdp 9122.
- Watchdog D: ON (оставить до приёмки 15D).

## Правила (кратко)

- C:\DeepSeek - песочница 14D. C:\JewAI - чистовик. Тест - C:\JewTest_XXX.
- Python-исходники ASCII-only. Markdown фенсы через chr(96)*3.
- Стоп-слово: два слова подряд (см. behavior_rules §6).

Dixi. 14D, 2026-11-05 (ночь).
