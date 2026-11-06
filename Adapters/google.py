"""Adapters/google.py - adapter for Google AI Mode chat.

Mechanic (from C:/DeepSeek/AI-Swing-Bridge content.js + background.js):
- Find visible textarea. Focus it, clear, execCommand insertText,
  dispatch input/change, focus again.
- Submit via CDP Input.dispatchKeyEvent keyDown+keyUp VK 13 (Enter).
  Do NOT look for send button: click on it opens the side panel (old pain).

Verified live on Google AI Mode tab 2026-11-06:
- two textareas: hidden search box (role=textbox) and visible AI Mode input.
- send_text via execCommand + CDP Enter => message went through, reply ACK.
- reply DOM: DIV.pWvJNd (ACK), parent DIV.Zkbeff; request stored in H3.iMqumd.
  Simplest reliable read: document.body.innerText, then parse_blocks().
"""
from __future__ import annotations

import time
from typing import Any

from Bridge.cdp import CDP
from Bridge.exec import Block, parse_blocks


class Google:
    HOST = "google.com"
    MARKER = "/search"
    TEXTAREA_SELECTOR = "textarea"

    _FIND_VISIBLE = (
        "(() => {"
        " const ts = document.querySelectorAll('textarea');"
        " for (const t of ts) {"
        "  const b = t.getBoundingClientRect();"
        "  if (b.width > 0 && b.height > 0) return t;"
        " }"
        " const r = document.querySelector('[role=\"textbox\"]');"
        " return r || null; })()"
    )

    def _cur_value(self, cdp: CDP) -> str:
        v = cdp.eval_expr(
            "(() => { const t = " + self._FIND_VISIBLE + ";"
            " if (!t) return '';"
            " return (t.value !== undefined) ? t.value : (t.innerText || ''); })()"
        )
        return v or ""

    def _is_textarea(self, cdp: CDP) -> bool:
        v = cdp.eval_expr(
            "(() => { const t = " + self._FIND_VISIBLE + ";"
            " if (!t) return '';"
            " return t.tagName || ''; })()"
        )
        return (v or "").upper() == "TEXTAREA"

    def collect_blocks(self, cdp: CDP, last_n: int = 3) -> list[Block]:
        # Google AI Mode DOM is unstable across A/B variants. We take the whole
        # visible body text, filter to assistant zones via parse_blocks (which is
        # tolerant), and dedupe by id. last_n is advisory: ledger protects
        # against replay, so over-reading is safe.
        txt = cdp.eval_expr("document.body ? document.body.innerText : ''") or ""
        if not txt:
            return []
        seen: set[str] = set()
        blocks: list[Block] = []
        for b in parse_blocks(txt):
            if b.id in seen:
                continue
            seen.add(b.id)
            blocks.append(b)
        return blocks

    def send_text(self, cdp: CDP, text: str) -> bool:
        # 1) Busy guard: if textarea already has content, do not overwrite.
        if self._cur_value(cdp).strip():
            return False

        # 2) Focus + clear + insertText via execCommand (as in AI-Swing-Bridge).
        ins = (
            "(() => { const t = " + self._FIND_VISIBLE + ";"
            " if (!t) return false;"
            " t.focus();"
            " if (t.value !== undefined) { t.value = ''; } else { t.innerText = ''; }"
            " document.execCommand('insertText', false, %r);"
            " t.dispatchEvent(new Event('input', {bubbles:true}));"
            " t.dispatchEvent(new Event('change', {bubbles:true}));"
            " t.focus();"
            " return true; })()"
        ) % text
        if not cdp.eval_expr(ins):
            return False

        time.sleep(0.4)

        # 3) Submit via CDP Input.dispatchKeyEvent (keyDown + keyUp VK 13).
        #    "Hardware enter" - does not depend on the send button at all.
        try:
            cdp.call("Input.dispatchKeyEvent", {
                "type": "keyDown",
                "windowsVirtualKeyCode": 13,
                "nativeVirtualKeyCode": 13,
                "macCharCode": 13,
                "key": "Enter",
                "code": "Enter",
            })
            cdp.call("Input.dispatchKeyEvent", {
                "type": "keyUp",
                "windowsVirtualKeyCode": 13,
                "nativeVirtualKeyCode": 13,
                "key": "Enter",
                "code": "Enter",
            })
        except Exception:
            # Fallback: synthetic KeyboardEvent via JS.
            for phase in ("keydown", "keypress", "keyup"):
                cdp.eval_expr(
                    "(() => { const t = " + self._FIND_VISIBLE + ";"
                    " if (!t) return;"
                    " t.dispatchEvent(new KeyboardEvent(%r, {key:'Enter', code:'Enter',"
                    " keyCode:13, which:13, bubbles:true, cancelable:true})); })()" % phase
                )
                time.sleep(0.05)

        time.sleep(1.6)

        # 4) Confirm: textarea empty OR body already contains our text.
        after = self._cur_value(cdp)
        if not after.strip():
            return True
        body = cdp.eval_expr("document.body ? document.body.innerText : ''") or ""
        probe = (text[:40] if text else "").strip()
        if probe and probe in body:
            return True
        return False

    def verify_prompt_hits(self, cdp: CDP, markers: list[str]) -> int:
        body = cdp.eval_expr("document.body ? document.body.innerText : ''") or ""
        return sum(1 for m in markers if m in body)

    def new_chat(self, cdp: CDP) -> bool:
        cdp.eval_expr("location.href = 'https://www.google.com/search?udm=50'")
        time.sleep(2)
        return True