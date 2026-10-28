"""Functional smoke tests: parse, ledger, ops. No Chrome, no network."""
import sys, tempfile, shutil
from pathlib import Path

ROOT = Path(r'C:/JewAI')
sys.path.insert(0, str(ROOT))

from Bridge.exec import (Block, parse_blocks, Ledger, execute, safe_path, OpError)

H = '#' * 3
out_path = Path(r'C:/DeepSeek/logs/D/_v5_smoke.txt')
lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond:
        lines.append(f'OK   {name}')
    else:
        fails += 1
        lines.append(f'FAIL {name} {detail}')

def check_eq(name, got, want):
    check(name, got == want, f'got={got!r} want={want!r}')

# ---- parse ----
check_eq('parse empty', parse_blocks(''), [])
check_eq('parse no-marker', parse_blocks('plain text'), [])

txt = f'{H}BEGIN{H}\nid: AAAA0001\nop: read\npath: x\n{H}END{H}'
bs = parse_blocks(txt)
check_eq('parse simple count', len(bs), 1)
if bs:
    check_eq('parse id', bs[0].id, 'AAAA0001')
    check_eq('parse op', bs[0].op, 'read')
    check_eq('parse path', bs[0].path, 'x')

txt2 = f'{H}BEGIN{H}\nid: BBAA0042\nop: write\npath: y.txt\n{H}CONTENT{H}\nhello world\n{H}END{H}'
bs2 = parse_blocks(txt2)
check_eq('parse write count', len(bs2), 1)
if bs2:
    check_eq('parse write body', bs2[0].content, 'hello world')

bad = f'{H}BEGIN{H}\nid: BAD\nop: read\npath: x\n{H}END{H}'
check_eq('parse bad-id skip', parse_blocks(bad), [])

# ---- ledger ----
tmp = Path(tempfile.mkdtemp(prefix='v5smoke_'))
try:
    led_path = tmp / 'ledger.json'
    stale_path = tmp / 'stale.log'
    led = Ledger(led_path, stale_path, max_entries=10)
    b1 = Block(id='AAAA0001', op='read', path='x')
    ok, reason = led.check(b1)
    check_eq('ledger first ok', (ok, reason), (True, 'ok'))
    led.commit(b1)
    ok, reason = led.check(b1)
    check('ledger dup blocked', not ok and 'duplicate' in reason, reason)
    b2 = Block(id='AAAA0001', op='write', path='x', content='diff')
    ok, reason = led.check(b2)
    check('ledger collision blocked', not ok and 'collision' in reason, reason)
    b3 = Block(id='AAAA0002', op='read', path='y')
    ok, _ = led.check(b3)
    check('ledger new ok', ok)
    led.commit(b3)
    led2 = Ledger(led_path, stale_path, max_entries=10)
    check_eq('ledger persists watermark', led2.watermark, 'AAAA0002')
    b_stale = Block(id='AAAA0000', op='read', path='x')
    ok, reason = led2.check(b_stale)
    check('ledger stale below wm', not ok and 'below' in reason, reason)
    b4 = Block(id='AAAA0003', op='read', path='z')
    ok, _ = led2.check(b4)
    check('ledger above wm ok', ok)

    # ---- ops ----
    root = tmp / 'root'
    root.mkdir()
    r = execute(root, Block(id='AAAA0100', op='write', path='a/b.txt', content='hi'))
    check('op write ok', r.get('ok'), r.get('error', ''))
    check('op write file exists', (root / 'a' / 'b.txt').exists())
    r = execute(root, Block(id='AAAA0101', op='read', path='a/b.txt'))
    check_eq('op read content', r.get('content'), 'hi')
    r = execute(root, Block(id='AAAA0102', op='write', path='a/b.txt', content='hi'))
    check('op write unchanged', r.get('unchanged'), r.get('error', ''))
    r = execute(root, Block(id='AAAA0103', op='list', path='a'))
    check('op list has b.txt', any(i['name'] == 'b.txt' for i in r.get('items', [])))
    r = execute(root, Block(id='AAAA0104', op='hash', path='a/b.txt'))
    check('op hash ok', r.get('ok') and len(r.get('sha256', '')) == 64)
    r = execute(root, Block(id='AAAA0105', op='run', cmd='echo hello', timeout=10))
    check('op run ok', r.get('ok'), r.get('stderr', ''))
    # escape
    try:
        safe_path(root, '../outside.txt')
        check('safe_path escape', False, 'should raise')
    except OpError:
        check('safe_path escape', True)

finally:
    shutil.rmtree(tmp, ignore_errors=True)

lines.append(f'--- fails={fails} ---')
out_path.write_text('\n'.join(lines), encoding='utf-8')
print(f'WROTE {out_path} fails={fails}')
sys.exit(1 if fails else 0)