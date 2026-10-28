# Agent layout: personal folder vs Chrome profile vs extension (13D, 2026-10-28)

Requirement from operator:
- Base extension template - one.
- Each channel has its OWN copy of extension (customized).
- Extension lives in channel personal folder - same place as TODO, personal notes, logs.
- Do NOT confuse with Chrome profile (browser data only).

## Current state of v5

- Profiles/<CH>/ - Chrome profile (browser data, cookies, cache, login). Location correct.
- Adapters/<model>.py - Python adapter for SPA. This is the bridge, not extension. Location correct.
- Extension (content.js, agent.py HTTP server, manifest.json) - ABSENT in v5.
  In old project: extension/ + extension_qwen/ + extension_alice/ (shared + specialization).

## Target structure

```
C:/JewAI/
  Templates/
    extension/              <- base template (do not touch without reason)
      manifest.json
      content.js            <- generic block parser
      background.js         <- service worker
      sidepanel.html + js
      agent.py              <- HTTP endpoint (read/write/run) on channel port
  Agents/
    A/                       <- personal folder for channel A
      TODO.md
      PERSONAL.md
      logs/
      extension/            <- copy of Templates/extension, customized for A
    B/ ... F/
  Profiles/
    A/                       <- Chrome profile A (browser data ONLY)
    B/ ... F/
  Core/, Bridge/, Adapters/, Mainframe/, Rebirth/, Tools/
```

## Rules

1. Templates/extension - source. Customizations only in Agents/<CH>/extension/.
2. Chrome loads extension via --load-extension=Agents/<CH>/extension.
3. Profiles/<CH>/ - only --user-data-dir. No code there.
4. Agents/<CH>/ - personal folder: TODO, personal notes, logs, custom extension.
5. Shared bridge modules (Python) - in Bridge/, Adapters/. Not in Agents/.

## What this changes in current v5

Currently v5 has no extension at all (ROADMAP: "Watermark/Ledger extension - not in v5").
If operator wants extension - it must be added. This does not contradict ROADMAP if we read
"not in v5" as "do not port old watermark/ledger", not "no extension needed at all".

Open question for operator:
- Is extension needed in v5 (content.js parses blocks, agent.py - HTTP endpoint)?
- Or is parsing via CDP sufficient (Bridge/daemon.py already does this in v5)?

13D current decision: Bridge/daemon.py via native CDP does what old extension did.
Extension not needed in v5. But if operator requires - layout above is ready.

## Adapters (Python) vs Extension (JS)

- Adapters/*.py: selectors, block parsing, send_text - via CDP, no extension.
- Extension: alternative path via JS in browser.
v5 chose CDP path. Second one kept as documented alternative.
