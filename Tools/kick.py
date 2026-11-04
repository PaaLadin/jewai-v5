"""Tools/kick.py - kick message to another channel's chat via CDP.

Usage:
  python Tools/kick.py --to B --from A --text "[A>B] hello"
  python Tools/kick.py --to B --text "plain"

Wraps message with marker if --from is provided.
"""
from __future__ import annotations
import argparse, sys, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from Core.config import load as load_config
from Bridge.cdp import connect
from Bridge.run import _adapter_for


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", required=True, help="target channel letter (A-F)")
    ap.add_argument("--from", dest="from_ch", default="", help="source channel (optional)")
    ap.add_argument("--text", required=True)
    a = ap.parse_args()

    cfg = load_config()
    try:
        ch = cfg.channel(a.to.upper())
    except Exception as e:
        print("bad channel %s: %s" % (a.to, e)); return 2

    text = a.text
    if a.from_ch and not text.startswith("["):
        text = "[%s>%s] %s" % (a.from_ch.upper(), a.to.upper(), text)

    import urllib.request
    is_paused = False
    try:
        req = urllib.request.urlopen("http://127.0.0.1:%d/pause_state" % ch.agent_port, timeout=1.5)
        j = json.loads(req.read().decode("utf-8", "replace"))
        is_paused = bool(j.get("paused"))
    except Exception:
        pass

    if is_paused:
        buf_dir = os.path.join(cfg.root, "Profiles", a.to.upper(), "logs")
        os.makedirs(buf_dir, exist_ok=True)
        buf_file = os.path.join(buf_dir, "kick_buffer.jsonl")
        try:
            with open(buf_file, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": time.time(), "from": a.from_ch or "?", "text": text}, ensure_ascii=False) + "\n")
            print("kick %s -> %s: BUFFERED (target paused)" % (a.from_ch or "?", a.to))
            return 0
        except Exception as e:
            print("buffer failed:", e)
            return 5

    adapter = _adapter_for(ch.model)
    cdp = connect(ch.cdp_port, adapter.HOST)
    if not cdp:
        print("no chat target on %s (cdp %d)" % (a.to, ch.cdp_port)); return 3

    try:
        ok = adapter.send_text(cdp, text)
        print("kick %s -> %s: %s" % (a.from_ch or "?", a.to, "OK" if ok else "FAIL"))
        return 0 if ok else 4
    finally:
        try: cdp.close()
        except Exception: pass


if __name__ == "__main__":
    sys.exit(main())