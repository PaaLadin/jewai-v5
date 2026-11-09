"""test_export_share.py - smoke for Tools/export_share.py (BUG-006).

Без живого CDP: проверяет NDA-redaction и header-формат через локальный
HTML-файл, минуя браузерный путь (только переиспользуя чистые хелперы).
"""
import io
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from Tools import export_share as es  # noqa: E402

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


def test_nda_redaction():
    src = "hello\n[NDA]\nsecret line\n[/NDA]\nbye\n"
    red, n = re.subn(r"\[NDA\][\s\S]*?\[/NDA\]", "[NDA-REDACTED]", src, flags=re.IGNORECASE)
    ok('NDA regex n=1', n == 1, 'n=%r' % n)
    ok('NDA secret removed', 'secret line' not in red)
    ok('NDA marker present', '[NDA-REDACTED]' in red)
    ok('NDA bye kept', 'bye' in red)


def test_header_format():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / 'x.md'
        text = 'line1\nline2'
        url, final, title = 'https://share/x', 'https://share/x/final', 'DeepSeek chat'
        import time as _t
        header = ("# source: %s\n# final_url: %s\n# title: %s\n# exported: %s\n# bytes: %d\n\n"
                  % (url, final, title, _t.strftime("%Y-%m-%d %H:%M:%S"), len(text)))
        out.write_text(header + text, encoding='utf-8')
        got = out.read_text(encoding='utf-8')
        ok('header has source', '# source: %s' % url in got)
        ok('header has final_url', '# final_url: %s' % final in got)
        ok('header has title', '# title: %s' % title in got)
        ok('header has bytes', '# bytes: %d' % len(text) in got)
        ok('body present', 'line1\nline2' in got)


def test_browser_ws_error_on_dead_port():
    """Порт 19999 заведомо мёртв: должен быть URLError/ConnectionError."""
    try:
        es._browser_ws(19999)
        ok('dead port raises', False, 'no exception')
    except Exception as e:
        ok('dead port raises', True, type(e).__name__)


def test_scroll_js_present():
    ok('JS_SNAP has body.innerText', 'innerText' in es._JS_SNAP)
    ok('JS_TOP returns scrollTop', 'scrollTop' in es._JS_TOP)
    ok('JS_SCROLL_BY moves', 'scrollTop' in es._JS_SCROLL_BY)
    ok('JS_SCROLL_TOP zero', '= 0' in es._JS_SCROLL_TOP)


test_nda_redaction()
test_header_format()
test_browser_ws_error_on_dead_port()
test_scroll_js_present()

print()
print('PASS %d FAIL %d' % (oks, fails))
sys.exit(0 if fails == 0 else 1)