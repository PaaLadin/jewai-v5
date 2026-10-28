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
}


def _adapter_for(model: str):
    mod_name, cls_name = ADAPTERS.get(model.lower(), ADAPTERS["deepseek"])
    mod = __import__(mod_name, fromlist=[cls_name])
    return getattr(mod, cls_name)()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True, choices=["A", "B", "C", "D", "E", "F"])
    ap.add_argument("--once", action="store_true", help="single tick, then exit")
    ap.add_argument("--config", default=None)
    a = ap.parse_args()

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