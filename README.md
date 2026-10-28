# JewAI v5
Local bridge between LLM chats and filesystem. Version 0.1.0-dev.
## Architecture
- Core/config.py - single source: ports, channels, paths, timeouts.
- Bridge/cdp.py - native CDP client (no Playwright).
- Bridge/read.py - readers (text, textarea, heartbeat, sidepanel).
- Bridge/exec.py - block parser, replay-guard (Ledger), operations.
- Bridge/daemon.py - poll loop: stable-gate, coalesce, dedup, report.
- Bridge/run.py - daemon entrypoint per channel.
- Adapters/deepseek.py, qwen.py, alice.py - SPA-specific.
- Tools/launcher.py - Chrome launcher.
- Tools/boot.py - stack orchestrator (never kills foreign).
- Tools/diagnose.py - one-shot health report.
- Tools/run_all_tests.py - runs all tests, summary to logs/runtime/.
- Mainframe/ - panel 8670: web.py, api.py, llm.py, mail.py, rag_channel.py, server.py, static/.
- Rebirth/ - series table, gate, orchestrator, onboarding.

## Ports

| Ch | Agent | CDP |
|----|-------|-----|
| A | 8666 | 9122 |
| B | 8667 | 9123 |
| C | 8668 | 9124 |
| D | 8669 | 9125 |
| E | 8671 | 9126 |
| F | 8672 | 9127 |

Panel: 8670.

## Running

Boot stack (channel C):

```text
python C:/JewAI/Tools/boot.py --channel C
```

Mainframe only:

```text
python C:/JewAI/Mainframe/server.py
```

Daemon for one channel:

```text
python C:/JewAI/Bridge/run.py --channel C
```

Health report:

```text
python C:/JewAI/Tools/diagnose.py
```

All tests:

```text
python C:/JewAI/Tools/run_all_tests.py
```

## Tests

14 suites, 207 checks, all green (13D session).
Suite list in Tools/tests/. Summary -> logs/runtime/_v5_all_tests.txt.

## Rules of engagement

1. RAG/architecture/AUDIT.md - source of truth: what came from old and what does NOT.
2. RAG/procedures/architecture.md - short decisions.
3. logs/JOURNAL.md - append-only completed steps.
4. logs/TODO.md - planned work, [x] only after test passes.
5. Python source ASCII-only, <=1.5KB per op=write, py_compile each fragment.
6. Module named like stdlib (http, json) MUST have subprocess test.

## Known blockers (operator decision required)

1. Port 8670 busy by pid 5304 (predecessor Mainframe). Our Mainframe tested on 8671.
   Restart with: ```text
taskkill /PID 5304 /F and python C:/JewAI/Mainframe/server.py
```
2. F2 live-send E2E: writes into live C chat.
3. F6 rollout A/B/D/E/F: spawn live agents.
4. F7 GitHub push.

## Session 13D summary

- AUDIT.md 44467b, 29 sections + replay-guard lesson.
- 27 modules written from scratch.
- 14 test suites, 207 checks, all green.
- Chrome C v5 (9124) live, E2E read verified.
- HANDOVER_14D + PROMPT_14D updated.
- JOURNAL 24 entries.
