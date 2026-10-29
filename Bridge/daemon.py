"""Bridge/daemon.py — цикл моста для одного канала.

Контракт (AUDIT §19, §29):
- Загрузить config, адаптер канала.
- Найти CDP-вкладку чата по HOST.
- Цикл poll_ms:
    stable-gate (pre-count не менялся stable_ms) ->
    collect_blocks(last_n) -> ledger.check ->
    exec.execute -> отправить [AGENT REPORT] через адаптер.
- Replay-guard: водяной знак + хэш в файле.
- inflight: не начинать новый цикл пока предыдущий не завершён; auto-reset через 45с.
- min_gap: не чаще, чем раз в min_gap_ms.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from Bridge.cdp import CDP, connect
from Bridge.exec import Block, Ledger, execute
from Core.config import Config, load as load_config


@dataclass
class DaemonResult:
    channel: str
    processed: int
    skipped: int
    errors: int


class Daemon:
    def __init__(self, cfg: Config, letter: str, adapter: Any):
        self.cfg = cfg
        self.letter = letter.upper()
        self.ch = cfg.channel(self.letter)
        self.adapter = adapter
        # 11B: per-agent ledger in Profiles/<L>/logs
        bridge_logs = cfg.channel_path(self.letter, "logs")
        bridge_logs.mkdir(parents=True, exist_ok=True)
        self.ledger = Ledger(
            ledger_path=bridge_logs / f"ledger_{self.letter}.json",
            stale_log_path=bridge_logs / f"stale_{self.letter}.log",
        )
        self.poll_ms = int(cfg.timeouts.get("cdp_poll", 2000))
        self.stable_ms = int(cfg.timeouts.get("stable_ms", 1200))
        self.coalesce_ms = int(cfg.timeouts.get("coalesce_ms", 2500))
        self.min_gap_ms = int(cfg.timeouts.get("min_gap_ms", 5000))

        self._last_pre_count: int = -1
        self._last_change_at: float = time.time()
        self._last_send_at: float = 0.0
        self._inflight_since: float = 0.0
        self._inflight_timeout: float = 45.0

    # ---- gates ----
    def _is_stable(self, cdp: CDP) -> bool:
        n = cdp.eval_expr(
            "(() => { const r = document.querySelector('main') || document.body;"
            " return r ? r.querySelectorAll('pre, code').length : 0; })()"
        ) or 0
        now = time.time()
        if n != self._last_pre_count:
            self._last_pre_count = int(n)
            self._last_change_at = now
            return False
        return (now - self._last_change_at) * 1000.0 > self.stable_ms

    def _inflight(self) -> bool:
        if not self._inflight_since:
            return False
        if (time.time() - self._inflight_since) > self._inflight_timeout:
            self._inflight_since = 0.0
            return False
        return True

    # ---- report ----
    def _fmt_report(self, results: list[dict], next_id: str) -> str:
        H = "#" * 3
        lines = ["[AGENT REPORT]"]
        for r in results:
            head = "id: %s | op: %s | %s" % (r["id"], r["op"], r["status"])
            lines.append(head)
            res = r.get("result") or {}
            if "code" in res:
                lines.append("exit: %s" % res["code"])
            if "elapsed" in res:
                lines.append("elapsed: %ss" % res["elapsed"])
            if res.get("unchanged"):
                lines.append("unchanged: true")
            if res.get("stdout"):
                lines.append("stdout:\n" + str(res["stdout"]).rstrip())
            if res.get("stderr"):
                lines.append("stderr:\n" + str(res["stderr"]).rstrip())
            if res.get("error"):
                lines.append("error: %s" % res["error"])
            if res.get("path"):
                lines.append("path: %s" % res["path"])
            if res.get("sha256"):
                lines.append("sha256: %s" % res["sha256"][:16])
            if r["op"] == "read" and isinstance(res.get("content"), str):
                lines.append("bytes: %s" % res.get("bytes", ""))
                lines.append("content:\n" + res["content"])
            lines.append("---")
        lines.append("next_id: %s" % next_id)
        return "\n".join(lines)

    def _next_id(self, current_max: str) -> str:
        """Простой инкремент id по префиксу канала."""
        pref = self.ch.prefix
        num = 0
        if current_max and current_max.startswith(pref):
            num = int(current_max[len(pref):])
        return "%s%04d" % (pref, num + 1)

    # ---- one pass ----
    def tick(self, cdp: CDP) -> DaemonResult:
        if self._inflight():
            return DaemonResult(self.letter, 0, 0, 0)
        if not self._is_stable(cdp):
            return DaemonResult(self.letter, 0, 0, 0)
        blocks = self.adapter.collect_blocks(cdp, last_n=3)
        if not blocks:
            return DaemonResult(self.letter, 0, 0, 0)
        if (time.time() - self._last_send_at) * 1000.0 < self.min_gap_ms:
            return DaemonResult(self.letter, 0, 0, 0)
        time.sleep(self.coalesce_ms / 1000.0)
        blocks = self.adapter.collect_blocks(cdp, last_n=3)

        results: list[dict] = []
        processed = skipped = errors = 0
        max_id = ""
        self._inflight_since = time.time()
        try:
            for b in blocks:
                if b.id > max_id:
                    max_id = b.id
                ok, reason = self.ledger.check(b)
                if not ok:
                    skipped += 1
                    results.append({"id": b.id, "op": b.op, "status": "SKIP",
                                    "result": {"error": reason}})
                    continue
                res = execute(self.cfg.root, b)
                self.ledger.commit(b)
                status = "OK" if res.get("ok") else "FAIL"
                results.append({"id": b.id, "op": b.op, "status": status, "result": res})
                if res.get("ok"):
                    processed += 1
                else:
                    errors += 1
            if results:
                next_id = self._next_id(max_id)
                report = self._fmt_report(results, next_id)
                sent = self.adapter.send_text(cdp, report)
                if sent:
                    self._last_send_at = time.time()
        finally:
            self._inflight_since = 0.0
        return DaemonResult(self.letter, processed, skipped, errors)

    # ---- loop ----
    def run_forever(self) -> None:
        while True:
            cdp = connect(self.ch.cdp_port, self.adapter.HOST)
            if not cdp:
                time.sleep(2.0)
                continue
            try:
                self.tick(cdp)
            except Exception:
                pass
            finally:
                try:
                    cdp.close()
                except Exception:
                    pass
            time.sleep(self.poll_ms / 1000.0)