"""Provider requests are consumed only between complete daemon ticks.

The existing authenticated /run endpoint enqueues a request. No process is killed.
A new chat is pinned by CDP target ID; old queues are archived, never replayed.
"""
import contextlib
import json
import os
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse
from Adapters.registry import provider


def read(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=True, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


@contextlib.contextmanager
def locked(root):
    """OS-owned installation lock; automatically released on process death."""
    path = Path(root) / "logs" / "runtime" / "provider.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def paths(cfg, letter):
    base = cfg.channel_path(letter, "logs")
    return base / "provider_request.json", base / "provider_state.json"


def enqueue(cfg, letter, model, expected):
    provider(model)
    ch = cfg.channel(letter)
    request, state = paths(cfg, letter)
    with locked(cfg.root):
        raw = read(cfg.path("config.json"))
        actual = raw["channels"][letter]["model"]
        if actual != expected:
            raise ValueError("provider changed; refresh the panel")
        if request.exists():
            raise ValueError("a provider request is already pending")
        previous = read(state, {})
        if previous.get("phase") not in (None, "ready", "error", "unchanged"):
            raise ValueError("previous switch is not finished")
        if model == actual:
            return {"ok": True, "phase": "unchanged", "model": actual}
        nonce = uuid.uuid4().hex
        body = {"nonce": nonce, "model": model, "expected": expected}
        write(state, dict(body, phase="queued", ts=time.time()))
        write(request, body)
        return dict(body, ok=True, phase="queued")


def _open_target(ch, url):
    from Bridge.cdp import CDP, list_targets
    pages = [p for p in list_targets(ch.cdp_port)
             if p.get("type") == "page" and p.get("webSocketDebuggerUrl")]
    if not pages:
        raise RuntimeError("Chrome CDP is unavailable; config not changed")
    cdp = CDP(pages[0]["webSocketDebuggerUrl"])
    try:
        reply = cdp.call("Target.createTarget", {"url": url})
        target = reply.get("result", {}).get("targetId")
        if not target:
            raise RuntimeError("CDP did not return a target ID")
        return target
    finally:
        cdp.close()


def consume(cfg, letter):
    request, state = paths(cfg, letter)
    if not request.exists():
        return
    try:
        with locked(cfg.root):
            _consume(cfg, letter, request, state)
    except (BlockingIOError, PermissionError):
        return


def _consume(cfg, letter, request, state):
    body = read(request)
    if not isinstance(body, dict):
        raise ValueError("invalid provider request")
    nonce = str(body.get("nonce", ""))
    if len(nonce) != 32 or any(c not in "0123456789abcdef" for c in nonce):
        raise ValueError("invalid request nonce")
    ch = cfg.channel(letter)
    base = cfg.channel_path(letter, "logs")
    config_path = cfg.path("config.json")
    local_path = cfg.channel_path(letter, "config", "config.json")
    raw = read(config_path)
    old = raw["channels"][letter]["model"]
    saved_root = config_path.read_text(encoding="utf-8")
    saved_local = local_path.read_text(encoding="utf-8") if local_path.exists() else None
    touched = False
    try:
        model = body["model"]
        item = provider(model)
        if old != body["expected"]:
            raise ValueError("stale provider selection")
        if old == model:
            write(state, dict(body, phase="unchanged", ts=time.time()))
            return
        pause = read(base / "paused.json", {"paused": False})
        target = _open_target(ch, item["url"])
        # Pause before changing config or queues. Current tick has already ended.
        write(base / "paused.json", {"paused": True, "by": "provider_switch", "since": time.time()})
        touched = True
        archive = base / "provider_archive" / nonce
        archive.mkdir(parents=True, exist_ok=False)
        (archive / "root_config.json").write_text(saved_root, encoding="utf-8")
        if saved_local is not None:
            (archive / "channel_config.json").write_text(saved_local, encoding="utf-8")
        for name in ("outbox_" + letter + ".jsonl", "kick_buffer.jsonl", "activation_sent.flag"):
            src = base / name
            if src.exists():
                os.replace(src, archive / name)
        active = cfg.path("logs", "active_chat_" + letter + ".json")
        if active.exists():
            os.replace(active, archive / active.name)
        raw["channels"][letter]["model"] = model
        local = read(local_path, {})
        local.update(channel=letter, model=model)
        write(local_path, local)
        write(config_path, raw)
        write(state, dict(body, phase="awaiting_input", target=target,
                          previous_paused=bool(pause.get("paused")), ts=time.time()))
    except Exception as exc:
        if touched:
            # Root config is authoritative. Remain paused on any partial failure.
            write(config_path, json.loads(saved_root))
            if saved_local is not None:
                write(local_path, json.loads(saved_local))
            else:
                local_path.unlink(missing_ok=True)
        write(state, dict(body, phase="error", error=str(exc), ts=time.time()))
    finally:
        request.unlink(missing_ok=True)


def bound_connect(cfg, letter, adapter):
    from Bridge.cdp import CDP, connect, list_targets
    _, state_path = paths(cfg, letter)
    state = read(state_path, {})
    if not state.get("target"):
        return connect(cfg.channel(letter).cdp_port, adapter.HOST)
    if state.get("model") != cfg.channel(letter).model:
        raise RuntimeError("provider/session mismatch; refusing an old chat")
    for target in list_targets(cfg.channel(letter).cdp_port):
        if target.get("id") == state["target"]:
            host = urlparse(target.get("url", "")).hostname
            if host != adapter.HOST:
                return None
            return CDP(target["webSocketDebuggerUrl"])
    return None


def initialize(cfg, letter, daemon, cdp):
    """Returns True only when normal tick execution is allowed."""
    _, state_path = paths(cfg, letter)
    state = read(state_path, {})
    phase = state.get("phase")
    if phase in (None, "ready", "unchanged"):
        return True
    if phase != "awaiting_input":
        return False
    # Empty visible composer only. No generic page text is parsed as commands.
    ready = cdp.eval_expr("""(() => {
      const el = [...document.querySelectorAll('textarea, [contenteditable="true"]')]
        .find(e => e.getClientRects().length && !e.disabled && !e.readOnly);
      return !!el && !(el.value === undefined ? el.innerText : el.value).trim();
    })()""")
    if not ready:
        return False
    pause_now = read(cfg.channel_path(letter, "logs", "paused.json"), {})
    if pause_now.get("paused") and pause_now.get("by") != "provider_switch":
        return False
    prompt = daemon._render_activation()
    if not prompt:
        state.update(phase="error", error="activation template missing")
        write(state_path, state)
        return False
    next_id = daemon._next_id(daemon.ledger.watermark)
    if len(next_id) != 8:
        state.update(phase="error", error="command ID range exhausted")
        write(state_path, state)
        return False
    prompt = prompt.replace(daemon.ch.prefix + "0001", next_id)
    prompt += "\n[SYS] Continue this channel; next command ID: " + next_id
    # Durable intent: a crash or ambiguous send must never cause automatic retry.
    state.update(phase="sending_activation", ts=time.time())
    write(state_path, state)
    try:
        sent = daemon.adapter.send_text(cdp, prompt)
    except Exception as exc:
        sent = False
        state["error"] = str(exc)
    if not sent:
        state.update(phase="confirmation_required", error=state.get("error", "activation send uncertain"))
        write(state_path, state)
        return False
    cfg.channel_path(letter, "logs", "activation_sent.flag").write_text("provider switch", encoding="utf-8")
    state.update(phase="ready", ts=time.time())
    write(state_path, state)
    pause_path = cfg.channel_path(letter, "logs", "paused.json")
    if read(pause_path, {}).get("by") == "provider_switch":
        write(pause_path, {"paused": state.get("previous_paused", False),
                           "by": "provider_switch", "since": time.time()})
    return True


class PrefixAdapter:
    """Filter every collection, including the daemon's post-coalesce collection."""
    def __init__(self, adapter, prefix):
        self.adapter, self.prefix = adapter, prefix

    def __getattr__(self, name):
        return getattr(self.adapter, name)

    def collect_blocks(self, cdp, last_n=3):
        return [b for b in self.adapter.collect_blocks(cdp, last_n=last_n)
                if b.id.startswith(self.prefix)]
