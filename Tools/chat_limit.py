"""Tools/chat_limit.py - detect chat overflow banner.

Contract (AUDIT_GAP 1, F4b):
- Read chat DOM via CDP (native, no Playwright).
- Banner only: short element (<=160 chars), most nested, contains phrase.
- Phrases are passed as JSON with ensure_ascii=True (file stays ASCII).
- Print LIMIT or OK.

Usage: python Tools/chat_limit.py --channel A
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from Core.config import load as load_config
from Bridge.cdp import connect
from Bridge.run import _adapter_for


PHRASES = [
    "\u043f\u0440\u0435\u0434\u0435\u043b \u0434\u043b\u0438\u043d\u044b",
    "\u043f\u0440\u0435\u0432\u044b\u0448\u0435\u043d \u043b\u0438\u043c\u0438\u0442",
    "length limit reached",
    "please start a new chat",
]


_BANNER_JS = (
    "(() => {"
    " const ph = " + json.dumps(PHRASES, ensure_ascii=True) + ";"
    " const els = Array.from(document.querySelectorAll('div,span,p,section'));"
    " for (const e of els) {"
    "  const t = (e.innerText || '').trim().toLowerCase();"
    "  if (!t || t.length > 160) continue;"
    "  if (e.querySelector('div,span,p')) continue;"
    "  for (const p of ph) if (t.includes(p)) return p;"
    " }"
    " return '';"
    "})()"
)


def check_chat_limit(cfg, letter: str) -> bool:
    ch = cfg.channel(letter.upper())
    adapter = _adapter_for(ch.model)
    cdp = connect(ch.cdp_port, adapter.HOST)
    if not cdp:
        return False
    try:
        return bool(cdp.eval_expr(_BANNER_JS))
    finally:
        try:
            cdp.close()
        except Exception:
            pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True)
    a = ap.parse_args()
    cfg = load_config()
    hit = check_chat_limit(cfg, a.channel)
    print("LIMIT" if hit else "OK")
    return 0 if hit else 1


if __name__ == "__main__":
    sys.exit(main())