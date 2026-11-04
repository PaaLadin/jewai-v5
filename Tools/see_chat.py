"""sandbox/see_chat.py - screenshot + innerText of a channel's chat via CDP.

Port of DeepSeek sandbox/see_chat.py (AUDIT section 11), adapted for v5.

Usage:
  python Tools/see_chat.py --channel B --out logs/B/see_B.png
  python Tools/see_chat.py --channel B --text-only --out logs/B/see_B.txt
  python Tools/see_chat.py --cdp 9123 --out logs/B/see_B.png
  python Tools/see_chat.py --channel B --text-only --maxlen 4000

Cyrillic in stdout breaks on the bridge -> always writes to file.
Prints only ASCII status line to stdout.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from Core.config import load as load_config  # noqa: E402
from Bridge.cdp import connect  # noqa: E402
from Bridge.run import _adapter_for  # noqa: E402


def _grab_png(cdp) -> bytes | None:
    try:
        cdp.call("Page.enable", {})
    except Exception:
        pass
    try:
        res = cdp.call("Page.captureScreenshot", {"format": "png"})
    except Exception:
        return None
    data = (res.get("result") or {}).get("data")
    if not data:
        return None
    try:
        return base64.b64decode(data)
    except Exception:
        return None


def _grab_text(cdp, maxlen: int) -> str:
    expr = ("(() => { const b = document.body; "
            "return b ? b.innerText.slice(0, %d) : ''; })()" % int(maxlen))
    try:
        t = cdp.eval_expr(expr)
        return t or ""
    except Exception:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", default="", help="channel letter (A-F)")
    ap.add_argument("--cdp", type=int, default=0, help="override CDP port")
    ap.add_argument("--out", default="", help="output path (png or txt)")
    ap.add_argument("--text-only", action="store_true", help="text instead of png")
    ap.add_argument("--maxlen", type=int, default=8000, help="text max chars")
    a = ap.parse_args()

    cfg = load_config()

    if a.cdp:
        ch = cfg.channel_by_cdp(a.cdp)
        cdp_port = a.cdp
        model = ch.model if ch else "deepseek"
        letter = ch.letter if ch else "?"
    elif a.channel:
        try:
            ch = cfg.channel(a.channel.upper())
        except Exception as e:
            print("bad channel: %s" % e)
            return 2
        cdp_port = ch.cdp_port
        model = ch.model
        letter = ch.letter
    else:
        print("need --channel or --cdp")
        return 2

    if not a.out:
        suffix = "txt" if a.text_only else "png"
        a.out = str(ROOT / "logs" / letter / ("see_%s.%s" % (letter, suffix)))

    adapter = _adapter_for(model)
    cdp = connect(cdp_port, adapter.HOST)
    if not cdp:
        print("no chat target on cdp %d" % cdp_port)
        return 3

    try:
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        if a.text_only:
            txt = _grab_text(cdp, a.maxlen)
            out.write_text(txt, encoding="utf-8", newline="\n")
            print("text %d chars -> %s" % (len(txt), out))
        else:
            png = _grab_png(cdp)
            if not png:
                print("screenshot FAIL")
                return 4
            out.write_bytes(png)
            print("png %d bytes -> %s" % (len(png), out))
        return 0
    finally:
        try:
            cdp.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())