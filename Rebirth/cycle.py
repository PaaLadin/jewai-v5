"""Rebirth/cycle.py - real CDP cycle (create_chat -> send_prompt -> verify -> advance).

Contract (AUDIT section 27, rewritten from scratch, no Playwright):
- load PROMPT_<next_series>.md and 0_ACTIVATION.md.
- send header + body to a NEW chat via adapter.send_text.
- verify hits >= MIN_HITS: markers from PROMPT.
- on success: advance table; append log to rebirth_log.jsonl.
- on failure: do NOT advance, log FAIL.

MIN_HITS = 1 (any marker present in body).
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from Core.config import Config
from Rebirth.table import Table


MIN_HITS = 1
MARKER_MIN_LEN = 40
MARKERS_MAX = 3


def extract_markers(prompt_text: str) -> list[str]:
    """Take first N long non-header non-separator lines. Used as verification markers."""
    out: list[str] = []
    for line in prompt_text.splitlines():
        s = line.strip()
        if len(s) < MARKER_MIN_LEN:
            continue
        if s.startswith("#") or s.startswith("---"):
            continue
        out.append(s[:60])
        if len(out) >= MARKERS_MAX:
            break
    return out


def load_prompt(cfg: Config, letter: str, next_series: str) -> Path | None:
    """Look for PROMPT_<next_series>.md in cfg.root/logs/<CH>/, else rebirth/, else RAG/."""
    fn = "PROMPT_%s.md" % next_series
    cands = [
        cfg.path("logs", letter.upper(), fn),
        cfg.path("logs", "rebirth", fn),
        cfg.path("RAG", "procedures", fn),
    ]
    for p in cands:
        if p.exists():
            return p
    return None


def append_log(cfg: Config, entry: dict) -> None:
    p = cfg.path("logs", "rebirth", "rebirth_log.jsonl")
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_cycle(cfg: Config, letter: str, adapter: Any, cdp: Any, table: Table) -> dict:
    """Execute real CDP cycle. Returns dict with result and details.

    adapter: object with new_chat(cdp), send_text(cdp, text), verify_prompt_hits(cdp, markers).
    cdp: object with eval_expr(expr) (for current_url probe).
    table: Table instance for series table.
    """
    ch = cfg.channel(letter)
    info = table.get(letter)
    next_series = info.get("next_series", "")
    if not next_series:
        return {"ok": False, "error": "no next_series in table"}

    prompt_path = load_prompt(cfg, letter, next_series)
    if prompt_path is None:
        return {"ok": False, "error": "PROMPT not found for " + next_series}
    prompt_text = prompt_path.read_text(encoding="utf-8", errors="replace")
    markers = extract_markers(prompt_text)
    if not markers:
        return {"ok": False, "error": "no markers in PROMPT (too short?)"}

    header = "%s %s" % (next_series, ch.name)
    
    # Replace placeholders in prompt text
    prompt_text = prompt_text.replace("{{AGENT_NAME}}", ch.name)
    prompt_text = prompt_text.replace("{{CHANNEL_LETTER}}", letter.upper())
    prompt_text = prompt_text.replace("{{SERIES}}", next_series)
    prompt_text = prompt_text.replace("{{ID_PREFIX}}", ch.prefix)
    
    body = header + "\n\n" + prompt_text
    t0 = time.time()

    try:
        adapter.new_chat(cdp)
    except Exception as e:
        append_log(cfg, {"ts": time.time(), "ch": letter, "old_series": info.get("current_series"),
                         "new_series": next_series, "result": "FAIL: new_chat", "error": str(e)[:200]})
        return {"ok": False, "error": "new_chat: " + str(e)[:200]}

    time.sleep(2.0)

    sent = False
    try:
        sent = adapter.send_text(cdp, body)
    except Exception as e:
        append_log(cfg, {"ts": time.time(), "ch": letter, "old_series": info.get("current_series"),
                         "new_series": next_series, "result": "FAIL: send_text", "error": str(e)[:200]})
        return {"ok": False, "error": "send_text: " + str(e)[:200]}
    if not sent:
        append_log(cfg, {"ts": time.time(), "ch": letter, "old_series": info.get("current_series"),
                         "new_series": next_series, "result": "FAIL: send_text returned False"})
        return {"ok": False, "error": "send_text returned False"}

    time.sleep(5.0)

    hits = 0
    try:
        hits = adapter.verify_prompt_hits(cdp, markers) or 0
    except Exception as e:
        hits = 0
    elapsed = round(time.time() - t0, 1)

    new_url = ""
    try:
        new_url = cdp.eval_expr("location.href") or ""
    except Exception:
        pass


    if hits < MIN_HITS:
        append_log(cfg, {"ts": time.time(), "ch": letter, "old_series": info.get("current_series"),
                         "new_series": next_series, "new_url": new_url,
                         "hits": hits, "markers_total": len(markers),
                         "elapsed": elapsed, "result": "FAIL: prompt not verified"})
        return {"ok": False, "error": "verify failed", "hits": hits, "markers_total": len(markers),
                "new_url": new_url, "elapsed": elapsed}

    try:
        adv = table.advance(letter, new_url=new_url)
    except Exception as e:
        append_log(cfg, {"ts": time.time(), "ch": letter, "old_series": info.get("current_series"),
                         "new_series": next_series, "new_url": new_url,
                         "hits": hits, "result": "FAIL: advance", "error": str(e)[:200]})
        return {"ok": False, "error": "advance: " + str(e)[:200],
                "hits": hits, "new_url": new_url}

    append_log(cfg, {"ts": time.time(), "ch": letter, "old_series": adv.old_series,
                     "new_series": adv.new_series, "new_url": new_url,
                     "hits": hits, "markers_total": len(markers),
                     "elapsed": elapsed, "result": "OK"})
    return {"ok": True, "hits": hits, "markers_total": len(markers),
            "elapsed": elapsed, "new_url": new_url,
            "old_series": adv.old_series, "new_series": adv.new_series,
            "new_range": adv.new_range}
