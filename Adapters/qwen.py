"""Adapters/qwen.py - adapter for chat.qwen.ai (per AUDIT section 20).

Contract:
- HOST: "chat.qwen.ai"
- TEXTAREA_SELECTOR: "textarea.message-input-textarea" (with fallback)
- MARKER: "/c/" (Qwen chat path - TBD, probe at runtime)
- collect_blocks: read last N assistant messages, glue zones, normalize
  (strip gutter line numbers, NBSP->space), parse.
- send_text: React _valueTracker mandatory; try native click on send DIV first,
  then Enter.
- verify_prompt_hits, new_chat: same shape as DeepSeek.
"""
from __future__ import annotations

import time
from typing import Any

from Bridge.cdp import CDP
from Bridge.exec import Block, parse_blocks


class Qwen:
    HOST = "chat.qwen.ai"
    MARKER = "/c/"
    TEXTAREA_SELECTOR = "textarea.message-input-textarea"

    def collect_blocks(self, cdp: CDP, last_n: int = 3) -> list[Block]:
        expr = (
            "(() => {"
            " const zones = document.querySelectorAll("
            "'.response-message-content, .custom-qwen-markdown, .qwen-markdown, "
            "[class*=response-message], [class*=markdown]');"
            f" const n = Math.min({last_n}, zones.length);"
            " let glued = '';"
            " for (let i = zones.length - n; i < zones.length; i++) {"
            "  if (i < 0) continue;"
            "  glued += '\\n' + (zones[i].innerText || '');"
            " }"
            " return glued; })()"
        )
        glued = cdp.eval_expr(expr) or ""
        if not glued:
            return []
        norm = self._normalize(glued)
        seen: set[str] = set()
        blocks: list[Block] = []
        for b in parse_blocks(norm):
            if b.id in seen:
                continue
            seen.add(b.id)
            blocks.append(b)
        return blocks

    @staticmethod
    def _normalize(text: str) -> str:
        t = (text or "").replace("\u00a0", " ").replace("\r\n", "\n")
        # drop gutter-only lines (just digits)
        lines = [ln for ln in t.split("\n") if not ln.strip().isdigit()]
        return "\n".join(lines)

    def send_text(self, cdp: CDP, text: str) -> bool:
        sel = self.TEXTAREA_SELECTOR
        # 1) find textarea (with fallbacks)
        find = (
            "(() => { let ta = document.querySelector('textarea.message-input-textarea');"
            " if (!ta) ta = document.querySelector(\"textarea:not([readonly]):not([aria-hidden='true'])\");"
            " return ta ? true : false; })()"
        )
        if not cdp.eval_expr(find):
            return False
        # 2) clear + set via prototype setter, reset React _valueTracker
        fill = (
            "(() => { const ta = document.querySelector('textarea.message-input-textarea')"
            " || document.querySelector(\"textarea:not([readonly]):not([aria-hidden='true'])\");"
            " if (!ta) return false;"
            " const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;"
            " ta.focus(); setter.call(ta, '');"
            " if (ta._valueTracker) ta._valueTracker.setValue('');"
            " ta.dispatchEvent(new Event('input', {bubbles:true}));"
            " setter.call(ta, %r);"
            " if (ta._valueTracker) ta._valueTracker.setValue('');"
            " ta.dispatchEvent(new Event('input', {bubbles:true}));"
            " ta.dispatchEvent(new Event('change', {bubbles:true}));"
            " ta.focus(); return true; })()"
        ) % text
        if not cdp.eval_expr(fill):
            return False
        time.sleep(0.4)
        # 3) try send: native click on send DIV, then Enter, up to 3 attempts
        for attempt in range(3):
            click = (
                "(() => { const b = document.querySelector('.message-input-right-button-send');"
                " if (!b) return false;"
                " const r = b.getBoundingClientRect();"
                " if (r.width <= 0 || r.height <= 0) return false;"
                " b.click(); return true; })()"
            )
            cdp.eval_expr(click)
            time.sleep(0.8)
            v = self._value(cdp)
            if not v.strip():
                return True
            # Enter fallback
            for t in ("keydown", "keypress", "keyup"):
                cdp.eval_expr(
                    "(() => { const ta = document.querySelector('textarea.message-input-textarea');"
                    " if (!ta) return;"
                    " ta.dispatchEvent(new KeyboardEvent(%r, {key:'Enter', code:'Enter',"
                    " keyCode:13, which:13, bubbles:true, cancelable:true})); })()" % t
                )
                time.sleep(0.05)
            time.sleep(0.8)
            if not self._value(cdp).strip():
                return True
        return False

    def _value(self, cdp: CDP) -> str:
        v = cdp.eval_expr(
            "(() => { const ta = document.querySelector('textarea.message-input-textarea')"
            " || document.querySelector(\"textarea:not([readonly]):not([aria-hidden='true'])\");"
            " return ta ? ta.value : ''; })()"
        )
        return v or ""

    def verify_prompt_hits(self, cdp: CDP, markers: list[str]) -> int:
        body = cdp.eval_expr("document.body ? document.body.innerText : ''") or ""
        return sum(1 for m in markers if m in body)

    def new_chat(self, cdp: CDP) -> bool:
        cdp.eval_expr("location.href = 'https://chat.qwen.ai/'")
        time.sleep(2)
        return True