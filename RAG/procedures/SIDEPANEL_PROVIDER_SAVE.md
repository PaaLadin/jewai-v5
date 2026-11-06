# Sidepanel provider Save: experimental integration

Click the extension icon after fresh deployment/reload. provider_panel.html wraps
the original sidepanel; old standalone sidepanel.html debug tabs have no selector.
Agent count, letters and ports stay unchanged. DeepSeek remains the install default.

Save validates the profile channel against /identity and reads root config.json.
It uses authenticated /run to execute the fixed Tools/select_provider.py command.
The runner consumes requests BETWEEN ticks, opens a new pinned CDP target, pauses,
archives report/kick queues and activation flag, backs up configs, updates root and
per-channel model, then sends activation with the next ledger ID. IDs are retained.
Config-write failures roll back; ambiguous sends block instead of retrying.
An OS installation lock serializes config changes. No process is killed.

Known limits (not a finished release):
- Existing /run rejects Save while paused (423); no secret automatic unpause.
- Perplexity DOM and browser authentication are not live-verified.
- Pinned target recovery after Chrome restart is unfinished; no old-tab fallback.
- Inspect provider_state.json and chat on error/confirmation_required; do not
  blindly resume. 'ready' means submitted, not acknowledged by the model.
- Legacy kick/rebirth routing and remaining A-F limits elsewhere are unfinished.
- G must already exist in installed config; this does not add unwanted agents.
- Qwen/Alice content injection is disabled to avoid a second executor. Python
  adapters remain enabled; DeepSeek retains its existing stuck-response helper.
- Existing agent /identity caches model; the new selector reads actual root config.
- Full legacy Windows/Chrome regression remains to be run locally.

Test: python Tools/tests/test_provider_switch.py (offline files and fake CDP).
No paid API, API key, or new unauthenticated endpoint is introduced.
