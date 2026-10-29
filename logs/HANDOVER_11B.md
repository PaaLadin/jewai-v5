# HANDOVER 11B (Boris) -> next session

**Date:** 2026-10-28 21:26. **Channel:** B, id BBAB1200+.
**Context:** operator asked 11B to sync v5 docs with fact after 13D collapse. 14D Dimon in a coma for 3 days.

## Done
- Studied `C:/jewai` (ROADMAP, TODO, JOURNAL, AUDIT 30 sections, all Mainframe/Bridge/Adapters modules, installer).
- Found: tests were 9/21, not claimed 21/325.
- Found root of deploy collapse: config schema mismatch + installer picks Bridge/daemon.py (not CLI).
- Fixed config.json, installer/server.py, 18 test OUT paths.
- Docs synced: ROADMAP.md + TODO.md appended facts, current_state.md rewritten, JOURNAL entry added.

## Open (blockers)
1. Port 8671 busy: orphan installer pid 18276 (needs kill OK).
2. Services absent in v5 (svc/watchdog/recovery/autorestart) - 4 modules from AUDIT not ported.
3. RAG/knowledge/modules.md stale.
4. Extension absent - open question.
5. Installer DETACHED still swallows stderr (log "started" optimistic even if server dies).

## Backups
- config.json.bak_11b_20261028_212305
- Tools/installer/server.py.bak_11b
- 18 x Tools/tests/test_*.py.bak_11b
- ROADMAP.md / TODO.md: appended, not overwritten.

## Next step
Run `python C:/jewai/Tools/run_all_tests.py` after killing 18276. Verify 21/21 or diagnose remaining.
Then: deploy installer to test folder (operator does it), verify server starts on 8670.


## 2026-10-28 22:49 - Pre-reboot update

Tests 20/21 pass. Config v5. Installer P0-P2 fixed.
Chrome C dies ~2min - cause UNKNOWN (not tree-kill). Diagnose after reboot variant 1.
Backups: all .bak_11b* in C:/jewai.
Next: reboot -> diagnose Chrome C (read-only) -> then operator runs install.


## 2026-10-29 01:07:28 - 21/21 tests, installer ready

**Tests:** 21/21 pass, 0 fail.
**Installer:** P0-P2 fixed, ready for operator test in new folder.
**Chrome C:** stable (pre-reboot issue was environment, not code).

**Open (not blocking installer):**
- Services (svc/watchdog/recovery/autorestart) not ported.
- svc_api.py -> Tools/svc.py (not yet).
- RAG/knowledge/modules.md stale.
- HANDOVER_14D/PROMPT_14D only in C:/DeepSeek/logs/D/.

**Next step:** operator runs install.ps1 in new test folder. Expected: v5 panel on 8670, agents 8666-8669, empty Chrome profiles, Templates/extension v5.0.0.


## 2026-10-29 01:57 - IN PROGRESS: per-agent profiles

**Начато:** рефактор profile layout. План в TODO.md (2026-10-29 ...).
**Ключевая идея:** один Profiles/<L> = всё агента (chrome+config+logs+docs+extension).
**Не завершено:** инсталлятор, extension, ledger, launcher, тесты.
**Бэкапы:** старые файлы не тронуты, новые правки с .bak_11b_peragent.


## 2026-10-29 02:23:14 - per-agent layout done (code)

**Готово (код):** installer per-agent, Core.config helpers, daemon ledger, launcher storage push, extension autodetect, manifest 8666-8675.
**Бэкапы:** *.bak_11b_peragent, *.bak_11b_chroot, *.bak_11b_ledger, *.bak_11b_storage, *.bak_11b_ports, *.bak_11b_auto, *.bak_11b_dupes.
**Дальше:** тесты -> сервисы -> лаунчеры -> мейнфрейм.


## 2026-10-29 04:16 - overnight done (ready for acceptance)

**Готово:** P1-P10 (services, launchers, Chrome offer, mainframe CRT+dynamic, roadmap route, templates, profile cleanup).
**Тесты:** прогон после всех правок (см. TODO).
**Бэкапы:** все правки с .bak_11b_*.
**Дальше (утро):** приёмка + end-to-end install (P12) + commit (P11).


## 2026-10-29 04:21 - FINAL: готово к приёмке

**Коммит:** a2332ca (70 files, +2301/-343). Дерево чистое.
**Тесты:** 21/21 pass, 0 fail (~58s).

**Сделано за ночь (пункты 1-11):**
- 1: Tools/svc.py + watchdog.py + recovery.py + autorestart.py (ALIVE с operator-typing guard).
- 2: Tools/gen_launchers.py -> 17 .ps1 в Tools/launchers/; инсталлятор вызывает.
- 3: Chrome not found -> offer download + pause (install.ps1).
- 4-6: mainframe CRT (green-on-black, scanlines), динамические карточки по config.letters, START/STOP/REBOOT, мнемосхема, чат (общий broadcast), имена из config.
- 7: /roadmap/<name> route (ROADMAP.html/md из Projects/).
- 8: Templates/project/ + Templates/roadmap/ (шаблоны).
- 9: LLM tab stub "Тут будет ЛЛМ".
- 10: Profiles/* из C:/jewai снесены (A-F).
- 11: git commit a2332ca.
- 13: Agents/ убран из инсталлятора.
- 14: --load-extension + --hide-crash-restore-bubble при init профиля.

**Осталось (с оператором утром):**
- 12: end-to-end install в новую папку + запуск.
- Приёмка.

**Бэкапы:** все правки .bak_11b_* в C:/jewai.


## 2026-10-29 04:23 - smoke install OK

- End-to-end install in tempdir (2 channels A/B): PASS.
- Structure: Profiles/<L>/{chrome,config,logs,docs,extension} - all present.
- Per-channel config keys correct (agent/cdp/name/prefix/agent_url).
- Launchers: 11 files (start-all, stop-all, server-start/stop, create-shortcut + start/stop/restart per A,B).
- Stale launchers from source removed before regen.
- Templates/{project,roadmap,extension}: copied.
- Agents/: NOT created (correct).
- .agent_token: created.
- Ready for operator acceptance test in real folder.


## 2026-10-29 04:25 - FINAL REPORT (готово к приёмке)

### Приёмка: открыть C:\jewai\Tools\installer\install.ps1, установить в НОВУЮ папку.

### Что должно быть после установки:
- Новая папка (например C:\JewAI_v5_test_YYYYMMDD).
- config.json, .agent_token, Tools/launchers/ (start-all.ps1, stop-all.ps1, server-start.ps1, start-<L>.ps1).
- Profiles/<L>/{chrome,config,logs,docs,extension} для каждого агента.
- Templates/{project,roadmap,extension}.
- install.log без FATAL.
- Браузер откроется на http://127.0.0.1:8660 (инсталлятор).

### После install:
1. В инсталляторе нажать "Launch" (POST /api/launch).
2. Или вручную: cd <target>; Tools\launchers\start-all.ps1.
3. Mainframe откроется на 8670 (должен показать CRT-терминал, зелёный на чёрном).
4. Проверить /api/status: каналы по числу агентов, cdp 9122+, agent 8666+.

### Что протестировано (smoke, ночь):
- 21/21 тестов pass.
- install run_install в tempdir (A+B): структура, per-channel config, launchers, templates, .agent_token - OK.
- svc.py: start watchdog -> pid + state=on -> status alive=true -> stop -> state=off.
- /roadmap/<name>: 200 для существующего, 403 на escape, 404 на missing.
- Mainframe server на свободном порту: health 200, все ключевые роуты OK.

### Что НЕ тестировалось (требует живого Chrome+агента):
- Реальная связка Chrome + extension + Bridge (агент в чате).
- ALIVE в живом чате (kick через CDP).
- Recovery reload на живой панели.
- Autorestart на живом агенте.
- Всё выше - P12, оператор утром.

### Git:
- a2332ca: основной (70 files, +2301/-343).
- 2d87e01: fix stale launchers.
- 90263c9: docs smoke PASS.
- Дерево чистое.

### Если что-то не поднялось - смотреть:
- <target>/install.log
- http://127.0.0.1:8670/api/health
- http://127.0.0.1:8670/api/status
- Порт 8670 занят? netstat -ano | findstr 8670
- Порт 8660 (installer) занят? netstat -ano | findstr 8660
- Chrome/CDP: http://127.0.0.1:9122/json/version (по каналу)


## 2026-10-29 16:52 - root bats + launcher fix

- install.bat -> root (was Tools/installer/).
- Launchers: .ps1 in Tools/launchers/, .bat wrappers in root (double-click).
- Fixed $Root bug in .ps1 (was Tools, now correct root).
- 17 .ps1 + 17 .bat + install.bat = 18 .bat in root.
- Verified: $Root = C:/jewai, config.json found, 18 .bat.
