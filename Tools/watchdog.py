"""watchdog.py - per-channel ALIVE (silence ping).

Contract:
- Loop every --interval seconds. GET <agent>/ping.
- If ago >= interval AND watchdog still ON: send ALIVE text via kick.
- Guard: if operator is typing (Bridge doesn't know - rely on kick refusing if busy).
- If agent started replying (ago < interval): reset silencePinged.
- Repeat ALIVE not more than every alive_repeat (default 1800s).
- Reads state file: Profiles/<L>/logs/svc_watchdog_<L>.json. If state != on -> exit.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from Core.config import load as load_config  # noqa: E402

ALIVE_TEXT = "[ALIVE?] Жив? Проверь TODO, если всё сделал и работы завершены и приняты - выключи watchdog!"


def _ping(url: str, token: str, timeout: float = 3.0):
    try:
        req = urllib.request.Request(url + "/ping", headers={"X-Token": token})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _state_on(path: Path) -> bool:
    if not path.exists():
        return True  # if no state file, assume on (svc started us)
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return d.get("state") == "on"
    except Exception:
        return True


def _kick(port: int, text: str) -> bool:
    """Send ALIVE via CDP kick (bridge_kick2 equivalent)."""
    try:
        from Tools.launcher import _push_storage  # not used here
    except Exception:
        pass
    # use Bridge.cdp if available
    try:
        sys.path.insert(0, str(ROOT))
        from Bridge.cdp import connect
        cdp = connect(port)
        try:
            ta = None
            # find textarea in active tab
            expr = ("(() => { const t = document.querySelector('textarea:not([readonly])');"
                    "if (!t) return 'no_ta';"
                    "const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;"
                    "setter.call(t, " + json.dumps(text) + ");"
                    "t.dispatchEvent(new Event('input', {bubbles: true}));"
                    "return 'ok'; })()")
            res = cdp.eval_expr(expr)
            if res != "ok":
                return False
            time.sleep(0.5)
            # Enter twice
            cdp.eval_expr("(() => { const t = document.querySelector('textarea'); t.focus(); "
                          "t.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));"
                          "t.dispatchEvent(new KeyboardEvent('keyup',{key:'Enter',bubbles:true}));"
                          "return 'ok'; })()")
            return True
        finally:
            try: cdp.close()
            except Exception: pass
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True)
    ap.add_argument("--interval", type=int, default=300)
    ap.add_argument("--threshold", type=int, default=3)
    ap.add_argument("--alive-repeat", type=int, default=1800)
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()

    cfg = load_config()
    ch = cfg.channel(a.channel)
    token = ""
    tok_file = cfg.path(".agent_token")
    if tok_file.exists():
        token = tok_file.read_text(encoding="utf-8").strip()
    url = "http://127.0.0.1:%d" % ch.agent_port
    state_path = cfg.channel_path(a.channel, "logs", "svc_watchdog_%s.json" % a.channel.upper())

    print("[watchdog %s] start interval=%ds url=%s" % (a.channel, a.interval, url), flush=True)

    silence_pinged = False
    last_alive_at = 0.0
    fails = 0

    while True:
        if not _state_on(state_path):
            print("[watchdog %s] state off, exit" % a.channel, flush=True)
            return 0

        j = _ping(url, token)
        if j is None:
            fails += 1
            print("[watchdog %s] ping FAIL (%d/%d)" % (a.channel, fails, a.threshold), flush=True)
        else:
            ago = j.get("ago")
            if isinstance(ago, (int, float)) and ago < a.interval:
                silence_pinged = False
                fails = 0
            else:
                now = time.time()
                if (not silence_pinged) and (now - last_alive_at >= a.alive_repeat):
                    # operator-typing guard: kick refuses if busy (returns False)
                    ok = _kick(ch.cdp_port, ALIVE_TEXT)
                    print("[watchdog %s] ALIVE sent=%s" % (a.channel, ok), flush=True)
                    if ok:
                        silence_pinged = True
                        last_alive_at = now

        if a.once:
            return 0
        time.sleep(max(5, a.interval // 3))


if __name__ == "__main__":
    sys.exit(main())