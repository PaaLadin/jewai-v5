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

import os
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
        self.handicap_ms = int(cfg.timeouts.get("handicap_ms", 7000))
        self._handicap_until = 0.0
        self.bridge_status = {"text": "Инициализация...", "ts": time.time(), "iso": time.strftime("%Y-%m-%d %H:%M:%S")}

        self._last_pre_count: int = -1
        self._last_change_at: float = time.time()
        self._last_send_at: float = 0.0
        self._inflight_since: float = 0.0
        self._inflight_timeout: float = 45.0
        # 8C: track pause transitions for bootstrap/resume/stop messages
        self._last_paused: bool | None = None

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

    # ---- pause (B-15) ----
    def _pause_path(self):
        return self.cfg.channel_path(self.letter, "logs", "paused.json")

    def _is_paused(self) -> bool:
        pp = self._pause_path()
        if not pp.exists():
            return False
        try:
            import json as _j
            return bool(_j.loads(pp.read_text(encoding="utf-8")).get("paused"))
        except Exception:
            return False

    # ---- 8C: bootstrap outbox + activation ----
    def _outbox_path(self):
        return self.cfg.channel_path(self.letter, "logs", f"outbox_{self.letter}.jsonl")

    def _activation_flag_path(self):
        return self.cfg.channel_path(self.letter, "logs", "activation_sent.flag")

    def _is_ledger_empty(self) -> bool:
        """True if ledger has no committed entries (fresh install)."""
        try:
            lp = self.ledger.path
            if not lp.exists():
                return True
            import json as _j
            data = _j.loads(lp.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                entries = data.get("entries") or data.get("committed") or []
                return not entries
            if isinstance(data, list):
                return not data
            return True
        except Exception:
            return True

    def _send_or_buffer(self, cdp: CDP, text: str) -> bool:
        """If paused or busy — append to outbox; else send to chat."""
        if self._is_paused():
            try:
                op = self._outbox_path()
                op.parent.mkdir(parents=True, exist_ok=True)
                import json as _j
                with open(op, "a", encoding="utf-8") as f:
                    f.write(_j.dumps({"ts": time.time(), "text": text}, ensure_ascii=False) + "\n")
                return True
            except Exception:
                return False
        
        ok = self.adapter.send_text(cdp, text)
        if not ok:
            # Busy (user typing) or CDP failed. Buffer it.
            try:
                op = self._outbox_path()
                op.parent.mkdir(parents=True, exist_ok=True)
                import json as _j
                with open(op, "a", encoding="utf-8") as f:
                    f.write(_j.dumps({"ts": time.time(), "text": text}, ensure_ascii=False) + "\n")
                return True
            except Exception:
                return False
        return True

    def _drain_outbox(self, cdp: CDP) -> bool:
        """Send queued outbox items FIFO. Return True when empty."""
        op = self._outbox_path()
        if not op.exists():
            return True
        try:
            lines = op.read_text(encoding="utf-8").splitlines()
        except Exception:
            return True
        if not lines:
            return True
        import json as _j
        remaining = []
        for ln in lines:
            try:
                item = _j.loads(ln)
                text = item.get("text", "")
                if not text:
                    continue
                ok = self.adapter.send_text(cdp, text)
                if not ok:
                    remaining.append(ln); break
                time.sleep(2.0)
            except Exception:
                remaining.append(ln); break
        try:
            op.write_text("\n".join(remaining) + ("\n" if remaining else ""), encoding="utf-8")
        except Exception:
            pass
        return len(remaining) == 0

    def _render_activation(self) -> str:
        """Read Templates/PROMPT_ACTIVATION.md and substitute placeholders."""
        try:
            tpl = self.cfg.path("Templates", "PROMPT_ACTIVATION.md")
            if not tpl.exists():
                return ""
            text = tpl.read_text(encoding="utf-8")
            ch = self.ch
            # derive ID range from prefix
            pref = ch.prefix
            id_start = pref + "0001"
            id_end = pref + "0999"
            subs = {
                "{{NAME}}": ch.name,
                "{{CHANNEL}}": self.letter,
                "{{PREFIX}}": pref,
                "{{ID_START}}": id_start,
                "{{ID_END}}": id_end,
                "{{AGENT_PORT}}": str(ch.agent_port),
                "{{CDP_PORT}}": str(ch.cdp_port),
                "{{CHAT_PORT}}": str(self.cfg.chat_port),
                "{{ROOT}}": str(self.cfg.root),
            }
            for k, v in subs.items():
                text = text.replace(k, str(v))
            return text
        except Exception:
            return ""

    def _bootstrap_check(self, cdp: CDP) -> bool:
        """Return True if bootstrap handled this tick (skip normal work)."""
        flag = self._activation_flag_path()
        if flag.exists():
            return False  # already activated once
        if not self._is_ledger_empty():
            return False  # not fresh
        text = self._render_activation()
        if not text:
            return False
        ok = self.adapter.send_text(cdp, text)
        if ok:
            try:
                flag.parent.mkdir(parents=True, exist_ok=True)
                flag.write_text("sent @ " + str(time.time()), encoding="utf-8")
            except Exception:
                pass
            return True
        return False

    # ---- live.json for sidepanel ----
    def _live_path(self):
        return self.cfg.channel_path(self.letter, "logs", "live.json")

    def _set_status(self, text: str) -> None:
        self.bridge_status = {"text": text, "ts": time.time(), "iso": time.strftime("%Y-%m-%d %H:%M:%S")}
        self._write_live()

    def _drain_kick_buffer(self, cdp: CDP) -> bool:
        kb = self.cfg.channel_path(self.letter, "logs", "kick_buffer.jsonl")
        if not kb.exists(): return True
        try:
            lines = kb.read_text(encoding="utf-8").splitlines()
        except Exception: return True
        if not lines: return True
        import json as _j
        remaining = []
        for ln in lines:
            try:
                item = _j.loads(ln)
                text = item.get("text", "")
                if not text: continue
                ok = self.adapter.send_text(cdp, text)
                if not ok:
                    remaining.append(ln); break
                time.sleep(1.0)
            except Exception:
                remaining.append(ln); break
        try:
            kb.write_text("\n".join(remaining) + ("\n" if remaining else ""), encoding="utf-8")
        except Exception: pass
        return len(remaining) == 0

    def _write_live(self) -> None:
        try:
            import json as _j
            data = {
                "channel": self.letter,
                "watermark": self.ledger.watermark,
                "entries": self.ledger.entries[-50:],
                "last_action": self.ledger.last_action,
                "bridge_status": self.bridge_status,
                "paused": self._is_paused(),
                "updated": time.time(),
                "updated_iso": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            lp = self._live_path()
            lp.parent.mkdir(parents=True, exist_ok=True)
            tmp = lp.with_suffix(".tmp")
            tmp.write_text(_j.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            os.replace(tmp, lp)
        except Exception:
            pass

    # ---- one pass ----
    def tick(self, cdp: CDP) -> DaemonResult:
        # 8C: pause/play transition detection
        paused = self._is_paused()
        transition = None
        if self._last_paused is None:
            self._last_paused = paused  # baseline, no action on first tick
        elif self._last_paused != paused:
            transition = (self._last_paused, paused)
            self._last_paused = paused
        # ---- PAUSE: transition to paused -> send STOP ----
        if paused:
            if transition and transition[1]:
                # just paused — send STOP message once
                self._send_or_buffer(cdp, "СТОП! Пауза. Диалог с оператором начат. Не пиши команд в чат. Только ответы оператору.")
            self._set_status("Стою на паузе (диалог с оператором)")
            return DaemonResult(self.letter, 0, 0, 0)
        # handicap: after any text sent to chat, wait before next block
        if time.time() < self._handicap_until:
            self._set_status("Ожидание (handicap)")
            return DaemonResult(self.letter, 0, 0, 0)
        # ---- PLAY side: bootstrap by condition (idempotent via flag) ----
        flag = self._activation_flag_path()
        if (not flag.exists()) and self._is_ledger_empty():
            # bootstrap: first PLAY — send activation, set flag, skip rest this tick
            text = self._render_activation()
            if text and self.adapter.send_text(cdp, text):
                try:
                    flag.parent.mkdir(parents=True, exist_ok=True)
                    flag.write_text("sent @ " + str(time.time()), encoding="utf-8")
                except Exception:
                    pass
            return DaemonResult(self.letter, 0, 0, 0)
        if transition and not transition[1]:
            # regular resume (flag exists or ledger non-empty)
            self._send_or_buffer(cdp, "Возобновляй работу!")
        # 8C: outbox first
        if not self._drain_kick_buffer(cdp):
            self._set_status("Отправка буфера киков...")
            return DaemonResult(self.letter, 0, 0, 0)
        if not self._drain_outbox(cdp):
            self._set_status("Отправка буфера исходящих...")
            return DaemonResult(self.letter, 0, 0, 0)
        if self._inflight():
            return DaemonResult(self.letter, 0, 0, 0)
        if not self._is_stable(cdp):
            self._set_status("Ожидание стабилизации чата")
            return DaemonResult(self.letter, 0, 0, 0)
        blocks = self.adapter.collect_blocks(cdp, last_n=3)
        # 8C B-51: filter blocks by own channel prefix (safety)
        _own = self.ch.prefix
        blocks = [b for b in blocks if b.id.startswith(_own)]
        if not blocks:
            self._set_status("Ожидание команд (idle)")
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
                self._set_status("Выполняю " + b.id + " " + b.op)
                if b.id > max_id:
                    max_id = b.id
                ok, reason = self.ledger.check(b)
                if not ok:
                    skipped += 1
                    results.append({"id": b.id, "op": b.op, "status": "SKIP",
                                    "result": {"error": reason}})
                    continue
                _er = tuple(getattr(self.cfg, "extra_roots", ()) or ())
                res = execute(self.cfg.root, b, extra_roots=_er)
                self.ledger.commit(b)
                status = "OK" if res.get("ok") else "FAIL"
                _detail = ""
                if isinstance(res, dict):
                    _detail = str(res.get("path") or res.get("sha256") or res.get("error") or "")[:200]
                try:
                    self.ledger.record(b, status, _detail)
                except Exception:
                    pass
                results.append({"id": b.id, "op": b.op, "status": status, "result": res})
                if res.get("ok"):
                    processed += 1
                else:
                    errors += 1
            if results:
                next_id = self._next_id(max_id)
                report = self._fmt_report(results, next_id)
                self._set_status("Отправка [AGENT REPORT]")
                sent = self._send_or_buffer(cdp, report)
                if sent:
                    self._last_send_at = time.time()
                    self._handicap_until = time.time() + self.handicap_ms / 1000.0
        finally:
            self._inflight_since = 0.0
            try:
                self._write_live()
            except Exception:
                pass
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