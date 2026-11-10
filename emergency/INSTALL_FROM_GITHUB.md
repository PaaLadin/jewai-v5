# INSTALL_FROM_GITHUB — установка с нуля

Полная инструкция — в корневом `INSTALL.md`. Здесь — короткая
памятка для того, кто ставит проект впервые.

---

## Что понадобится

- Windows 10/11.
- Python 3.11+ (`python --version`).
- Chrome / Edge.
- Git.

---

## Шаги

1. Клонировать репозиторий:

       git clone <URL> jewai
       cd jewai

2. Установить зависимости:

       pip install -r requirements.txt
       python -m playwright install chromium

3. Запустить установщик:

       python install.py

   Установщик спросит папку, число каналов (1–10), базовый порт.
   Создаст структуру, профили Chrome, `config.json`, launchers.

4. Создать `.agent_token` — любая длинная случайная строка.

5. Запустить всё:

       launchers\start-all.ps1

6. В каждом Chrome установить расширение (Load unpacked →
   `extension_v2`) и настроить сайдпанель.

7. Проверить: read-команда в чате возвращает `[AGENT REPORT]`.

---

## Если что-то не работает

- Панель серая → `OPERATOR_GUIDE.md`.
- Агент молчит → `python sandbox\ping_all.py`.
- Совсем не поднимается → корневой `INSTALL.md`, раздел
  «Восстановление».