"""Tests for Mainframe/council.py: dedup, append, personal ids, ACL."""
import shutil, sys, tempfile, time
from pathlib import Path

ROOT = Path(r'C:/JewAI')
sys.path.insert(0, str(ROOT))

import dataclasses
from Core.config import load as load_config
from Mainframe import council

OUT = Path(r'C:/DeepSeek/logs/D/_v5_council_test.txt')
lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond: lines.append('OK   ' + name)
    else: fails += 1; lines.append('FAIL ' + name + ' ' + detail)

tmp = Path(tempfile.mkdtemp(prefix='v5cc_'))
try:
    cfg0 = load_config()
    cfg = dataclasses.replace(cfg0, root=tmp, chat_port=8671)

    r = council.send(cfg, 'operator', 'ALL', 'hello world')
    check('send ok', r.get('ok') and not r.get('dedup'), str(r))

    r2 = council.send(cfg, 'operator', 'ALL', 'hello world')
    check('dedup same text within window', r2.get('ok') and r2.get('dedup') is True, str(r2))

    r3 = council.send(cfg, 'operator', 'ALL', 'different text')
    check('different text passes', r3.get('ok') and not r3.get('dedup'), str(r3))

    msgs = council.load_messages(cfg)
    check('2 messages stored', len(msgs) == 2, str(len(msgs)))

    r = council.send(cfg, 'operator', 'ALL', '')
    check('empty text rejected', r.get('ok') is False, str(r))

    r = council.send_personal(cfg, 'C', 'operator', 'hello C agent')
    check('personal operator ok', r.get('ok') is True, str(r))
    check('operator id starts ZCAA', (r.get('id', '').startswith('ZCAA')), r.get('id'))

    r2 = council.send_personal(cfg, 'C', 'C', 'reply from C')
    check('personal C->op ok', r2.get('ok') is True, str(r2))
    check('C id starts CZAA', (r2.get('id', '').startswith('CZAA')), r2.get('id'))

    r3 = council.send_personal(cfg, 'C', 'D', 'unauthorized')
    check('ACL: D cannot write C', r3.get('ok') is False and 'forbidden' in r3.get('error', ''), str(r3))

    r4 = council.send_personal(cfg, 'C', 'operator', 'second op msg')
    check('operator id increments', r4.get('id') == 'ZCAA0002', r4.get('id'))
    r5 = council.send_personal(cfg, 'C', 'C', 'second C msg')
    check('C id increments', r5.get('id') == 'CZAA0002', r5.get('id'))

    r = council.send_personal(cfg, 'Z', 'operator', 'hi')
    check('unknown channel rejected', r.get('ok') is False, str(r))

    msgs = council.load_personal(cfg, 'C')
    check('personal 4 messages', len(msgs) == 4, str(len(msgs)))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)