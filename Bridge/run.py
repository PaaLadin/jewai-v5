"""Channel bridge entrypoint. Provider changes apply between complete ticks."""
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
from Adapters.registry import PROVIDERS, create

ADAPTERS = {k: (v["module"], v["class"]) for k, v in PROVIDERS.items()}


def _adapter_for(model: str):
    return create(model)


def _try_recreate_chat(cfg, letter, ch_port, adapter):
    """Only recreate after onboarding; never replace a pinned provider session."""
    import json
    import urllib.request
    from urllib.parse import urlparse
    try:
        state = cfg.channel_path(letter, "logs", "provider_state.json")
        if state.exists() and json.loads(state.read_text(encoding="utf-8")).get("target"):
            return False
        if not cfg.channel_path(letter, "logs", "onboarding_disabled.flag").exists():
            return False
        with urllib.request.urlopen("http://127.0.0.1:%d/json/list" % ch_port, timeout=3) as r:
            targets = json.loads(r.read().decode("utf-8"))
        pages = [t for t in targets if t.get("type") == "page" and t.get("webSocketDebuggerUrl")]
        if not pages:
            return False
        url = "https://" + adapter.HOST + "/"
        active = cfg.path("logs", "active_chat_%s.json" % letter)
        if active.exists():
            try:
                candidate = json.loads(active.read_text(encoding="utf-8")).get("chat_url", "")
                if urlparse(candidate).hostname == adapter.HOST:
                    url = candidate
            except (ValueError, OSError):
                pass
        from Bridge.cdp import CDP
        cdp = CDP(pages[0]["webSocketDebuggerUrl"])
        try:
            cdp.call("Target.createTarget", {"url": url})
        finally:
            cdp.close()
        return True
    except Exception:
        return False


def _acquire_single_instance_mutex(channel: str):
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        k32.CreateMutexW.restype = ctypes.c_void_p
        handle = k32.CreateMutexW(None, True, "Local\\JewAI_Bridge_" + channel)
        if not handle:
            print("[Bridge %s] mutex create failed" % channel, flush=True)
            return None
        if k32.GetLastError() == 183:
            k32.CloseHandle.argtypes = [ctypes.c_void_p]
            k32.CloseHandle(handle)
            print("[Bridge %s] Duplicate instances detected, exiting." % channel, flush=True)
            return None
        return handle
    except Exception as exc:
        print("[Bridge %s] mutex init err: %s" % (channel, exc), flush=True)
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True, type=str.upper)
    ap.add_argument("--once", action="store_true", help="single tick, then exit")
    ap.add_argument("--config", default=None)
    args = ap.parse_args()
    try:
        cfg = load_config(args.config)
        ch = cfg.channel(args.channel)
        adapter = _adapter_for(ch.model)
    except (KeyError, ValueError, OSError) as exc:
        ap.error(str(exc))
    mutex = _acquire_single_instance_mutex(args.channel)
    if mutex is None:
        return 3
    daemon = Daemon(cfg, args.channel, adapter)
    if args.once:
        cdp = connect(ch.cdp_port, adapter.HOST)
        if not cdp:
            print("no_chat_target port=%d host=%s" % (ch.cdp_port, adapter.HOST))
            return 2
        try:
            result = daemon.tick(cdp)
            print("processed=%d skipped=%d errors=%d" %
                  (result.processed, result.skipped, result.errors))
            return 0
        finally:
            cdp.close()
    from Bridge.provider_switch import consume, bound_connect, initialize, PrefixAdapter
    adapter = PrefixAdapter(adapter, ch.prefix)
    daemon = Daemon(cfg, args.channel, adapter)
    backoff = 2.0
    while True:
        cdp = None
        try:
            # This boundary is reached only after the previous tick and report finish.
            consume(cfg, args.channel)
            latest = load_config(args.config)
            fresh = latest.channel(args.channel)
            if fresh != ch:
                cfg, ch = latest, fresh
                adapter = PrefixAdapter(_adapter_for(ch.model), ch.prefix)
                daemon = Daemon(cfg, args.channel, adapter)
            cdp = bound_connect(cfg, args.channel, adapter)
            if not cdp:
                attempted = getattr(main, "_recreate_attempted", 0.0)
                now = time.time()
                if now - attempted > 30.0:
                    _try_recreate_chat(cfg, args.channel, ch.cdp_port, adapter)
                    main._recreate_attempted = now
                backoff = min(backoff * 1.2, 10.0)
            else:
                backoff = 2.0
                if initialize(cfg, args.channel, daemon, cdp):
                    daemon.tick(cdp)
        except Exception as exc:
            print("[Bridge %s] tick failed: %s" % (args.channel, exc), flush=True)
        finally:
            if cdp:
                cdp.close()
        time.sleep(backoff if not cdp else daemon.poll_ms / 1000.0)


if __name__ == "__main__":
    sys.exit(main())
