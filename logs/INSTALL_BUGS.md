# INSTALL_BUGS - приём багов с тестовой инсталляции jewai_5

**Дата приёма:** 2026-11-02, 7C.
**Источник:** оператор, тестовая установка jewai_5.
**Правило:** каждый баг = id (B-NN), симптом, шаги, ожидание, что делать (проще / сложнее / после).

## Очередь (по мере приёма)

| id | Симптом | Источник | В ROADMAP (шаг) | Статус |
|----|---------|----------|-----------------|--------|

## Принято

(здесь будут баги по мере прихода)

Dixi. C (Семён), 7C, 2026-11-02.

### B-01: installer FATAL на logs/JOURNAL.md

- **Симптом:** install.bat запускается, файлы скопированы, потом FATAL: [Errno 2] No such file or directory: C:\JewAI_v5\logs\JOURNAL.md
- **Где:** Tools/installer/server.py, run_install (фаза после copytree)
- **Гипотеза:** logs/ не создан (git пустые папки не трекает) ИЛИ код открывает JOURNAL.md без проверки существования / без mkdir
- **Приоритет:** BLOCKER, без фикса install не завершается
- **Шаг в ROADMAP:** P12 (installer end-to-end), первый в очереди


**Точная причина (7C, разбор кода):**
- Tools/installer/server.py:70-78. Seeding logs/JOURNAL.md стоит ВНУТРИ цикла mkdir по [Core, Bridge, ..., logs, ...].
- На 1-й итерации (d=Core) target/logs/ ещё не создан, copyfile падает на несуществующем пути.
- exists(tpl_dst)=False (правильно), exists(tpl_src)=True (Templates/logs/JOURNAL.md есть), copyfile -> FileNotFoundError.
**Фикс (1 строка):** вынести seeding-блок за цикл mkdir, ИЛИ добавить os.makedirs(os.path.dirname(tpl_dst), exist_ok=True) перед copyfile.
