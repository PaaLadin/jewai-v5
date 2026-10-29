"""recovery.py - per-channel panel recovery.

Contract:
- Loop every --interval seconds. Check panel alive via /api/status?ch=X or CDP.
- If panel dead: check operator activity (via chrome.storage or kick-refuse).
  If operator is typing -> SKIP this tick.
- Otherwise reload page (F5) via CDP, cooldown between attempts.
- State file: Profiles/<L>/logs/svc_recovery_<L>.json. If state != on -> exit.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from Core.config import load as load_config  # noqa: E402


def _state_on(path: Path) -> bool:
    if not path.exists():
        return True
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("state") == "on"
    except Exception:
        return True


def _cdp_alive(port: int) -> bool:
    import urllib.request
    try:
        urllib.request.urlopen("http://127.0.0.1:%d/json/version" % port, timeout=2).read()
        return True
    except Exception:
        return False


def _operator_typing(port: int) -> bool:
    """Check if operator has non-empty textarea in any tab."""
    try:
        from Bridge.cdp import connect
        cdp = connect(port)
        try:
            expr = ("(() => { const ts = document.querySelectorAll('textarea');"
                    "for (const t of ts) { if (t.value && t.value.trim().length > 0 && !t.readOnly && !t.getAttribute('readonly')) { return 'busy'; } }"
                    "return 'idle'; })()")
            r = cdp.eval_expr(expr)
            return r == "busy"
        finally:
            try: cdp.close()
            except Exception: pass
    except Exception:
        return False


def _panel_alive(port: int) -> bool:
    """Check panel is responsive (sidepanel + no 'no-answer')."""
    try:
        from Bridge.cdp import connect
        cdp = connect(port)
        try:
            expr = ("(() => { const t = document.body ? document.body.innerText : '';"
                    "if (t.includes('no-answer') || t.includes('content no') || t.includes('content bad')) return 'dead';"
                    "return 'ok'; })()")
            return cdp.eval_expr(expr) == "ok"
        finally:
            try: cdp.close()
            except Exception: pass
    except Exception:
        return False


def _reload_page(port: int) -> bool:
    try:
        from Bridge.cdp import connect
        cdp = connect(port)
        try:
            cdp.eval_expr("location.reload(); 'ok'")
            return True
        finally:
            try: cdp.close()
            except Exception: pass
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True)
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--cooldown", type=int, default=300)
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()

    cfg = load_config()
    ch = cfg.channel(a.channel)
    state_path = cfg.channel_path(a.channel, "logs", "svc_recovery_%s.json" % a.channel.upper())

    print("[recovery %s] start interval=%ds cdp=%d" % (a.channel, a.interval, ch.cdp_port), flush=True)

    last_reload = 0.0
    while True:
        if not _state_on(state_path):
            print("[recovery %s] state off, exit" % a.channel, flush=True)
            return 0

        if not _cdp_alive(ch.cdp_port):
            print("[recovery %s] CDP down, skip (watchdog will alert)" % a.channel, flush=True)
        elif not _panel_alive(ch.cdp_port):
            if _operator_typing(ch.cdp_port):
                print("[recovery %s] panel dead BUT operator typing -> skip" % a.channel, flush=True)
            else:
                now = time.time()
                if now - last_reload >= a.cooldown:
                    ok = _reload_page(ch.cdp_port)
                    print("[recovery %s] reload=%s" % (a.channel, ok), flush=True)
                    last_reload = now

        if a.once:
            return 0
        time.sleep(max(10, a.interval))


if __name__ == "__main__":
    sys.exit(main())