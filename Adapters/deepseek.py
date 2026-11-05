"""Adapters/deepseek.py — адаптер для chat.deepseek.com.

Селекторы подтверждены на старом content.js (AUDIT §19):
- сообщения: .ds-message, ответ ассистента: .ds-assistant-message-main-content.
- блоки команд: внутри pre/code.
- textarea: единственная на странице.
- Enter x2 — канон отправки.
"""
from __future__ import annotations

import time
from typing import Any

from Bridge.cdp import CDP
from Bridge.exec import Block, parse_blocks


class DeepSeek:
    HOST = "chat.deepseek.com"
    MARKER = "/a/chat/s/"
    TEXTAREA_SELECTOR = "textarea"

    def collect_blocks(self, cdp: CDP, last_n: int = 3) -> list[Block]:
        """Собрать блоки из последних N ассистентских сообщений.

        Возвращает список уникальных Block (в порядке появления в DOM).
        """
        expr = (
            "(() => {"
            f" const msgs = document.querySelectorAll('.ds-message');"
            f" const n = Math.min({last_n}, msgs.length);"
            " const out = [];"
            " for (let i = msgs.length - n; i < msgs.length; i++) {"
            "  if (i < 0) continue;"
            "  const m = msgs[i];"
            "  const c = m.querySelector('.ds-assistant-message-main-content');"
            "  if (!c) continue;"
            "  const pres = c.querySelectorAll('pre, code');"
            "  if (pres.length > 0) {"
            "   for (const p of pres) { out.push(p.textContent || ''); }"
            "  } else {"
            "   const t = c.innerText || c.textContent || '';"
            "   if (t) out.push(t);"
            "  }"
            " }"
            " return out; })()"
        )
        chunks = cdp.eval_expr(expr) or []
        seen: set[str] = set()
        blocks: list[Block] = []
        for txt in chunks:
            # 8C B-55: accept bare BEGIN too (agent may omit ###)
            if not txt:
                continue
            _t = txt.replace(" ", "")
            _nl = chr(10)
            if "###BEGIN###" not in _t and not (_nl + "BEGIN" + _nl) in (_nl + txt + _nl):
                continue
            for b in parse_blocks(txt):
                if b.id in seen:
                    continue
                seen.add(b.id)
                blocks.append(b)
        return blocks

    def send_text(self, cdp: CDP, text: str) -> bool:
        """Ввод + Enter x2. Возвращает True если textarea опустела."""
        sel = self.TEXTAREA_SELECTOR
        # 1) Check if user is typing (don't overwrite)
        v = cdp.eval_expr(
            "(() => { const t = document.querySelector(%r); return t ? t.value : ''; })()" % sel
        ) or ""
        if v.strip():
            return False  # Busy

        # 2) Clear textarea
        fill = (
            "(() => { const t = document.querySelector(%r); if (!t) return false;"
            " const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;"
            " setter.call(t, ''); t.dispatchEvent(new Event('input', {bubbles:true}));"
            " t.focus(); return true; })()"
        ) % sel
        if not cdp.eval_expr(fill):
            return False
        time.sleep(0.2)

        # 3) Insert text via CDP Input.insertText (reliable for large texts)
        try:
            cdp.call("Input.insertText", {"text": text})
        except Exception:
            setter_js = (
                "(() => { const t = document.querySelector(%r); if (!t) return false;"
                " const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;"
                " setter.call(t, %r); t.dispatchEvent(new Event('input', {bubbles:true}));"
                " return true; })()"
            ) % (sel, text)
            cdp.eval_expr(setter_js)

        time.sleep(0.5)
        # 2) Enter x2
        for _ in range(2):
            for t in ("keydown", "keypress", "keyup"):
                cdp.eval_expr(
                    "(() => { const t = document.querySelector(%r); if (!t) return;"
                    " t.dispatchEvent(new KeyboardEvent(%r, {key:'Enter', code:'Enter',"
                    " keyCode:13, which:13, bubbles:true, cancelable:true})); })()"
                    % (sel, t)
                )
                time.sleep(0.05)
            time.sleep(1.5)
        # 3) проверить опустела ли textarea
        v = cdp.eval_expr(
            "(() => { const t = document.querySelector(%r); return t ? t.value : ''; })()" % sel
        ) or ""
        return not v.strip()

    def verify_prompt_hits(self, cdp: CDP, markers: list[str]) -> int:
        body = cdp.eval_expr("document.body ? document.body.innerText : ''") or ""
        return sum(1 for m in markers if m in body)

    def new_chat(self, cdp: CDP) -> bool:
        cdp.eval_expr("location.href = 'https://chat.deepseek.com/'")
        time.sleep(2)
        return True