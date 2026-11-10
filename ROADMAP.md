# JewAI v5 ROADMAP

## Done
- [x] Base setup by Semyon (Bridge, Mainframe skeleton).
- [x] BUG-017 fixed by Semyon (bridge hangs on background procs).
- [x] Lada LLM deployed via llama.cpp b12243 CUDA 12.4 (RTX 2070 SUPER).
- [x] Lada launch scripts (start_all.bat, start_lada.bat, start_mainframe.bat).
- [x] Mnemoscheme action log (OK/FAIL) for LLM buttons.
- [x] lada_setup.py hardcode removed (config.json driven).

## In Progress (Arkady)
- [ ] Multi-chat system for Lada (Create, Switch, Delete chats with confirmation).
- [ ] Chat History persistence (save to files for RAG indexing).
- [ ] UI fixes: Enter to send, Shift+Enter newline, fixed scroll, font size, sticky bottom.
- [ ] Self-test & Health check (verify bridge worker, not just HTTP).
- [ ] Mnemoscheme LLM buttons (launchpad.py target llm).

## Future
- [ ] SMB sync with Monolith distro (C:/JewAI/).
- [ ] Git push integration (need token).
- [ ] RAG chunking of chat histories for cross-chat memory.
- [ ] Agentic tool use for Lada (execute scripts via bridge).
