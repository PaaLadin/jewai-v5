# Architecture decisions (v5, 13D)

Короткие решения, чтобы 14D не переоткрывал.

## 1. Один адаптер на SPA-семейство, не на канал

Адаптер `Adapters/deepseek.py` знает про SPA (селекторы, поведение).
Каналы A-D — один и тот же адаптер, разные порты.
Qwen и Alice — отдельные адаптеры в Ф6.

## 2. Config - единственный источник правды

Порты, каналы, пути, таймауты - только из `config.json` через `Core/config.py`.
Никаких hardcoded `C:/DeepSeek` или `127.0.0.1:9124` в коде.
Хардкод допустим только в тестах.

## 3. Replay-guard - обязательный слой

См. AUDIT §29. Водяной знак + хэш + `stale_blocks.log` - в `Bridge/exec.py` Ledger.
Не обходить, не отключать. Если отладка требует обхода - отдельный тестовый флаг,
не в продакшн.

## 4. Daemon - единственный владелец цикла

`Bridge/daemon.py` держит stable-gate, coalesce, min_gap, inflight.
Не дублировать в адаптере. Адаптер - только SPA-специфика.

## 5. Python-исходники - ASCII-only

См. AUDIT §30. Кириллица в docstring ломается через `op=write` > 1.5 КБ.
Дробить на фрагменты, py_compile каждого, склейка через build-скрипт.

## 6. Mainframe - сборка без внешних зависимостей

Только stdlib. ThreadingHTTPServer, urllib, smtplib, json.
Ни Flask, ни FastAPI. Loopback only, X-Token - Ф5 (не реализован).

## 7. Rebirth - таблица серий + гейт + lock

`Rebirth/table.py` - series math и atomic write.
`Rebirth/master.py` - gate (limit|force|hold|threshold|deny) + lock TTL 1h + run.
CDP-цикл (create_chat, send_prompt, verify) - Ф5, реализуется поверх Bridge.
Ф4 minimal = gate + table advance.

## 8. Блокеры без ОК оператора

- Ф2 live-send: отправка в живой чат C.
- Ф6 раскатка: спавн агентов A/B/D/E/F.
- Ф7 GitHub push: force push в PaaLadin/jewai-v5.
- Убийство pid 5304 на 8670 (старый Mainframe).
- Все - разрушительные или вне зоны.

## 9. Что делать 14D без ОК

- Расширять покрытие тестов (edge cases).
- Документация в RAG/procedures/, RAG/knowledge/.
- Мониторинг: периодический прогон всех тестов, алерт на регресс.
- Рефакторинг при наличии тестов (Т.З. - сохранять контракт).

## 10. Installer UI (Accepted 28.10)
Default installer interface is a retro CRT terminal (BBS style).
Features: Typewriter text, Web Audio API synth (keyboard clicks, printer noise, WebMoney coins for splash).
Interactive dialog with language selection (en/ru) and aliases (y/n/da/net).
