"""Rebirth/table.py - series table: advance channels through series.

Contract (from AUDIT sections 23, 25, 26):
- State file: logs/rebirth/series_table.json
- Per channel: current_series, range [start, end], next_series, next_range,
  prefix, last_id, last_id_source, chat_url, share_url
- advance(ch): current = next; range = next_range; next_series = _inc_series(current);
  next_range = [start+1000, end+1000]; last_id = range[0]
- Series format: <digits><letter> e.g. "13D", "14D". Range format: <prefix><4digits>
- No subprocess to sync_session_start in v5. No import from old rebirth_reset_ledger.
- Atomic write (write to .tmp then os.replace).
"""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SERIES_RE = re.compile(r"^([0-9]+)([A-Z])$")


def _inc_series(s: str) -> str:
    m = SERIES_RE.match(s or "")
    if not m:
        return s
    return "%d%s" % (int(m.group(1)) + 1, m.group(2))


def _inc_range(rng: list[str]) -> list[str]:
    if not rng or len(rng) != 2:
        return rng
    pref = rng[0][:4]
    a = int(rng[0][4:])
    b = int(rng[1][4:])
    return ["%s%04d" % (pref, a + 1000), "%s%04d" % (pref, b + 1000)]


@dataclass
class AdvanceResult:
    channel: str
    old_series: str
    new_series: str
    new_range: list[str]


class Table:
    def __init__(self, table_path: Path):
        self.path = table_path
        self._data: dict[str, Any] = {}

    def load(self) -> None:
        if not self.path.exists():
            self._data = {"channels": {}}
            return
        self._data = json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    def channel(self, letter: str) -> dict[str, Any]:
        ch = self._data.setdefault("channels", {}).get(letter)
        if ch is None:
            raise KeyError("unknown channel: " + letter)
        return ch

    def advance(self, letter: str, new_url: str = "", share_url: str = "") -> AdvanceResult:
        if not self._data:
            self.load()
        ch = self.channel(letter)
        old = ch["current_series"]
        ch["current_series"] = ch["next_series"]
        ch["range"] = list(ch["next_range"])
        ch["next_series"] = _inc_series(ch["current_series"])
        ch["next_range"] = _inc_range(ch["range"])
        ch["last_id"] = ch["range"][0]
        ch["last_id_source"] = "Rebirth/table %s" % time.strftime("%Y-%m-%d %H:%M")
        if new_url:
            ch["chat_url"] = new_url
        if share_url:
            ch["share_url"] = share_url
        self._save()
        return AdvanceResult(letter, old, ch["current_series"], list(ch["range"]))

    def get(self, letter: str) -> dict[str, Any]:
        if not self._data:
            self.load()
        return dict(self.channel(letter))


def default_table_template() -> dict:
    out: dict[str, Any] = {"channels": {}}
    seed = {
        "A": ("13A", "AAAB", "AAA"), "B": ("13B", "BBAB", "BBB"),
        "C": ("13C", "CCAB", "CCC"), "D": ("13D", "DDAB", "DDD"),
        "E": ("13E", "QQAB", "QQQ"), "F": ("13F", "FFAB", "FFF"),
    }
    for L, (series, pref, _) in seed.items():
        start = "%s3000" % pref
        end = "%s3999" % pref
        out["channels"][L] = {
            "current_series": series,
            "range": [start, end],
            "next_series": _inc_series(series),
            "next_range": _inc_range([start, end]),
            "prefix": pref,
            "last_id": start,
            "last_id_source": "template",
            "chat_url": "",
            "share_url": "",
        }
    return out