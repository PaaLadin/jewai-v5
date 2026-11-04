"""Tools/token_counter.py - token estimate and level for a channel.

Contract (AUDIT_GAP 2, F5b):
- Formula: latin/4 + cyr/2.5 + other/4 over chat innerText.
- Limit: 3600 (config.thresholds.token_limit, default 3600).
- Levels: <80 green; 80-90 yellow blink 2s; 90-95 red blink 1s + voice;
  >=95 red blink 0.5s + voice.
- Hysteresis: <75 clears warned (so it re-arms).
- Reset: button or first thing after rebirth. Clears estimate, percent,
  warned, level, sendCount, sessionStartTs.
- Snowball = estimate * sendCount (cumulative load).
- State file: logs/<CH>/token_state.json (atomic write).
- ASCII-only, stdlib only.

Usage:
  python Tools/token_counter.py --channel A --once
  python Tools/token_counter.py --channel A --text-file path.txt
  python Tools/token_counter.py --channel A --reset
  python Tools/token_counter.py --channel A --send   (increment sendCount)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


def _find_root(start: Path) -> Path:
    p = start.resolve()
    for _ in range(8):
        if (p / "Core" / "config.py").is_file():
            return p
        if p.parent == p:
            break
        p = p.parent
    return start.parent


HERE = Path(__file__).resolve().parent
ROOT = _find_root(HERE)
sys.path.insert(0, str(ROOT))

DEFAULT_LIMIT = 3600
LEVELS = {"green": 0, "yellow": 80, "red1": 90, "red2": 95}
HYSTERESIS = 75


def estimate_tokens(text: str) -> int:
    """latin/4 + cyr/2.5 + other/4, rounded."""
    latin = cyr = other = 0
    for ch in text:
        o = ord(ch)
        if o < 128:
            latin += 1
        elif 0x0400 <= o <= 0x04FF:
            cyr += 1
        else:
            other += 1
    return int(latin / 4.0 + cyr / 2.5 + other / 4.0 + 0.5)


def level_for(percent: float) -> str:
    if percent >= LEVELS["red2"]:
        return "red95"
    if percent >= LEVELS["red1"]:
        return "red90"
    if percent >= LEVELS["yellow"]:
        return "yellow"
    return "ok"


def blink_ms(level: str) -> int:
    return {"red95": 500, "red90": 1000, "yellow": 2000}.get(level, 0)


def voice_needed(level: str) -> bool:
    return level in ("red90", "red95")


def state_path(cfg, letter: str) -> Path:
    p = cfg.channel_path(letter, "logs")
    p.mkdir(parents=True, exist_ok=True)
    return p / "token_state.json"


def load_state(cfg, letter: str) -> dict:
    p = state_path(cfg, letter)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"estimate": 0, "percent": 0.0, "level": "ok", "warned": False,
            "sendCount": 0, "sessionStartTs": time.time(),
            "limit": DEFAULT_LIMIT, "updated": 0}


def save_state(cfg, letter: str, st: dict) -> None:
    p = state_path(cfg, letter)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def update(cfg, letter: str, text: str | None = None,
           send_delta: int = 0, limit: int | None = None) -> dict:
    st = load_state(cfg, letter)
    if limit:
        st["limit"] = limit
    lim = st.get("limit") or DEFAULT_LIMIT
    if text is not None:
        est = estimate_tokens(text)
        st["estimate"] = est
        st["percent"] = round(est * 100.0 / lim, 2)
        lvl = level_for(st["percent"])
        if lvl != "ok" and not st.get("warned"):
            st["warned"] = True
        if st["percent"] < HYSTERESIS:
            st["warned"] = False
        st["level"] = lvl
    if send_delta:
        st["sendCount"] = int(st.get("sendCount", 0)) + send_delta
    st["snowball"] = int(st.get("estimate", 0)) * int(st.get("sendCount", 0))
    st["updated"] = time.time()
    save_state(cfg, letter, st)
    return st


def reset(cfg, letter: str) -> dict:
    st = {"estimate": 0, "percent": 0.0, "level": "ok", "warned": False,
          "sendCount": 0, "sessionStartTs": time.time(),
          "limit": DEFAULT_LIMIT, "snowball": 0, "updated": time.time()}
    save_state(cfg, letter, st)
    return st

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--text-file", default="")
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    from Core.config import load as load_config
    cfg = load_config()
    L = a.channel.upper()
    if a.reset:
        st = reset(cfg, L)
        print(json.dumps(st, ensure_ascii=True))
        return 0
    text = None
    if a.text_file:
        text = Path(a.text_file).read_text(encoding="utf-8", errors="replace")
    if text is None and a.once:
        # read chat innerText via CDP
        try:
            from Bridge.cdp import connect
            from Bridge.run import _adapter_for
            ch = cfg.channel(L)
            ad = _adapter_for(ch.model)
            cdp = connect(ch.cdp_port, ad.HOST)
            if cdp:
                text = cdp.eval_expr("document.body ? document.body.innerText : ''") or ""
                cdp.close()
        except Exception:
            text = ""
    st = update(cfg, L, text=text, send_delta=(1 if a.send else 0),
                limit=(a.limit or None))
    print(json.dumps(st, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

