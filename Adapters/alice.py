"""Adapters/alice.py - adapter for alice.yandex.ru (per AUDIT section 21).

Contract:
- HOST: "alice.yandex.ru"
- TEXTAREA_SELECTOR: "textarea.AliceInput-Textarea" (fallback generic)
- collect_blocks: zones .FuturisMarkdown, .MarkdownText, [class*=Markdown], [class*=answer]
- normalize: NBSP->space, CRLF->LF only (no gutter).
- send_text: Enter only (no click). 2 rounds.
- verify_prompt_hits, new_chat.
"""
from __future__ import annotations

import time

from Bridge.cdp import CDP
from Bridge.exec import Block, parse_blocks


class Alice:
    HOST = "alice.yandex.ru"
    MARKER = "/"
    TEXTAREA_SELECTOR = "textarea.AliceInput-Textarea"

    def collect_blocks(self, cdp: CDP, last_n: int = 3) -> list[Block]:
        expr = (
            "(() => {"
            " const zones = document.querySelectorAll("
            "'.FuturisMarkdown, .MarkdownText, [class*=Markdown], [class*=markdown], "
            "[class*=response-message], [class*=answer]');"
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
        return (text or "").replace("\u00a0", " ").replace("\r\n", "\n")

    def send_text(self, cdp: CDP, text: str) -> bool:
        fill = (
            "(() => { let ta = document.querySelector('textarea.AliceInput-Textarea');"
            " if (!ta) ta = document.querySelector(\"textarea:not([readonly]):not([aria-hidden='true'])\");"
            " if (!ta) return false;"
            " const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;"
            " setter.call(ta, %r);"
            " ta.dispatchEvent(new Event('input', {bubbles:true}));"
            " ta.focus(); return true; })()"
        ) % text
        if not cdp.eval_expr(fill):
            return False
        time.sleep(0.3)
        for _ in range(2):
            for t in ("keydown", "keypress", "keyup"):
                cdp.eval_expr(
                    "(() => { let ta = document.querySelector('textarea.AliceInput-Textarea');"
                    " if (!ta) ta = document.querySelector(\"textarea:not([readonly]):not([aria-hidden='true'])\");"
                    " if (!ta) return;"
                    " ta.dispatchEvent(new KeyboardEvent(%r, {key:'Enter', code:'Enter',"
                    " keyCode:13, which:13, bubbles:true, cancelable:true})); })()" % t
                )
                time.sleep(0.05)
            time.sleep(1.0)
            v = cdp.eval_expr(
                "(() => { let ta = document.querySelector('textarea.AliceInput-Textarea');"
                " if (!ta) ta = document.querySelector(\"textarea:not([readonly]):not([aria-hidden='true'])\");"
                " return ta ? ta.value : ''; })()"
            ) or ""
            if not v.strip():
                return True
        return False

    def verify_prompt_hits(self, cdp: CDP, markers: list[str]) -> int:
        body = cdp.eval_expr("document.body ? document.body.innerText : ''") or ""
        return sum(1 for m in markers if m in body)

    def new_chat(self, cdp: CDP) -> bool:
        cdp.eval_expr("location.href = 'https://alice.yandex.ru/'")
        time.sleep(2)
        return True