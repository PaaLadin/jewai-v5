"""Adapters/base.py — протокол адаптера SPA-чата.

Адаптер знает про конкретную SPA (селекторы, кнопки, URL). Мост (daemon)
работает только через этот интерфейс.

Контракт:
- HOST: str — домен, по которому искать вкладку.
- TEXTAREA_SELECTOR: str — CSS textarea ввода.
- collect_blocks(cdp, last_n) -> list[Block] — блоки из последних N сообщений.
- send_text(cdp, text) -> bool — ввод и отправка.
- verify_prompt_hits(cdp, markers) -> int — сколько маркеров из списка есть в теле.
- new_chat(cdp) -> bool — переход в новый чат (для rebirth).
"""
from __future__ import annotations

from typing import Protocol

from Bridge.cdp import CDP
from Bridge.exec import Block


class ChatAdapter(Protocol):
    HOST: str
    TEXTAREA_SELECTOR: str
    MARKER: str

    def collect_blocks(self, cdp: CDP, last_n: int = 3) -> list[Block]: ...

    def send_text(self, cdp: CDP, text: str) -> bool: ...

    def verify_prompt_hits(self, cdp: CDP, markers: list[str]) -> int: ...

    def new_chat(self, cdp: CDP) -> bool: ...