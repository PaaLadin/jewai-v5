# Current state (2026-10-29 02:23:14, 11B)

## per-agent layout (NEW)
- Profiles/<L>/{chrome, config, logs, docs, extension} - one folder per agent.
- Profiles/<L>/config/config.json - per-channel config (channel, name, prefix, agent_port, cdp_port, agent_url, extension, model, root, chat_port).
- Profiles/<L>/extension/ - per-channel extension copy.
- Profiles/<L>/logs/ledger_<L>.json + stale_<L>.log - per-channel replay-guard.
- Agents/<L> - REMOVED (single source of truth).
- Migration: move Profiles/<L> -> agent fully moved.

## Extension knows own port
- Installer writes per-channel config.
- Tools/launcher.py after CDP start pushes agentUrl/token/channel/name into chrome.storage.local via CDP.
- sidepanel.html: autodetect port 8666-8675 if storage empty.
- manifest host_permissions: 8666-8675 (was 8666-8669+8671-8672).

## Config / core
- Core/config.py: channel_root(L), channel_path(L, *parts), channel_config(L).
- Installer ignores .agent_token (does not copy from source).

## Tests: see last run
- 21/21 pass before refactor. Refactor in progress.
