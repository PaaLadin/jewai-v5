"""Bridge/run.py - daemon entrypoint per channel.

Usage:
  python C:/JewAI/Bridge/run.py --channel C
  python C:/JewAI/Bridge/run.py --channel D --once

Picks adapter by channel model (deepseek -> DeepSeek, qwen -> Qwen, alice -> Alice).
Runs Daemon in a loop. --once runs a single tick and exits (debug).
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from Core.config import load as load_config
from Bridge.cdp import connect
from Bridge.daemon import Daemon


ADAPTERS = {
    "deepseek": ("Adapters.deepseek", "DeepSeek"),
    "qwen": ("Adapters.qwen", "Qwen"),
    "alice": ("Adapters.alice", "Alice"),
    "google": ("Adapters.google", "Google"),
}


def _adapter_for(model: str):
    mod_name, cls_name = ADAPTERS.get(model.lower(), ADAPTERS["deepseek"])
    mod = __import__(mod_name, fromlist=[cls_name])
    return getattr(mod, cls_name)()


def _try_recreate_chat(cfg, letter, ch_port, adapter):
    """7C B-10: if CDP is alive but find_chat fails, open the chat tab via Target.createTarget.
    Uses logs/active_chat_<L>.json if present (from B-11 rebirth), otherwise a fresh chat URL.
    8C: do NOT auto-open chat while onboarding is unacknowledged.
    """
    import json as _j
    import urllib.request as _u
    # 8C B-48: only reopen chat AFTER onboarding acked. Before that — do not touch.
    try:
        _flag = cfg.channel_path(letter, "logs", "onboarding_disabled.flag")
        if not _flag.exists():
            return False
    except Exception:
        return False
    try:
        with _u.urlopen("http://127.0.0.1:%d/json/list" % ch_port, timeout=3) as r:
            targets = _j.loads(r.read().decode("utf-8"))
    except Exception:
        return False
    # need at least one page target to send Target.createTarget via CDP
    page_targets = [x for x in targets if x.get("type") == "page" and x.get("webSocketDebuggerUrl")]
    if not page_targets:
        return False
    # determine URL
    url = None
    active = cfg.path("logs", "active_chat_%s.json" % letter)
    if active.exists():
        try:
            d = _j.loads(active.read_text(encoding="utf-8"))
            u = d.get("chat_url")
            if u and (adapter.HOST in u):
                url = u
        except Exception:
            pass
    if not url:
        base = "https://" + adapter.HOST + "/"
        url = base
    try:
        from Bridge.cdp import CDP
        cdp = CDP(page_targets[0]["webSocketDebuggerUrl"])
        try:
            cdp.call("Target.createTarget", {"url": url})
        finally:
            cdp.close()
        return True
    except Exception:
        return False


def _acquire_single_instance_mutex(channel: str):
    """8C B-40: Windows named mutex — only ONE Bridge per channel can run.
    OS auto-releases on process exit. Returns handle (keep alive) or None.
    """
    try:
        import ctypes
        name = "Local\\JewAI_Bridge_" + channel
        k32 = ctypes.windll.kernel32
        k32.CreateMutexW.restype = ctypes.c_void_p
        h = k32.CreateMutexW(None, True, name)
        if not h:
            print("[Bridge %s] mutex create failed (err=%d), exiting." % (channel, ctypes.get_last_error()), flush=True)
            return None
        last = k32.GetLastError()
        if last == 183:
            print("[Bridge %s] Duplicate instances detected, exiting." % channel, flush=True)
            return None
        return h
    except Exception as _e:
        print("[Bridge %s] mutex init err: %s" % (channel, _e), flush=True)
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True, choices=["A", "B", "C", "D", "E", "F"])
    ap.add_argument("--once", action="store_true", help="single tick, then exit")
    ap.add_argument("--config", default=None)
    a = ap.parse_args()

    # 8C B-40: single instance per channel (skip for --once diagnostics)
    _mutex = None if a.once else _acquire_single_instance_mutex(a.channel)
    if not a.once and _mutex is None:
        return 3
    cfg = load_config(a.config)
    ch = cfg.channel(a.channel)
    adapter = _adapter_for(ch.model)
    daemon = Daemon(cfg, a.channel, adapter)

    if a.once:
        cdp = connect(ch.cdp_port, adapter.HOST)
        if not cdp:
            print("no_chat_target port=%d host=%s" % (ch.cdp_port, adapter.HOST))
            return 2
        try:
            r = daemon.tick(cdp)
            print("processed=%d skipped=%d errors=%d" % (r.processed, r.skipped, r.errors))
            return 0
        finally:
            try: cdp.close()
            except Exception: pass

    # continuous loop with auto-reconnect
    backoff = 2.0
    while True:
        cdp = connect(ch.cdp_port, adapter.HOST)
        if not cdp:
            # 7C B-10: try to recreate the chat tab if CDP is alive
            _recreate_attempted = getattr(main, "_recreate_attempted", 0.0)
            now_ts = time.time()
            if now_ts - _recreate_attempted > 30.0:
                ok = _try_recreate_chat(cfg, a.channel, ch.cdp_port, adapter)
                if ok:
                    print("b10: recreated chat tab for %s at %s" % (a.channel, adapter.HOST), flush=True)
                main._recreate_attempted = now_ts
            time.sleep(min(backoff, 10.0))
            backoff = min(backoff * 1.2, 10.0)
            continue
        backoff = 2.0
        try:
            daemon.tick(cdp)
        except Exception:
            pass
        finally:
            try: cdp.close()
            except Exception: pass
        time.sleep(daemon.poll_ms / 1000.0)


if __name__ == "__main__":
    sys.exit(main())