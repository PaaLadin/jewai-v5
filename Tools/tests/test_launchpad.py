"""Tests for launchpad: status, self-forbidden, bad channels, not-v5 modules."""
import shutil, sys, tempfile
from pathlib import Path

ROOT = Path(r'C:/JewAI')
sys.path.insert(0, str(ROOT))

import dataclasses
from Core.config import load as load_config
from Mainframe import launchpad

OUT = Path(__file__).resolve().parent.parent.parent / Path('logs/runtime/_v5_launchpad_test.txt')
lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond: lines.append('OK   ' + name)
    else: fails += 1; lines.append('FAIL ' + name + ' ' + detail)

tmp = Path(tempfile.mkdtemp(prefix='v5lp_'))
try:
    cfg0 = load_config()
    cfg = dataclasses.replace(cfg0, root=tmp, chat_port=8671)

    st = launchpad.status(cfg)
    check('status ok', st.get('ok') is True)
    b = st.get('blocks', {})
    check('has server', 'server' in b)
    check('server is self', b.get('server', {}).get('self') is True)
    for L in cfg.letters:
        check('agent:' + L, 'agent:' + L in b)
        check('chrome:' + L, 'chrome:' + L in b)
    check('doh block', 'doh' in b)
    check('mailbot block', 'mailbot' in b)
    check('rebirth block', 'rebirth' in b)

    r = launchpad.boot(cfg, 'server')
    check('boot server denied', r.get('ok') is False)
    r = launchpad.stop(cfg, 'server')
    check('stop server denied', r.get('ok') is False)
    r = launchpad.restart(cfg, 'server')
    check('restart server denied', r.get('ok') is False)

    r = launchpad.boot(cfg, 'agent:Z')
    check('agent Z rejected', r.get('ok') is False)
    r = launchpad.boot(cfg, 'chrome:Z')
    check('chrome Z rejected', r.get('ok') is False)
    r = launchpad.boot(cfg, 'unknown')
    check('unknown boot rejected', r.get('ok') is False)
    r = launchpad.stop(cfg, 'unknown')
    check('unknown stop rejected', r.get('ok') is False)

    r = launchpad.boot(cfg, 'doh')
    check('doh refused', r.get('ok') is False and 'not implemented' in r.get('error', ''))
    r = launchpad.boot(cfg, 'mailbot')
    check('mailbot refused', r.get('ok') is False and 'not in v5' in r.get('error', ''))
    r = launchpad.boot(cfg, 'rebirth')
    check('rebirth refused', r.get('ok') is False and 'not in v5' in r.get('error', ''))

    sp = launchpad._sp_load(cfg)
    check('registry is dict', isinstance(sp, dict))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)