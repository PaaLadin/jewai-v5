# Perplexity adapter foundation

Status: experimental, stage 1 only. Not a complete sidepanel switching release.

Adapters/registry.py lists DeepSeek, Qwen, Alice and Perplexity. Unknown provider
names raise ValueError, never silently select DeepSeek. Adapters/perplexity.py
uses the shared block parser, with candidate assistant-role selectors stored in
perplexity_dom.js. The selectors have NOT been verified against the live UI.
Unknown assistant DOM yields no commands; never fall back to whole-page text,
user messages, citations or search results. Input text is never overwritten.
One Enter press submits a report; an empty composer is not a delivery receipt.
Stable text and known stop controls are heuristics, not a streaming guarantee.
New-chat and rebirth verification may require live UI and prompt adjustments.

Offline tests: python Tools/tests/test_perplexity_adapter.py
These isolate the adapter with fake CDP and a stub parser, not a real browser.

Remaining work: register the provider in existing entrypoints; sidepanel Save
and authenticated backend; safe execution-boundary switching; queue ownership;
launcher/onboarding URLs; G support across boot/services/rebirth; full regression
and Windows/Chrome end-to-end tests. Do not enable automatic execution merely
because these unit tests pass. Existing daemon retry behavior needs reconciliation
of uncertain submissions before production use.

Channel is independent of provider. Keep DeepSeek as the install default. Do not
overwrite operator channels E/Qwen or F/Alice. G is the proposed test channel;
actual membership and ports come from the installed config, not assumptions.
No paid API or API key is introduced by this foundation.
