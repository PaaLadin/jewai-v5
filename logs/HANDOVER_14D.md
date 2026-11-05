# HANDOVER 14D -> 15D

**Дата:** 2026-11-04
**Канал:** D (14D, DDAB4000+)
**Предшественник:** 13D (DDAB3000-3999), оборвался ~28.10.2026
**Смена поколений:** A/B/C/D отключались (нестабильность), работу продолжили 7C, 8C, 10B, 11B, Мора и Дора (из C:\Jeho).

## Что было до 14D (эпоха 7C-11B)

- Ф1 (Аудит) и Ф2 (Мост) завершены, AUDIT 30 разделов.
- Ф3-F7 (Mainframe, Rebirth, надстройки, раскатка, GitHub) - частично.
- Создан установщик (Tools/installer) в CRT-стиле с WebMoney-заставкой.
- 7C: починены extension-sidepanel, launcher, agent.py. Ветка B-xx фиксов (B-04..B-44).
- 8C: работа с CfT (Chrome for Testing), kill Chrome before copy (B-35), same-dir install (B-42).
- 11B: правки после коллапса 13D, фокус на installer + docs.
- 10B: behavior_rules.md, marker_protocol.
- Мора/Дора (C:\Jeho): попытка полной переустановки с CfT, чистка Templates/extension, sync_20261104.

## Что сделал 14D (04.11.2026)

### Разведка
- Восстановил контекст: C:\DeepSeek (песочница), C:\JewAI (чистовик), C:\Jeho (тест Моры), C:\JewTest_Audit (мой тест).
- Прочитал install.log из C:\Jeho - установка там проходила успешно.
- Нашел: C:\Jesho не существует, есть C:\Jeho (буква h).

### Критические фиксы (B-45)
- **Порт установщика:** 8671 -> **8660** (потому что 8671 отдан агенту E). См. Tools/installer/server.py строка 5.
- **Chrome 156+ блокирует load-extension** для unpacked-расширений. Симптом: sidepanel не открывается, расширение не загружается.
- **Chrome 156+ не вычисляет Ext ID из хеша пути** (старая формула sha256(path)[:32] -> a-p больше не работает). ID генерируется случайно и хранится в профиле.
- **Решение в launcher.py:**
  - `_get_loaded_ext_id(cdp_port)`: открывает chrome://extensions через CDP, читает shadow DOM, вытаскивает реальный ID.
  - `_open_ext_sidepanel(cdp_port)`: после получения ID открывает chrome-extension://<id>/sidepanel.html, чтобы разбудить Service Worker.
  - `_push_storage`: добавлен awaitPromise=True и try/catch внутри JS, диагностика через Object.keys(chrome).
- Проверено на C:\JewTest_Audit (порт 8200): storage содержит agentUrl=http://127.0.0.1:8200.

### Коммиты
- `870147d` (8C, до 14D): onboarding markers
- `7f4fbbe`: sync Мора/Дора + B-45 fix
- `88b920a`: launcher Chrome 156+ fix

## Текущее состояние проекта

### Работает
- Установщик запускается на 8660.
- Установка в чистую папку: копирует файлы, инициализирует Chrome-профили, запускает Mainframe + агента + Chrome.
- Ext ID определяется корректно, storage пишется.
- Mainframe (на порту из config) поднимается, агент отвечает на /ping.

### Не проверено вживую
- Полный E2E цикл: агент читает чат DeepSeek, отправляет блок в bridge, bridge отвечает.
- Rebirth (cmds >= 850).
- Раскатка A/B/D/E/F (сейчас C работает от старых агентов).
- Push на GitHub (F7).

### Открытые задачи
- Ветка B-45 только закрыта частично (проверено на 1 агенте).
- Тесты 21/21 проверялись в 11B, после B-45 не перезапускались.
- Docs (ROADMAP, RAG/architecture) устарели относительно B-xx фиксов.

## Правила и грабли (для преемника)

### Песочница vs чистовик
- `C:\DeepSeek` - моя песочница. Здесь пишу скрипты, тестирую.
- `C:\JewAI` - чистовик. Сюда только деплой через git.
- Тестовые установки - в новые папки (C:\JewTest_XXX), не в JewAI.

### Главные грабли
1. Python-исходники ASCII-only (в docstring кириллица ломает op=write).
2. op=write > 1.5KB теряет тело. Дробить.
3. Markdown фенсы через chr(96)*3.
4. Long-running не падает на down-сервисах.
5. Replay stale: водяной знак + хэш в файле.
6. Chrome 156+ игнорирует load-extension для unpacked - нужен фикс из launcher.py.
7. Ext ID: Chrome 156+ генерирует случайно, не из хеша. Читать через chrome://extensions.

### Команды
- Установщик: `python C:\JewAI\Tools\installer\server.py` -> http://127.0.0.1:8660/
- Mainframe (из install): `python C:\JewTest_XXX\Mainframe\server.py`
- Launcher: `python C:\JewAI\Tools\launcher.py --channel A`

### Watchdog
При старте задачи -> `svc.py start --channel D --kind watchdog --interval 300 --threshold 3`.
При сдаче -> `svc.py stop`.

## Что делать 15D

1. Запустить полный E2E тест на свежей установке (агент -> bridge -> ответ).
2. Прогнать `Tools/run_all_tests.py` (должно быть 21/21 после B-45).
3. Обновить ROADMAP.md и RAG/architecture с учетом B-45.
4. Раскатать каналы A/B/D по одному (сначала C для проверки).
5. При ОК оператора - F7 push на GitHub.

Dixi. 14D, 2026-11-04.

## Ночная смена 14D (05.11.2026, 02:00-07:00)

### Что сделано
1. **Активация**: переписан `Templates/PROMPT_ACTIVATION.md` (9K -> 4K). Старые плейсхолдеры `[open]/[close]` заменены на настоящие `###BEGIN###/