# Грабли Python (специфика проекта)

## 1. Python-исходники ASCII-only

**Правило (AUDIT §30):** docstring, комментарии - **только латиница**.

**Кириллица** - только в данных (JSON, md, конфиги).

**Причина:** op=write теряет тело при размере, обрезка непредсказуема,
em-dash / кириллица становится первой точкой падения парсера.

## 2. op=write крупного python-файла

**Не писать python-файл > 1.5 КБ через op=write.**

**Правило:**

1. Фрагменты по 1-1.5 КБ.
2. После каждого - py_compile.compile(..., doraise=True).
3. Склейка - отдельным build-скриптом.
4. Или pathlib.Path.write_text(...) через python-скрипт (файл -> файл).

## 3. sha256 от in-memory != от диска

**Симптом:** считаешь sha256(src.encode()) - один хеш, читаешь файл с диска - другой.

**Причина:** LF vs CRLF. write_text пишет \r\n на Windows, а .encode() даёт \n.

**Правило:** для сверки считать read_bytes() **после записи**, не от in-memory.

## 4. subprocess с DETACHED_PROCESS

**Для фоновых процессов:**

```
flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
p = subprocess.Popen([...], creationflags=flags,
                     stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL)
```

**Почему:** без DETACHED_PROCESS процесс - потомок моста и умирает по tree-kill.

**Проверка:** Get-Process -Id <pid> через 2 сек после op: run.

## 5. Windows pythonw вместо python

**Для фоновых процессов - pythonw.exe, не python.exe.**

python.exe рисует окно консоли. pythonw.exe - нет.

**Fallback:** если pythonw.exe нет - python.exe с CREATE_NO_WINDOW.

## 6. Кодировка stdout при subprocess

**При subprocess.run(..., capture_output=True, text=True)** - text=True использует системную кодировку (cp1251). Кириллица бьётся.

**Правило:**

```
r = subprocess.run([...], capture_output=True,
                   encoding="utf-8", errors="replace")
```

## 7. Импорты модулей с именем stdlib

**Правило (AUDIT):** если модуль назван как stdlib (http, json, web) - subprocess-тест обязателен.

**Причина:** from Mainframe import web может затенять stdlib web.

## 8. asyncio не тащим

Для websocket-client (CDP) хватает **sync**-режима. asyncio усложняет, не нужен.

## 9. pathlib vs os.path

**Всегда pathlib.Path.** Кроссплатформеннее, читаемее.

- Path(r"C:\\...") - raw string на Windows.
- Path("a") / "b" / "c" - join.
- .read_text(encoding="utf-8") - всегда указывать кодировку.

## 10. json.dump с ensure_ascii

**Правило:** ensure_ascii=False для читаемых файлов (config, ledger).

Без него кириллица в \u-escape. С ним - нормальный текст.

## 11. Атомарная запись JSON

**Правило:** не перезаписывать сразу, а tmp -> os.replace(tmp, real).

```
def atomic_write(p, data):
    p = pathlib.Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)
```

## 12. Проверка синтаксиса без py_compile

py_compile.compile пишет .pyc в __pycache__ - если он read-only, PermissionError.

**Обход:** compile(src, filename, "exec") - только проверка синтаксиса, без записи.

## 13. Таймауты subprocess

Всегда timeout=N. Без него - висит, если дочерний процесс ждёт.

После TimeoutExpired - p.kill() + p.communicate() (иначе зомби).

## 14. print в фоновых процессах

**Для detached-процессов** - print в stdout=DEVNULL, иначе pids накапливаются.

**Для логов** - pathlib.Path("log.txt").write_text(msg, encoding="utf-8") (append через open("a")).

