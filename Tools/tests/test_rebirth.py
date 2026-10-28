"""Tests for Rebirth: table advance, gate, onboard neighbor pick."""
import json, shutil, sys, tempfile
from pathlib import Path

ROOT = Path(r'C:/JewAI')
sys.path.insert(0, str(ROOT))

import dataclasses
from Core.config import Config, Channel, load as load_config
from Rebirth.table import Table, default_table_template, _inc_series, _inc_range
from Rebirth.master import Master, GateVerdict, set_ready
from Rebirth.onboard import pick_neighbor, onboard_message

OUT = Path(r'C:/DeepSeek/logs/D/_v5_rebirth_test.txt')
lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond:
        lines.append('OK   ' + name)
    else:
        fails += 1
        lines.append('FAIL ' + name + ' ' + detail)

# ---- series math ----
check('inc_series 13D->14D', _inc_series('13D') == '14D')
check('inc_series 9A->10A', _inc_series('9A') == '10A')
check('inc_series bad', _inc_series('xxx') == 'xxx')
check('inc_range +1000', _inc_range(['AAAB3000', 'AAAB3999']) == ['AAAB4000', 'AAAB4999'])

# ---- table.advance ----
tmp = tempfile.mkdtemp(prefix='v5reb_')
try:
    tp = Path(tmp) / 'table.json'
    tp.write_text(json.dumps(default_table_template(), ensure_ascii=False), encoding='utf-8')
    tab = Table(tp)
    tab.load()
    d_before = tab.get('D')
    check('D series before', d_before['current_series'] == '13D', d_before['current_series'])
    check('D range before', d_before['range'] == ['DDAB3000', 'DDAB3999'], str(d_before['range']))
    r = tab.advance('D', new_url='https://x', share_url='https://s')
    check('advance old', r.old_series == '13D', r.old_series)
    check('advance new', r.new_series == '14D', r.new_series)
    check('advance range', r.new_range == ['DDAB4000', 'DDAB4999'], str(r.new_range))
    d_after = tab.get('D')
    check('D url after', d_after['chat_url'] == 'https://x')
    check('D next_series after', d_after['next_series'] == '15D', d_after['next_series'])
    # persistence
    tab2 = Table(tp); tab2.load()
    check('persist after reload', tab2.get('D')['current_series'] == '14D')

    # ---- gate ----
    ch_D = Channel(letter='D', name='Dimon', agent_port=8669, cdp_port=9125,
                   prefix='DDAA', extension='extension', model='deepseek')
    cfg = Config(root=Path(tmp), bind='127.0.0.1', chat_port=8671, doh_proxy_port=9899,
                 letters=('D',), channels={'D': ch_D},
                 thresholds={'rebirth_cmds': 850}, timeouts={}, version='test')
    (Path(tmp) / 'logs' / 'rebirth').mkdir(parents=True, exist_ok=True)
    m = Master(cfg, 'D')
    v = m.check_gate()
    check('gate no flag -> deny', v.decision == 'deny' and v.reason == 'no_ready_flag', str(v.__dict__))
    set_ready(cfg, 'D', cmds=500, limit=False)
    v = m.check_gate()
    check('gate 500 -> deny', v.decision == 'deny' and v.reason == 'below_threshold', str(v.__dict__))
    set_ready(cfg, 'D', cmds=900, limit=False)
    v = m.check_gate()
    check('gate 900 -> allow threshold', v.decision == 'allow' and v.reason == 'threshold', str(v.__dict__))
    set_ready(cfg, 'D', cmds=100, limit=True)
    v = m.check_gate()
    check('gate limit -> allow', v.decision == 'allow' and v.reason == 'limit', str(v.__dict__))
    (Path(tmp) / 'logs' / 'rebirth' / 'force_D.flag').write_text('x')
    set_ready(cfg, 'D', cmds=100, limit=False)
    v = m.check_gate()
    check('gate force -> allow', v.decision == 'allow' and v.reason == 'force', str(v.__dict__))
    (Path(tmp) / 'logs' / 'rebirth' / 'force_D.flag').unlink()
    (Path(tmp) / 'logs' / 'rebirth' / 'hold_D.flag').write_text('x')
    set_ready(cfg, 'D', cmds=900, limit=False)
    v = m.check_gate()
    check('gate hold -> deny even with 900', v.decision == 'deny' and v.reason == 'hold', str(v.__dict__))

    # ---- onboard neighbor ----
    def probe_none(ch): return None
    ch_out, pref, num = pick_neighbor('D', probe_none)
    check('neighbor no candidates', ch_out is None)

    def probe(ch):
        vals = {'A': ('AAAA', 400), 'B': ('BBAA', 900), 'C': ('CCAA', 20), 'D': ('DDAA', 400),
                'E': ('QQAA', 500), 'F': ('FFAA', 100)}
        return vals.get(ch)
    ch_out, pref, num = pick_neighbor('D', probe)
    check('neighbor after D -> E (500 in [50,800))', ch_out == 'E', str((ch_out, pref, num)))

    def probe2(ch):
        vals = {'A': ('AAAA', 500), 'B': ('BBAA', 900), 'C': ('CCAA', 20), 'E': ('QQAA', 900)}
        return vals.get(ch)
    ch_out, pref, num = pick_neighbor('D', probe2)
    check('neighbor after D -> skip E 900, F none, A 500 -> A', ch_out == 'A', str((ch_out, pref, num)))

    msg = onboard_message('14D', 'https://x')
    check('onboard msg has series', '14D' in msg)
    check('onboard msg has url', 'https://x' in msg)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)