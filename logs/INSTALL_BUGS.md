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

### B-02: installer не убивает старый server.py на 8660

- **Симптом:** после фикса B-01 повторная установка даёт ту же ошибку logs/JOURNAL.md. Фиксы не применяются.
- **Где:** Tools/installer/install.ps1, строки 57-61: Start-Process pythonw server.py без kill старого; Start-Process http://127.0.0.1:8660 попадает в старый процесс.
- **Факт:** netstat :8660 -> LISTENING PID 11344 и 14344 (два старых server.py).
- **Фикс:** перед Start-Process pythonw server.py — убить все pythonw с cmdline, содержащим server.py и 8660 (или Get-NetTCPConnection -LocalPort 8660 | Stop-Process).
- **Приоритет:** BLOCKER, без него любой фикс installer не применяется.



### B-04: push_storage FAILED для канала B (storage=False)

- **Симптом (install.log):** `Chrome A launcher rc=0 storage=True`; `Chrome B launcher ... push_storage FAILED x3 channel=B cdp=9123 storage=False`.
- **Где:** Tools/launcher.py::_push_storage (расширение B не получает agentUrl/token/channel/name в chrome.storage.local).
- **Последствия:** sidepanel B стартует без своих настроек, fallback на autodetect 8666-8675; имя/канал в UI могут показывать UNKNOWN.
- **Приоритет:** HIGH. Первый канал работает, второй — нет. Значит баг не в _push_storage как таковой, а в тайминге/окне готовности extension target для B (Chrome B стартует позже, target ещё не поднят за 3x2s).
- **Гипотеза фикса:** увеличить retry до 10x1s; ждать появления любого chrome-extension:// target; проверять по URL sidepanel/background; при неудаче — ретрай через 5с после первого push.

### B-05: имя второго агента = буква (UX)

- **Симптом:** оператор ввёл `Hans` в [6/6] → A=Hans, B=`"name": "B"`. Для неопытного пользователя — неожиданно.
- **Где:** Tools/installer/server.py, channels[L]["name"] = names_list[i] if i < len(names_list) else L.
- **Ожидание:** либо дефолт «Agent B» / «Boris», либо отказ: «для 2 агентов нужно 2 имени» / «оставьте пустым для всех».
- **Приоритет:** LOW (UX, не блокер).



### B-06: Mainframe 8670 — не тот UI (Pip-Boy sidepanel вместо Mainframe-пульта)

- **Симптом:** при старте открывается http://127.0.0.1:8670/ — это нормально. Ненормально: вместо панели Mainframe-пульта там визуал sidepanel моста (Pip-Boy UI от 12B).
- **Где:** Mainframe/static/{index.html,app.js,style.css}.
- **Что должно быть:** панель управления как в DeepSeek 8770 (Mainframe): блоки агентов (agent:CH, chrome:CH, server, doh, mailbot, rebirth, lada), мнемосхема, кнопки START/STOP/REBOOT, вкладки чата/проектов/roadmap, красные/зелёные лампы по cmds_from_start.
- **Масштабируемость:** количество блоков = config.letters (1-10), не хардкод 6. Имена/индексы агентов — из config.channels.<L>.name.
- **Образец кода:** C:/DeepSeek/sandbox/council_chat/{server.py,launchpad_live.js,index.html,style.css} + git/jewai (там есть наглядная версия).
- **Правило:** переписать с исходников панели Mainframe, не копировать из DeepSeek 1:1 (по ROADMAP v5 «код старого не копируется»). Контракт и костыли — из AUDIT.md §28.
- **Приоритет:** MEDIUM (не блокер, но UX/функционал v5). Ставить после B-04 и раскатки B-F.
- **Источник:** оператор, 2026-11-02, скриншот install → Mainframe 8670.


### B-03: installer не завершает свой сервер (жизненный цикл)

- **Симптом:** installer-сервер на 8660 живёт после успеха/провала; копится (B-02 видел два процесса одновременно).
- **Где:** Tools/installer/{install.ps1, server.py, app.js}.
- **Что сделано (7C, fix a632960 + 79d8b97):**
  - install.ps1: kill stale 8660 при старте (Get-NetTCPConnection -> Stop-Process).
  - server.py: `_kill_stale_on_port()` при старте; `/shutdown` роут (os._exit(0)); self-shutdown через 15с после успешного run_launch.
  - app.js: Enter на терминальных состояниях (fail/cancel/done) -> `fetch('/shutdown')`; авто-shutdown через 60с.
- **Приоритет:** BLOCKER (был). Закрыт кодом.
- **Проверка:** требует повторного прогона install.bat -> успех -> проверить, что 8660 свободен через 15с; провал -> через 60с.


### B-07: Onboarding-страница в каждой вкладке Chrome агента (вместо about:blank)

- **Симптом:** после install Chrome агента открывается на about:blank. Неопытный оператор не знает, что делать дальше.
- **Что должно быть:** в каждой вкладке Chrome агента открывается локальный onboarding-HTML:
  - "Ты — агент <буква>, зовут <name>. Три шага до первого запуска:"
  - Шаг 1: "Открой панель расширения. Ты видишь иконку JewAI в правом верхнем углу? Жми сюда →" (визуальная стрелка на icon)
  - Шаг 2: "Залогинься в чат: <link chat.deepseek.com / chat.qwen.ai / alice.yandex.ru>" (по model канала)
  - Шаг 3: "Закрепи вкладку чата (правый клик на вкладке → Закрепить), чтобы случайно не закрыть"
  - Кнопка: "Готово, открыть чат" → ведёт на URL чата
- **Где:** отдаётся agent.py на порту агента (новый роут `GET /onboarding?channel=<L>`). HTML — единый шаблон, параметры per-channel из config. Launcher при первом запуске открывает `http://127.0.0.1:<agent_port>/onboarding?channel=<L>` вместо about:blank.
- **Приоритет:** HIGH (UX для неопытного оператора, вторая точка после B-06).
- **Связано:** B-08.

### B-08: Линк-лист чатов + инструкция логина/закрепления (onboarding-контент)

- **Симптом:** в onboarding нужен контент — какие чаты, какие линки, как закрепить вкладку.
- **Что должно быть:** отдельный HTML/текст `RAG/onboarding/AGENT_FIRST_RUN.md` (или встроенный в onboarding-страницу), который:
  - Перечисляет распространённые чаты: chat.deepseek.com, chat.qwen.ai, alice.yandex.ru, chatgpt.com, claude.ai, gemini.google.com (сейчас мост настроен только под DeepSeek — Qwen/Alice адаптеры есть, но не оттестированы в v5).
  - Поясняет: "Не логинь Chromium в Google. Логинься только в чат."
  - Поясняет: "Профиль Chromium — папка C:/JewAI_v5/Profiles/<L>/chrome. В ней хранятся куки, логины, вкладки. Не удаляй — иначе логин потеряется."
- **Где:** RAG/onboarding/, встроено в B-07.
- **Приоритет:** HIGH, идёт вместе с B-07.

### B-09: Автодетект "не авторизован" — вернуть на onboarding

- **Симптом:** если куки чата истекли (DeepSeek refresh token), Bridge видит редирект на www.deepseek.com/en, не находит /a/chat/s/ и молчит. Оператор не понимает, что делать.
- **Что должно быть:** Bridge при `find_chat` returns None + детект "url редиректит на login/www" -> сигнал в Mainframe (alerts) -> Mainframe-панель показывает красный статус канала + кнопка "Залогиниться заново" -> открывает chat URL в той вкладке.
- **Где:** Bridge/cdp.py (расширенный find_chat, возвращать причину), Mainframe/health.py (алерт), Mainframe/static (кнопка).
- **Приоритет:** MEDIUM (после B-07/B-08). Связано с BUG3a (в DeepSeek отложен).

### B-10: Автовосстановление вкладки чата через CDP

- **Симптом:** вкладка чата может пропасть — случайно закрыли, Chrome крашнулся без restore, Chromium выгрузил target.
- **Что должно быть:** Bridge/run.py при потере чата (find_chat None, но CDP жив) -> `Target.createTarget` на URL чата -> повторный find_chat. Не ждать оператора.
- **Где:** Bridge/run.py / Bridge/cdp.py.
- **Приоритет:** MEDIUM (страховка, не критично, если B-07/B-08 работают).
- **Связано:** вкладка-пин не решает (pin — UX, не CDP).


### B-07 (обновлено 02.11): Onboarding HTML + чекбокс "не показывать"

- **Дополнение к B-07:** в onboarding-HTML добавить:
  - краткую инструкцию по проекту в целом (5-7 абзацев, для неопытного);
  - пустой чекбокс "Не показывать это окно при следующих запусках";
  - при проставке — POST /api/onboarding/disable?channel=L -> записать флаг (общий по умолчанию) в config.json (onboarding_disabled: true);
  - launcher перед открытием onboarding проверяет флаг.

### B-11: Rebirth пишет active chat URL + модель в config

- **Проблема:** после rebirth создаётся новый чат, но конфиг не знает, какой чат активный. Bridge ищет по общему маркеру /a/chat/s/ -> коллизия со старым чатом.
- **Что должно быть:** rebirth пишет в logs/active_chat_<CH>.json: chat_url (полный URL), model, model_index (порядковый), created_at.
- **Bridge find_chat:** сначала пробует конкретный URL из active_chat, fallback на общий поиск + алерт.
- **Mainframe status:** показывает "active model N, chat URL", красный если URL не открыт.
- **Приоритет:** MEDIUM (после B-04, B-07, B-08). Связано с B-09, B-10.


### B-12: Mainframe — вики по проекту (how-to, без тех. деталей)

- **Что:** отдельная вкладка в Mainframe 8670 — «Вики» / «Справка» / «How to».
- **Контент:** как пользоваться агентами, как логиниться, как закреплять вкладки, что делать если сломалось, ключевые механики (каналы, rebirth, восстановление). Без кода, без внутренних процедур.
- **Где:** Mainframe/static/ + роут /wiki или /help, контент — RAG/wiki/*.md.
- **Приоритет:** LOW (хвост). После RAG, раскатки, B-04..B-11, релизного пуша.
