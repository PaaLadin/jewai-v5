# Perplexity selectors: source check, not live verification

Evidence checked 2026-11-06:
https://github.com/urzeye/ophel/pull/1021 (merged 2026-11-05)
https://github.com/urzeye/ophel/blob/main/registry/sites/perplexity.json
Registry blob SHA: 37fa94bb4797d6eb724d1604b00479be1757b609.

The recent fix reports removal of #ask-input and old flow-root wrappers.
Current registry uses [data-lexical-editor='true'], user bubbles identified by
[data-message-bubble='right'], and .prose[data-renderer='lm'] for answers.
Scope is .scrollable-container .max-w-threadContentWidth. Do not replace this
with generic .prose or document.body command scanning. User bubbles, sidebars,
navigation and dialogs are excluded. Input and focus share one JSON selector set.

Additional candidate stop-control evidence:
https://github.com/mvanhorn/agent-tincan/blob/main/docs/adapters/web-agents.md
That source explicitly labels several assistant/stop selectors unconfirmed.
Stop controls plus text stability remain heuristics, not proof of completion.

CSS tests use synthetic HTML, beautifulsoup4 and soupsieve. They do not test
visibility, real Chrome, account login, Lexical event behavior or actual delivery.
Run: python Tools/tests/test_perplexity_selectors.py
Run existing adapter tests too: python Tools/tests/test_perplexity_adapter.py
The adapter remains experimental until a read-only probe in the operator's logged-in
browser confirms matched containers and input; then test one harmless round trip.
No authenticated browser connector or access to the operator's CDP is available in
this chat. This commit does NOT include the separate uncommitted sidepanel ZIP.
