"""Channel bridge entrypoint; provider metadata lives in Adapters.registry."""
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
    """Only recreate after onboarding; do not touch unacknowledged profiles."""
    import json
    import urllib.request
    from urllib.parse import urlparse
    try:
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
    """Windows named mutex; retain returned handle for the process lifetime."""
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
    backoff = 2.0
    while True:
        cdp = connect(ch.cdp_port, adapter.HOST)
        if not cdp:
            attempted = getattr(main, "_recreate_attempted", 0.0)
            now = time.time()
            if now - attempted > 30.0:
                if _try_recreate_chat(cfg, args.channel, ch.cdp_port, adapter):
                    print("b10: recreated chat tab for %s at %s" %
                          (args.channel, adapter.HOST), flush=True)
                main._recreate_attempted = now
            time.sleep(min(backoff, 10.0))
            backoff = min(backoff * 1.2, 10.0)
            continue
        backoff = 2.0
        try:
            daemon.tick(cdp)
        except Exception as exc:
            print("[Bridge %s] tick failed: %s" % (args.channel, exc), flush=True)
        finally:
            cdp.close()
        time.sleep(daemon.poll_ms / 1000.0)


if __name__ == "__main__":
    sys.exit(main())
