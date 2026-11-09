"""test_cdp_find_chat.py - поведение find_chat (10C BUG3a, вариант в).

Стратегия:
  1. Точное совпадение (host + marker) - берём этот таб.
  2. Иначе - fallback только при РОВНО одном page-табе с host.
  3. Иначе (ноль или много) - None.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from Bridge import cdp as C

fails = 0
oks = 0


def ok(name, cond, info=''):
    global fails, oks
    if cond:
        oks += 1
        print('OK   %s' % name)
    else:
        fails += 1
        print('FAIL %s %s' % (name, info))


def _with_targets(targets):
    orig = C.list_targets
    C.list_targets = lambda port, timeout=5.0: targets
    return orig


def test_exact_match():
    orig = _with_targets([
        {"type": "page", "url": "https://chat.deepseek.com/"},
        {"type": "page", "url": "https://chat.deepseek.com/a/chat/s/abc123"},
    ])
    try:
        r = C.find_chat(9999, "chat.deepseek.com", "/a/chat/s/")
        ok('exact match', r and '/a/chat/s/abc123' in r['url'], r)
    finally:
        C.list_targets = orig


def test_fallback_one_page():
    orig = _with_targets([
        {"type": "page", "url": "https://chat.deepseek.com/"},
        {"type": "page", "url": "https://example.com/"},
    ])
    try:
        r = C.find_chat(9999, "chat.deepseek.com", "/a/chat/s/")
        ok('fallback one host tab', r and 'chat.deepseek.com' in r['url'], r)
    finally:
        C.list_targets = orig


def test_fallback_many_pages():
    orig = _with_targets([
        {"type": "page", "url": "https://chat.deepseek.com/a/chat/s/x1"},
        {"type": "page", "url": "https://chat.deepseek.com/other"},
        {"type": "page", "url": "https://chat.deepseek.com/another"},
    ])
    try:
        r = C.find_chat(9999, "chat.deepseek.com", "/a/chat/s/MISSING")
        # Но marker MISSING нет, а fallback: >1 таб с host -> None
        ok('fallback many -> None', r is None, r)
    finally:
        C.list_targets = orig


def test_zero_pages():
    orig = _with_targets([
        {"type": "page", "url": "https://example.com/"},
    ])
    try:
        r = C.find_chat(9999, "chat.deepseek.com")
        ok('zero -> None', r is None, r)
    finally:
        C.list_targets = orig


def test_exact_wins_over_fallback():
    """Точный marker - даже если есть ещё page-табы с host, берём точный."""
    orig = _with_targets([
        {"type": "page", "url": "https://chat.deepseek.com/a/chat/s/target"},
        {"type": "page", "url": "https://chat.deepseek.com/other"},
    ])
    try:
        r = C.find_chat(9999, "chat.deepseek.com", "/a/chat/s/")
        ok('exact wins', r and 'target' in r['url'], r)
    finally:
        C.list_targets = orig


test_exact_match()
test_fallback_one_page()
test_fallback_many_pages()
test_zero_pages()
test_exact_wins_over_fallback()

print()
print('PASS %d FAIL %d' % (oks, fails))
sys.exit(0 if fails == 0 else 1)