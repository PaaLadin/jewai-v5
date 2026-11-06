"""Perplexity UI adapter. Source-checked selectors; live validation still required."""
from __future__ import annotations
import hashlib
import json
import time
from pathlib import Path
from urllib.parse import urlparse

SELECTORS = json.loads(Path(__file__).with_name("perplexity_selectors.json").read_text(encoding="utf-8"))
DOM = Path(__file__).with_name("perplexity_dom.js").read_text(encoding="utf-8").replace(
    "__JEWAI_SELECTORS__", json.dumps(SELECTORS, ensure_ascii=True))
INPUT = ", ".join(SELECTORS["inputs"])


class Perplexity:
    HOST = "www.perplexity.ai"
    MARKER = "/search/"
    TEXTAREA_SELECTOR = INPUT

    def __init__(self, stable_seconds=3.0, clock=None, sleep=None):
        self.stable_seconds = stable_seconds
        self.clock = clock or time.monotonic
        self.sleep = sleep or time.sleep
        self._digest = None
        self._changed = 0.0
        self.last_status = "unverified"

    def snapshot(self, cdp):
        data = cdp.eval_expr(DOM)
        if not isinstance(data, dict):
            raise RuntimeError("Perplexity DOM probe failed")
        host = urlparse(data.get("url", "")).hostname
        if host not in ("www.perplexity.ai", "perplexity.ai"):
            raise RuntimeError("unexpected Perplexity host")
        return data

    def ready(self, cdp):
        s = self.snapshot(cdp)
        self.last_status = ("generating" if s.get("busy") else
                            "ready" if s.get("input") else "login_or_unsupported_dom")
        return bool(s.get("input")) and not s.get("busy")

    def collect_blocks(self, cdp, last_n=3):
        from Bridge.exec import parse_blocks
        s = self.snapshot(cdp)
        if s.get("busy") or not s.get("input") or not s.get("supported"):
            self._digest = None
            self.last_status = "generating_or_unsupported_dom"
            return []
        texts = s.get("answers", [])[-max(1, int(last_n)):]
        digest = hashlib.sha256(json.dumps([s.get("url"), texts],
                                          ensure_ascii=False).encode()).hexdigest()
        now = self.clock()
        if digest != self._digest:
            self._digest, self._changed = digest, now
            return []
        if now - self._changed < self.stable_seconds:
            return []
        seen, blocks = set(), []
        for text in texts:
            for block in parse_blocks(text):
                if block.id not in seen:
                    seen.add(block.id)
                    blocks.append(block)
        self.last_status = "stable"
        return blocks

    def send_text(self, cdp, text):
        s = self.snapshot(cdp)
        if not s.get("input") or s.get("busy") or str(s.get("draft", "")).strip():
            return False
        focus = """(() => {
          const cfg = %s;
          for (const selector of cfg.inputs) {
            const el = [...document.querySelectorAll(selector)].find(e =>
              e.getClientRects().length && !e.disabled && !e.readOnly &&
              e.getAttribute('aria-disabled') !== 'true' && !e.closest(cfg.exclude));
            if (el) { el.focus(); return true; }
          }
          return false;
        })()""" % json.dumps(SELECTORS, ensure_ascii=True)
        if not cdp.eval_expr(focus):
            return False
        cdp.call("Input.insertText", {"text": text})
        self.sleep(0.2)
        s = self.snapshot(cdp)
        if str(s.get("draft", "")).replace("\r\n", "\n").strip() != text.replace("\r\n", "\n").strip():
            return False
        cdp.call("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Enter",
                                          "code": "Enter", "windowsVirtualKeyCode": 13})
        cdp.call("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Enter",
                                          "code": "Enter", "windowsVirtualKeyCode": 13})
        for _ in range(20):
            self.sleep(0.25)
            after = self.snapshot(cdp)
            if not str(after.get("draft", "")).strip():
                self.last_status = "submitted_not_delivery_ack"
                return True
        self.last_status = "submission_uncertain"
        return False

    def verify_prompt_hits(self, cdp, markers):
        s = self.snapshot(cdp)
        if s.get("busy") or not s.get("supported"):
            return 0
        text = "\n".join(s.get("answers", []))
        return sum(bool(m) and m in text for m in markers)

    def new_chat(self, cdp):
        cdp.call("Page.navigate", {"url": "https://www.perplexity.ai/"})
        self._digest = None
        for _ in range(40):
            self.sleep(0.25)
            try:
                s = self.snapshot(cdp)
                if s.get("input") and not s.get("answers") and not s.get("busy"):
                    return True
            except RuntimeError:
                continue
        raise RuntimeError("new Perplexity chat not verified; login or DOM inspection needed")
