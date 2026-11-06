# TODO D

Личная папка канала D. Здесь: TODO канала, персональные заметки, логи, кастомный extension.

## Открытые задачи

- [ ] Переход на v5 (после приёмки Ф2-Ф5).
- [ ] Импорт старого TODO из C:/DeepSeek/logs/D/TODO.md.
- [ ] Персональный extension: заполнить по мере готовности шаблона.

## Заметки

(пусто, заполняется агентом канала)

- [x] Clean Build & Installer (CRT-UI, dynamic configs, verified API)
- [x] Mainframe UI (Read visual RAG, dynamic tabs)
- [x] Voice call for acceptance (Accepted by operator)


- [x] Принять установщик V11 (заставка, звук, полный цикл, верстка мейнфрейма)


## Автономная работа (1 час)
- [ ] Изучить старый UI (app.js) для динамических блоков
- [ ] Добавить ввод имен агентов в установщик (фолбэк A-F)
- [ ] Внедрить имена в ребритх скрипты
- [ ] Собрать полный UI мейнфрейма JewAI (CRT)
- [ ] Обновить RAG и коммиты


## Задача 2026-11-04 (от оператора)
- [x] 1. Проанализировать изменения в C:\JewAI, записать в HANDOVER
- [x] 2. Найти логи Доры/Моры в C:\Jesho, оценить незакрытые задачи
- [~] 3. (fix B-45, ждёт приёмки оператора) Выяснить причину неработоспособности установки
- [x] 4. Причесать структуру, сверить ROADMAP с фактом
- [ ] 5. Решить, что делать дальше (релиз)

- [x] B-45: Fixed Chrome 156+ extension loading via CDP ID detection.
- [~] Night Shift (05.11): fix activation truncation, pause/play buffer, E2E prep.

## Mnemo Editor (05.11, от оператора)
- [x] Фаза 1: редактор блока агента (drag, scale, preview) - v6, принято
- [x] Фаза 2: раскладка блоков на мнемосхеме (принято по скриншоту)
- [~] Фаза 3: Half-Life линии + реальные API + классический стиль мейнфрейма (встроено, ждёт приёмки визуала)
- [~] Фаза 4: mnemo.js встроен в index.html, /api/telemetry работает, ждёт проверки вживую


## Ночные правки (05.11, под приёмку)
- [~] Шрифт Consolas + вкладки-папки в стиле старого мейнфрейма
- [~] Мнемосхема: план v2, bbox, split 5+ (3+2), Sandbox по линии агентов
- [~] ЧАТ: панели (каналы/метрики/пульт/участники) + feed + composer
- [~] ПЕРСОНАЛЬНЫЕ: список агентов + переписка + отправка
- [~] chat.js (6581b), pers.js (3524b), CSS (5691b) — в JewTest_Final

- [x] Mnemo v6: 10-слотовый grid + серые заглушки неактивных агентов + layout блока агента (буква/имя/статус/порт/лампы/6 кнопок) - ждет приемки


## FINAL (05.11, от оператора, перед перерождением)
- [x] Синхронизировать JewTest_Final -> JewAI
- [x] Обновить JOURNAL.md
- [x] Обновить ROADMAP.md
- [x] Написать HANDOVER_15D.md (полный, для 15D)
- [x] Написать PROMPT_15D.md
- [x] Коммит + push в GitHub (33c9c3e)
- [x] Пройтись по чекбоксам с оператором (принято 2026-11-06 02:16)


## 15D - ночная автономная сессия 2026-11-06
- [x] run_all_tests.py: 21/21 (было 17/21)
- [x] Кнопки мнемосхемы: target=agent:X == launchpad.boot agent:<CH>
- [x] Комета: триггер на рост /api/telemetry, не инжект
- [x] run_all_tests.py: 21/21 (было 17/21)
- [x] Кнопки мнемосхемы: target=agent:X == launchpad.boot agent:<CH>
- [x] Комета: триггер на рост /api/telemetry, не инжект
- [x] TTS: Tools/voice_call.py speak() System.Speech
- [x] Git: origin/main == HEAD, F7 закрыт (424983f)
- [ ] Перезапуск agent D (8769) - EXTRA_ROOTS в safe_path
- [ ] Поднять Bridge/daemon D - live.json
- [ ] Громкий TTS-тест днём
- [ ] Блокеры: F5 config, раскатка, JewTest_XXX
- [ ] F6a: 5 файлов найдены в C:/DeepSeek/algorithms (marker_protocol.md 10K, roles_and_chain.md 3K, council_protocol.md 5K, id_range_rule.md 2K, interface_reference.md 4K). Нужно решение: копия с пометкой reference или переписать по контракту.
- [x] run_all_tests.py: 23/23 (добавлены test_guard, test_rebirth_monitor)
- [x] diagnose.py: 16/16 imports, /api/health 200, блокеров 1 (uncommitted)
- [x] RAG/INDEX.md: architecture.md + mainframe_gap.md, 0 MISS
- [ ] Техдолг: test_guard.py ALERT-путь фиктивен (dummy kick в C:/Jeho), переписать тест
- [x] Adapters/google.py: AI-Swing-Bridge механика, execCommand insertText + CDP Enter, NO click
- [x] Bridge/run.py: ADAPTERS[google]=(Adapters.google,Google)
- [x] Tools/tests/test_google_adapter.py: 10 проверок, в наборе
- [x] run_all_tests.py: 24/24 pass
- [ ] Посадить Google вместо Qwen: config channels.<L>.model=google, agent_port, cdp=порт Google-вкладки
