"""Rebirth/monitor.py - rebirth supervision loop.

Contract (AUDIT_GAP 1, F4b):
- Thresholds: info 500, warn 700, critical 850 (config.thresholds).
- TTL of reminders: info once per series, warn 2h, critical 30min.
- Pending artifacts: pending_<CH>.json; verify mtime > since_ts and
  next_series marker in TODO/HANDOVER/PROMPT. Escalate after 30 min,
  up to 3 times, then operator.
- Hold mode: hold_<CH>.flag -> skip threshold, wait for chat limit.
- Lock: rebirth.lock, TTL 1h.
- Auto: ready_<CH>.json -> Master.run(live=True), one at a time.
- No Playwright, no subprocess to old scripts. ASCII-only.

Usage:
  python Tools/rebirth_monitor.py --once
  python Tools/rebirth_monitor.py --loop 600
  python Tools/rebirth_monitor.py --once --dry-run
"""
from __future__ import annotations

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

# 9C: single-instance guard. If another monitor runs, exit.
# Uses exclusive CreateFileW on logs/rebirth/monitor.lock (Windows).
try:
    import ctypes as _ct
    _MON_LOCK = ROOT / "logs" / "rebirth" / "monitor.lock"
    _MON_LOCK.parent.mkdir(parents=True, exist_ok=True)
    _k = _ct.windll.kernel32
    _h = _k.CreateFileW(str(_MON_LOCK), 0x40000000, 0, None, 4, 0x80, None)
    if _h in (None, -1, 0xFFFFFFFF, 0xFFFFFFFFFFFFFFFF):
        sys.stderr.write("rebirth_monitor: already running, exit\n")
        sys.exit(0)
except Exception:
    pass

from Core.config import load as load_config
from Rebirth.master import Master, set_ready
from Rebirth.table import Table


DEFAULT_THRESHOLDS = {"info": 500, "warn": 700, "critical": 850}
TTL = {"info": 0, "warn": 7200, "critical": 1800}
ESCALATE_AFTER = 1800
ESCALATE_MAX = 3

def _num_id(idstr: str) -> int | None:
    try:
        return int(idstr[4:])
    except Exception:
        return None


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _log(path: Path, msg: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write("[%s] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))


_LAST_KICK = {}


def _recent_kick(ch, window_sec=600):
    """9C: cooldown between any kicks per channel (default 10 min)."""
    now = time.time()
    last = _LAST_KICK.get(ch, 0)
    if (now - last) < window_sec:
        return True
    _LAST_KICK[ch] = now
    return False


class Monitor:
    def __init__(self, cfg, dry_run: bool = False):
        self.cfg = cfg
        self.dry = dry_run
        self.dir = cfg.path("logs", "rebirth")
        self.dir.mkdir(parents=True, exist_ok=True)
        self.log = self.dir / "watchdog.log"
        self.table = Table(self.dir / "series_table.json")
        self.table.load()
        self.th = dict(DEFAULT_THRESHOLDS)
        self.th.update({k: int(v) for k, v in (cfg.thresholds or {}).items()
                        if k in ("info", "warn", "critical")})
        self.threshold = int(cfg.thresholds.get("rebirth_cmds", 850))

    def _reminder_log(self) -> Path:
        return self.dir / "reminders.jsonl"

    def reminder_fired(self, ch: str, level: str) -> bool:
        p = self._reminder_log()
        if not p.exists():
            return False
        ttl = TTL.get(level, 1800)
        cutoff = (time.time() - ttl) if ttl else 0
        try:
            for line in p.read_text(encoding="utf-8").splitlines():
                try:
                    j = json.loads(line)
                except Exception:
                    continue
                if j.get("ch") != ch:
                    continue
                if level == "info":
                    if j.get("level") in ("info", "warn", "critical"):
                        return True
                elif j.get("level") == level and j.get("ts", 0) > cutoff:
                    return True
        except Exception:
            return False
        return False

    def log_reminder(self, ch: str, level: str, cmds: int) -> None:
        with self._reminder_log().open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "ch": ch, "level": level,
                                "cmds": cmds}, ensure_ascii=False) + "\n")

    def last_id_of(self, letter: str) -> str | None:
        """10C: lastId via agent /status OR ledger_<L>.json watermark.

        10C-REBIRTH-NO-LAST-ID fix:
          v5 agent.py has /ping, /svc_status, /live - но нет /status.
          Раньше Monitor всегда возвращал no_last_id и порог 850 не работал.
          Теперь после неудачи HTTP читаем Profiles/<L>/logs/ledger_<L>.json
          (поле watermark - последний исполненный id, пишет Bridge/exec.py::Ledger).
        """
        ch = self.cfg.channel(letter)
        url = "http://127.0.0.1:%d/status" % ch.agent_port
        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=5) as r:
                j = json.loads(r.read().decode("utf-8", "replace"))
            lid = j.get("lastId") or j.get("last_id")
            if lid:
                return lid
        except Exception:
            pass
        # Fallback: читаем ledger-файл напрямую
        try:
            lp = self.cfg.channel_path(letter, "logs", "ledger_%s.json" % letter)
            if lp.exists():
                data = json.loads(lp.read_text(encoding="utf-8"))
                wm = str(data.get("watermark") or "").strip()
                if wm:
                    return wm
        except Exception:
            pass
        return None

    def pending_path(self, ch: str) -> Path:
        return self.dir / ("pending_%s.json" % ch)

    def expected_artifacts(self, ch: str, info: dict) -> dict:
        ns = info.get("next_series", "")
        return {
            self.cfg.path("logs", ch, "TODO.md"): ns,
            self.cfg.path("logs", ch, "HANDOVER.md"): ns,
            self.cfg.path("emergency", "PROMPT_%s.md" % ns): ns,
            self.cfg.path("SESSION_STATE.md"): None,
        }

    def verify_artifacts(self, ch: str, info: dict, since_ts: float) -> list:
        missing = []
        for path, marker in self.expected_artifacts(ch, info).items():
            if not path.exists():
                missing.append(path.name + " (missing)")
                continue
            try:
                mt = path.stat().st_mtime
            except Exception:
                missing.append(path.name + " (no mtime)")
                continue
            if since_ts and mt < since_ts:
                missing.append(path.name + " (stale)")
                continue
            if marker:
                try:
                    txt = path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    txt = ""
                if marker not in txt:
                    missing.append(path.name + " (no %s)" % marker)
        return missing

    def check_pending(self) -> None:
        for pf in sorted(self.dir.glob("pending_*.json")):
            j = _read_json(pf)
            if not j:
                continue
            ch = j.get("ch")
            if not ch:
                continue
            try:
                info = self.table.get(ch)
            except Exception:
                continue
            ts0 = float(j.get("ts", 0))
            age = time.time() - ts0
            missing = self.verify_artifacts(ch, info, ts0)
            if not missing:
                try:
                    pf.unlink()
                except Exception:
                    pass
                _log(self.log, "PENDING %s: artifacts VERIFIED (age %.0fs)" % (ch, age))
                continue
            esc = int(j.get("escalated", 0))
            if age > ESCALATE_AFTER and esc < ESCALATE_MAX:
                j["escalated"] = esc + 1
                j["ts"] = time.time()
                if not self.dry:
                    _write_json(pf, j)
                _log(self.log, "PENDING %s: escalate #%d, missing %d"
                     % (ch, esc + 1, len(missing)))

    def kick(self, ch: str, text: str) -> None:
        if self.dry:
            _log(self.log, "DRY kick %s: %s" % (ch, text[:80]))
            return
        # 9C: cooldown — no kicks within 10 min on same channel
        if _recent_kick(ch, 600):
            _log(self.log, "kick %s skipped (cooldown 10m)" % ch)
            return
        try:
            import subprocess
            kick = self.cfg.path("Tools", "kick.py")
            subprocess.run([sys.executable, str(kick), "--to", ch, "--from", "LA",
                            "--text", text], capture_output=True, text=True, timeout=30,
                           cwd=str(self.cfg.root))
        except Exception as e:
            _log(self.log, "kick %s ERR: %r" % (ch, e))

    def check_channel(self, letter: str) -> dict:
        try:
            info = self.table.get(letter)
        except Exception:
            return {"ch": letter, "status": "no_table"}
        lid = self.last_id_of(letter)
        if not lid:
            return {"ch": letter, "status": "no_last_id"}
        n = _num_id(lid)
        start = _num_id(info.get("range", [""])[0] or "")
        if n is None or start is None:
            return {"ch": letter, "status": "parse_fail", "last_id": lid}
        # 9C: TABLE STALE guard. If lastId > range_end, table is behind;
        # skip kick, log warning. Operator must fix series_table.json.
        end_id = info.get("range", [None, None])[1]
        end_n = _num_id(end_id) if end_id else None
        if end_n is not None and n > end_n:
            _log(self.log, "TABLE STALE %s lastId=%s > range_end=%s" % (letter, lid, end_id))
            return {"ch": letter, "status": "table_stale", "last_id": lid,
                    "range_end": end_id}
        cmds = n - start
        level = None
        if cmds >= self.th["critical"]:
            level = "critical"
        elif cmds >= self.th["warn"]:
            level = "warn"
        elif cmds >= self.th["info"]:
            level = "info"
        if not level or self.reminder_fired(letter, level):
            return {"ch": letter, "status": "ok", "cmds": cmds, "last_id": lid}
        ns = info.get("next_series", "?")
        nr = info.get("next_range", ["?", "?"])
        msg = ("[LA>%s] cmds=%d (%s). Prepare TODO, HANDOVER, PROMPT_%s (%s-%s). "
               "When ready run rebirth_ready." % (letter, cmds, lid, ns, nr[0], nr[1]))
        self.kick(letter, msg)
        self.log_reminder(letter, level, cmds)
        if not self.dry:
            _write_json(self.pending_path(letter), {"ch": letter, "ts": time.time(),
                                                    "escalated": 0})
        _log(self.log, "reminder %s level=%s cmds=%d" % (letter, level, cmds))
        return {"ch": letter, "status": "reminded", "cmds": cmds, "level": level}

    def hold_check(self, letter: str) -> None:
        hold = self.dir / ("hold_%s.flag" % letter)
        if not hold.exists():
            return
        from Tools import chat_limit as _cl
        if self.dry:
            _log(self.log, "DRY hold check %s" % letter)
            return
        try:
            if _cl.check_chat_limit(self.cfg, letter):
                ready = self.dir / ("ready_%s.json" % letter)
                if not ready.exists():
                    set_ready(self.cfg, letter, None, True, "chat_limit")
                    _log(self.log, "CHAT-LIMIT %s -> ready flag set" % letter)
        except Exception as e:
            _log(self.log, "chat_limit %s ERR: %r" % (letter, e))

    def auto_rebirth(self) -> None:
        if self.dry:
            return
        for letter in self.cfg.letters:
            flag = self.dir / ("ready_%s.json" % letter)
            if not flag.exists():
                continue
            try:
                age = time.time() - flag.stat().st_mtime
            except Exception:
                age = 99999
            if age > 7200:
                _log(self.log, "flag %s stale, skip" % letter)
                continue
            _log(self.log, "READY %s -> Master.run(live=True)" % letter)
            try:
                m = Master(self.cfg, letter)
                r = m.run(live=True)
                _log(self.log, "Master %s result=%s" % (letter, r.get("result")))
            except Exception as e:
                _log(self.log, "Master %s ERR: %r" % (letter, e))
            return

    def tick(self) -> dict:
        summary = []
        for letter in self.cfg.letters:
            summary.append(self.check_channel(letter))
        self.check_pending()
        for letter in self.cfg.letters:
            self.hold_check(letter)
        self.auto_rebirth()
        return {"ts": time.time(), "channels": summary}


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--loop", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    cfg = load_config()
    mon = Monitor(cfg, dry_run=a.dry_run)
    if a.loop:
        while True:
            r = mon.tick()
            print(json.dumps(r, ensure_ascii=True))
            time.sleep(a.loop)
    else:
        r = mon.tick()
        print(json.dumps(r, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

