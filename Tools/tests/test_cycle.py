"""Tests for Rebirth/cycle.py with mocked adapter and cdp."""
import json, shutil, sys, tempfile, time
from pathlib import Path

ROOT = Path(r'C:/JewAI')
sys.path.insert(0, str(ROOT))

import dataclasses
from Core.config import load as load_config
from Rebirth.table import Table, default_table_template
from Rebirth.cycle import extract_markers, run_cycle, MIN_HITS

OUT = Path(r'C:/DeepSeek/logs/D/_v5_cycle_test.txt')
lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond: lines.append('OK   ' + name)
    else: fails += 1; lines.append('FAIL ' + name + ' ' + str(detail))

# --- extract_markers ---
txt = ("# Title\n\n---\n\n"
       "This is a long line that exceeds forty characters in length for sure.\n"
       "Short.\n"
       "Another long line here also exceeding forty characters for the test.\n"
       "Third long line that should be included as a marker because it is long.\n"
       "Fourth line will be ignored because MARKERS_MAX is 3.\n")
m = extract_markers(txt)
check('markers count 3', len(m) == 3, str(len(m)))
check('markers <=60 chars', all(len(x) <= 60 for x in m))
check('markers first starts This', m[0].startswith('This'), m[0] if m else '')

check('no markers for short', extract_markers("short\n# header\n---") == [])

tmp = Path(tempfile.mkdtemp(prefix='v5cyc_'))
try:
    tp = Path(tmp) / 'logs' / 'rebirth' / 'series_table.json'
    tp.parent.mkdir(parents=True)
    tp.write_text(json.dumps(default_table_template(), ensure_ascii=False), encoding='utf-8')

    cfg0 = load_config()
    cfg = dataclasses.replace(cfg0, root=tmp, chat_port=8671)
    tab = Table(tp); tab.load()

    class FakeCDP:
        def eval_expr(self, expr):
            if 'location.href' in expr: return 'https://chat.deepseek.com/a/chat/s/test'
            return ''

    class FakeAdapter:
        HOST = 'fake'
        def new_chat(self, cdp): return True
        def send_text(self, cdp, text): return True
        def verify_prompt_hits(self, cdp, markers): return 3

    # --- no prompt file in tmp root -> fail, table unchanged ---
    r = run_cycle(cfg, 'D', FakeAdapter(), FakeCDP(), tab)
    check('no prompt -> fail', r.get('ok') is False, str(r)[:120])
    check('no prompt error mentions PROMPT', 'PROMPT' in r.get('error', ''))
    tab_a = Table(tp); tab_a.load()
    check('table still 13D', tab_a.get('D')['current_series'] == '13D', tab_a.get('D')['current_series'])

    # --- create PROMPT_14D in tmp root, run again: success ---
    prompt_p = Path(tmp) / 'logs' / 'D' / 'PROMPT_14D.md'
    prompt_p.parent.mkdir(parents=True)
    prompt_p.write_text(
        "This is a long marker line that exceeds forty characters for sure.\n"
        "Second long marker also exceeds forty characters in this test text.\n"
        "Third long marker line that passes the minimum length check ok.\n",
        encoding='utf-8')

    tab2 = Table(tp); tab2.load()
    r = run_cycle(cfg, 'D', FakeAdapter(), FakeCDP(), tab2)
    check('cycle success', r.get('ok') is True, str(r)[:200])
    check('cycle hits>=MIN', r.get('hits', 0) >= MIN_HITS, r.get('hits'))
    check('cycle advanced 13D->14D', r.get('old_series') == '13D' and r.get('new_series') == '14D',
          '%s->%s' % (r.get('old_series'), r.get('new_series')))
    check('cycle new_url captured', r.get('new_url') == 'https://chat.deepseek.com/a/chat/s/test', r.get('new_url'))

    tab3 = Table(tp); tab3.load()
    d = tab3.get('D')
    check('table D now 14D', d.get('current_series') == '14D', d.get('current_series'))
    check('table D range shifted', d.get('range') == ['DDAB4000', 'DDAB4999'], str(d.get('range')))

    # After success, table D is at 14D, next_series is 15D.
    # Create PROMPT_15D for negative scenarios.
    prompt15 = Path(tmp) / 'logs' / 'D' / 'PROMPT_15D.md'
    prompt15.write_text(
        "This is a long marker line that exceeds forty characters for sure.\n"
        "Second long marker also exceeds forty characters in this test text.\n",
        encoding='utf-8')

    # --- verify fail: 0 hits -> no advance ---
    class FakeAdapterFail(FakeAdapter):
        def verify_prompt_hits(self, cdp, markers): return 0
    tab4 = Table(tp); tab4.load()
    r = run_cycle(cfg, 'D', FakeAdapterFail(), FakeCDP(), tab4)
    check('verify fail -> not ok', r.get('ok') is False and 'verify' in r.get('error', ''), str(r)[:120])
    tab5 = Table(tp); tab5.load()
    check('table D still 14D after fail', tab5.get('D')['current_series'] == '14D', tab5.get('D')['current_series'])

    # --- no markers in PROMPT_15D -> fail ---
    prompt15.write_text("Short.\n# header\n", encoding='utf-8')
    tab6 = Table(tp); tab6.load()
    r = run_cycle(cfg, 'D', FakeAdapter(), FakeCDP(), tab6)
    check('no markers fail', r.get('ok') is False and 'no markers' in r.get('error', ''), str(r)[:120])

    # --- log has entries ---
    log_p = Path(tmp) / 'logs' / 'rebirth' / 'rebirth_log.jsonl'
    check('log exists', log_p.exists())
    if log_p.exists():
        entries = [l for l in log_p.read_text(encoding='utf-8').splitlines() if l.strip()]
        check('log entries >=2', len(entries) >= 2, str(len(entries)))
        check('log has OK', any('"OK"' in e or '"result": "OK"' in e for e in entries), entries[0] if entries else '')

finally:
    shutil.rmtree(tmp, ignore_errors=True)

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)