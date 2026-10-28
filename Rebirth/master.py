"""Rebirth/master.py - orchestrator for rebirth cycle.

Contract (AUDIT section 26):
- check_gate(ch) -> verdict (limit | force | hold | threshold | deny)
- run(ch, live=False) -> result dict
- Lock file with TTL 1h
- NO Playwright. CDP cycle delegated to adapters.
- Ф4 minimal: gate + table advance only. Real CDP cycle wired in Ф5.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

from Core.config import Config
from Rebirth.table import Table
from Rebirth import cycle as _cycle


@dataclass
class GateVerdict:
    channel: str
    decision: str
    reason: str
    cmds: int | None
    limit: bool


class Master:
    def __init__(self, cfg: Config, letter: str):
        self.cfg = cfg
        self.letter = letter.upper()
        self.ch = cfg.channel(self.letter)
        self.rebirth_dir = cfg.path("logs", "rebirth")
        self.table = Table(self.rebirth_dir / "series_table.json")
        self.threshold = int(cfg.thresholds.get("rebirth_cmds", 850))
        self.lock_path = self.rebirth_dir / "rebirth.lock"

    def ready_flag(self) -> Path:
        return self.rebirth_dir / ("ready_%s.json" % self.letter)

    def force_flag(self) -> Path:
        return self.rebirth_dir / ("force_%s.flag" % self.letter)

    def hold_flag(self) -> Path:
        return self.rebirth_dir / ("hold_%s.flag" % self.letter)

    def read_ready(self) -> dict | None:
        p = self.ready_flag()
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None


    def check_gate(self) -> GateVerdict:
        ready = self.read_ready()
        if ready is None:
            return GateVerdict(self.letter, "deny", "no_ready_flag", None, False)
        cmds = ready.get("cmds")
        limit = bool(ready.get("limit"))
        if limit:
            return GateVerdict(self.letter, "allow", "limit", cmds, True)
        if self.force_flag().exists():
            return GateVerdict(self.letter, "allow", "force", cmds, False)
        if self.hold_flag().exists():
            return GateVerdict(self.letter, "deny", "hold", cmds, False)
        if cmds is not None and int(cmds) >= self.threshold:
            return GateVerdict(self.letter, "allow", "threshold", cmds, False)
        return GateVerdict(self.letter, "deny", "below_threshold", cmds, False)

    def acquire_lock(self) -> tuple[bool, dict]:
        if self.lock_path.exists():
            try:
                d = json.loads(self.lock_path.read_text(encoding="utf-8"))
                if time.time() - d.get("ts", 0) < 3600:
                    return False, d
            except Exception:
                pass
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        d = {"ch": self.letter, "ts": time.time()}
        self.lock_path.write_text(json.dumps(d), encoding="utf-8")
        return True, d

    def release_lock(self) -> None:
        try:
            self.lock_path.unlink()
        except Exception:
            pass


    def run(self, live: bool = False) -> dict:
        verdict = self.check_gate()
        out = {"channel": self.letter, "verdict": verdict.__dict__, "live": live}
        if verdict.decision != "allow":
            out["result"] = "deny"
            return out
        if not live:
            out["result"] = "dry_run_ok"
            return out
        got, d = self.acquire_lock()
        if not got:
            out["result"] = "locked"
            out["lock"] = d
            return out
        try:
            from Bridge.cdp import connect as _cdp_connect
            from Adapters.deepseek import DeepSeek as _DS
            from Adapters.qwen import Qwen as _QW
            from Adapters.alice import Alice as _AL
            _adapters = {"deepseek": _DS, "qwen": _QW, "alice": _AL}
            _cls = _adapters.get(self.ch.model, _DS)
            _adapter = _cls()
            _cdp = _cdp_connect(self.ch.cdp_port, _adapter.HOST)
            if not _cdp:
                out["result"] = "FAIL: no chat target"
                return out
            try:
                r = _cycle.run_cycle(self.cfg, self.letter, _adapter, _cdp, self.table)
            finally:
                try:
                    _cdp.close()
                except Exception:
                    pass
            out["cycle"] = r
            out["result"] = "cycle_ok" if r.get("ok") else "cycle_fail"
        finally:
            try:
                self.ready_flag().unlink()
            except Exception:
                pass
            if self.force_flag().exists():
                try:
                    self.force_flag().unlink()
                except Exception:
                    pass
            self.release_lock()
        return out


def set_ready(cfg: Config, letter: str, cmds: int | None, limit: bool, note: str = "") -> Path:
    d = cfg.path("logs", "rebirth")
    d.mkdir(parents=True, exist_ok=True)
    p = d / ("ready_%s.json" % letter.upper())
    p.write_text(json.dumps({
        "channel": letter.upper(), "ts": time.time(),
        "iso": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cmds": cmds, "limit": bool(limit), "note": note,
    }, ensure_ascii=False), encoding="utf-8")
    return p
