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
