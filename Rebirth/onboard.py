"""Rebirth/onboard.py - neighbor onboarding.

Contract (AUDIT section 24):
- pick_neighbor(newcomer, table, probe_fn) -> (ch, last_id or None)
- Rule: circular A->B->C->D->E->F->A starting after newcomer.
- Candidate: lastId_num % 1000 in [50, 800) - not at start, not near finish.
- send(msg) delegated to caller (kick adapter). No subprocess from here.
"""
from __future__ import annotations

from typing import Callable

ORDER = ["A", "B", "C", "D", "E", "F"]


def pick_neighbor(newcomer: str, probe_fn: Callable[[str], tuple[str, int] | None]) -> tuple[str | None, str | None, int | None]:
    """probe_fn(ch) -> (prefix, num) | None. Returns (ch, prefix, num)."""
    if newcomer in ORDER:
        i = ORDER.index(newcomer)
        order = ORDER[i + 1:] + ORDER[:i]
    else:
        order = list(ORDER)
    for ch in order:
        r = probe_fn(ch)
        if r is None:
            continue
        prefix, num = r
        pos = num % 1000
        if 50 <= pos < 800:
            return ch, prefix, num
    return None, None, None


def onboard_message(newcomer_series: str, new_url: str) -> str:
    return (
        "[SYS] Новый агент %s в чате %s.\n"
        "Задача: пообщаться, убедиться, что отвечает и разобрался с мостом.\n"
        "Если молчит >5 мин — пошли инструкцию: формат блок-команд, "
        "маркеры [X>Y], что читать в RAG (behavior_rules первым)."
    ) % (newcomer_series, new_url or "(url неизвестен)")