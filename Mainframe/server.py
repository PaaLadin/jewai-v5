"""Mainframe/server.py - entrypoint for v5 panel on port 8670."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from Core.config import load as load_config
from Mainframe import web, api, llm, mail, lada_chats, telemetry, rag_channel, council, health, svc_api, launchpad, controls, settings, diagnose


def _qs(path):
    if "?" not in path:
        return {}
    out = {}
    for pair in path.split("?", 1)[1].split("&"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            out[k] = v
    return out


def build_routes():
    return {
        ("GET", "/api/status"): api.status,
        ("GET", "/api/settings"): lambda c, p, b: settings.get_all(c),
        ("POST", "/api/settings"): lambda c, p, b: settings.set_adapter(c, (b or {}).get("channel", ""), (b or {}).get("model", "")),
        ("GET", "/api/telemetry"): api.telemetry,
        ("GET", "/api/health"): lambda c, p, b: health.collect(c),
        ("POST", "/api/svc"): lambda c, p, b: svc_api.handle(c, (b or {}).get("channel", ""), (b or {}).get("kind", ""), (b or {}).get("action", ""), b),
        ("GET", "/api/launchpad/status"): lambda c, p, b: launchpad.status(c),
        ("POST", "/api/boot"): lambda c, p, b: launchpad.boot(c, (b or {}).get("target", "")),
        ("POST", "/api/stop"): lambda c, p, b: launchpad.stop(c, (b or {}).get("target", "")),
        ("POST", "/api/restart"): lambda c, p, b: launchpad.restart(c, (b or {}).get("target", "")),
        ("GET", "/api/meeting"): lambda c, p, b: controls.meeting_get(c),
        ("POST", "/api/meeting"): lambda c, p, b: controls.meeting_set(c, b),
        ("GET", "/api/pause_all"): lambda c, p, b: controls.pause_all_get(c),
        ("POST", "/api/pause"): lambda c, p, b: controls.pause_set(c, (b or {}).get("channel", ""), (b or {}).get("on", True)),
        ("POST", "/api/resume"): lambda c, p, b: controls.pause_set(c, (b or {}).get("channel", ""), False),
        ("POST", "/api/diagnose"): lambda c, p, b: diagnose.collect(c),
        ("POST", "/api/pause_all"): lambda c, p, b: controls.pause_all_set(c, b),
        ("GET", "/api/logs"): lambda c, p, b: controls.logs_tail(c, _qs(p).get("name", "chat")),
        ("GET", "/api/roadmap"): lambda c, p, b: controls.roadmap_get(c, _qs(p).get("name", "game")),
        ("POST", "/api/roadmap"): lambda c, p, b: controls.roadmap_set(c, b),
        ("GET", "/api/projects"): api.projects,
        ("GET", "/api/chat_url/"): api.chat_url,
        ("GET", "/api/chats"): lambda c, p, b: {"ok": True, "chats": lada_chats.list_chats()},
            ("POST", "/api/chats"): lambda c, p, b: {"ok": True, "chat_id": lada_chats.create_chat((b or {}).get("title", "New Chat"))},
            ("POST", "/api/chats/delete"): lambda c, p, b: {"ok": lada_chats.delete_chat((b or {}).get("chat_id", ""))},
            ("GET", "/api/chats/"): lambda c, p, b: {"ok": True, "messages": lada_chats.get_chat(p.rstrip("/").split("/")[-1])},
            ("GET", "/api/sys_telemetry"): lambda c, p, b: telemetry.collect(c),
            ("GET", "/api/llm"): lambda c, p, b: llm.status(c),
        ("GET", "/api/llm/params"): lambda c, p, b: llm.get_params(c),
        ("POST", "/api/llm/params"): lambda c, p, b: llm.set_params(c, b or {}),
        ("GET", "/api/llm/tools"): lambda c, p, b: llm.get_tools(c),
        ("POST", "/api/llm/tools"): lambda c, p, b: llm.set_tool(c, (b or {}).get("name",""), bool((b or {}).get("on", False))),
        ("GET", "/api/llm/history"): lambda c, p, b: llm.history(c, int(_qs(p).get("n", 50))),
        ("POST", "/api/llm/clear"): lambda c, p, b: llm.clear_history(c),
        ("POST", "/api/llm/query"): lambda c, p, b: llm.query(c, (b or {}).get("text", ""), (b or {}).get("chat_id", "")),
        ("GET", "/api/mail"): lambda c, p, b: mail.status(c),
        ("POST", "/api/mail/send"): lambda c, p, b: mail.send(c, (b or {}).get("subject", ""), (b or {}).get("body", "")),
        ("POST", "/api/rag/push"): lambda c, p, b: rag_channel.push(c, (b or {}).get("from", "?"), (b or {}).get("to", "ALL"), (b or {}).get("text", "")),
        ("GET", "/api/rag/pull/"): lambda c, p, b: rag_channel.pull(c, p.rstrip("/").split("/")[-1].upper(), float(b.get("since", 0) or 0) if b else 0.0),
        ("GET", "/api/messages"): lambda c, p, b: {"ok": True, "messages": council.load_messages(c, 200)},
        ("POST", "/api/send"): lambda c, p, b: council.send(c, (b or {}).get("from", "operator"), (b or {}).get("to", "ALL"), (b or {}).get("text", "")),
        ("GET", "/api/say/"): lambda c, p, b: {"ok": True, "note": "use POST /api/send"},
        ("GET", "/api/chat/"): lambda c, p, b: {"ok": True, "channel": p.rstrip("/").split("/")[-1].upper(), "messages": council.load_personal(c, p.rstrip("/").split("/")[-1].upper(), 200)},
        ("POST", "/api/chat/"): lambda c, p, b: council.send_personal(c, p.rstrip("/").split("/")[-1].upper(), (b or {}).get("from", "operator"), (b or {}).get("text", "")),
    }


def main() -> int:
    cfg = load_config()
    web.run(cfg, build_routes())
    return 0


if __name__ == "__main__":
    sys.exit(main())