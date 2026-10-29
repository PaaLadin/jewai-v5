"""Edge cases for parse_blocks and Ledger."""
import shutil, sys, tempfile
from pathlib import Path

ROOT = Path(r'C:/JewAI')
sys.path.insert(0, str(ROOT))

from Bridge.exec import Block, parse_blocks, Ledger, execute, safe_path, OpError

OUT = Path(__file__).resolve().parent.parent.parent / Path('logs/runtime/_v5_edge.txt')
lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond:
        lines.append('OK   ' + name)
    else:
        fails += 1
        lines.append('FAIL ' + name + ' ' + detail)

H = '#' * 3

# empty / weird
check('empty str', parse_blocks('') == [])
check('None-ish', parse_blocks('   ') == [])
check('BEGIN without END', parse_blocks(f'{H}BEGIN{H}\nid: AAAA0001\nop: read\npath: x') == [])

# lowercase hex in id (should fail: only uppercase)
check('lowercase id', parse_blocks(f'{H}BEGIN{H}\nid: aaaa0001\nop: read\npath: x\n{H}END{H}') == [])

# id 3 letters (must fail: exactly 4)
check('id 3 letters', parse_blocks(f'{H}BEGIN{H}\nid: AAA0001\nop: read\npath: x\n{H}END{H}') == [])
check('id 5 letters', parse_blocks(f'{H}BEGIN{H}\nid: AAAAA001\nop: read\npath: x\n{H}END{H}') == [])
check('id 3 digits', parse_blocks(f'{H}BEGIN{H}\nid: AAAA001\nop: read\npath: x\n{H}END{H}') == [])

# missing op
check('no op', parse_blocks(f'{H}BEGIN{H}\nid: AAAA0001\npath: x\n{H}END{H}') == [])

# no CONTENT -> body empty for write
bs = parse_blocks(f'{H}BEGIN{H}\nid: AAAA0001\nop: write\npath: x\n{H}END{H}')
check('write no CONTENT -> empty body', len(bs) == 1 and bs[0].content == '')

# write with CRLF body
bs = parse_blocks(f'{H}BEGIN{H}\nid: AAAA0002\nop: write\npath: x\r\n{H}CONTENT{H}\r\nline1\r\nline2\r\n{H}END{H}')
check('write CRLF body stripped', len(bs) == 1 and bs[0].content == 'line1\r\nline2')

# write with empty body
bs = parse_blocks(f'{H}BEGIN{H}\nid: AAAA0003\nop: write\npath: x\n{H}CONTENT{H}\n\n{H}END{H}')
check('write empty body', len(bs) == 1 and bs[0].content == '')

# multiple blocks, dedupe by id at collect level (not parser) - parser returns both
bs = parse_blocks(f'{H}BEGIN{H}\nid: AAAA0001\nop: read\npath: a\n{H}END{H}\n{H}BEGIN{H}\nid: AAAA0001\nop: read\npath: b\n{H}END{H}')
check('parser keeps both (dedupe is collect-level)', len(bs) == 2)

# body containing marker-like text should not break regex (non-greedy)
inner = f'{H}BEGIN{H}\nid: AAAA0004\nop: write\npath: x\n{H}CONTENT{H}\ncontains {H}END{H} in body? no\n{H}END{H}'
bs = parse_blocks(inner)
check('write body with END-like marker', len(bs) == 1 and 'contains' in bs[0].content, str(bs))

# unknown op still parses (exec will fail)
bs = parse_blocks(f'{H}BEGIN{H}\nid: AAAA0005\nop: unknown\npath: x\n{H}END{H}')
check('unknown op parses', len(bs) == 1 and bs[0].op == 'unknown')

# --- Ledger watermark ordering ---
tmp = tempfile.mkdtemp(prefix='v5edge_')
try:
    L = Ledger(Path(tmp) / 'l.json', Path(tmp) / 's.log', max_entries=5)
    # out of order: commit AAAA0010 then AAAA0005
    b10 = Block(id='AAAA0010', op='read', path='a')
    b05 = Block(id='AAAA0005', op='read', path='a')
    L.check(b10); L.commit(b10)
    L2 = Ledger(Path(tmp) / 'l.json', Path(tmp) / 's.log', max_entries=5)
    check('watermark AAAA0010', L2.watermark == 'AAAA0010', L2.watermark)
    ok, reason = L2.check(b05)
    check('older id blocked below wm', (not ok) and 'below_watermark' in reason, reason)

    # collision: same id, different content
    b10b = Block(id='AAAA0010', op='read', path='DIFFERENT')
    ok, reason = L2.check(b10b)
    check('same id different hash -> collision', (not ok) and 'id_collision' in reason, reason)

    # cleanup: max_entries is applied at save
    for i in range(20, 30):
        b = Block(id='AAAA00%02d' % i, op='read', path='x')
        ok, _ = L2.check(b)
        if ok: L2.commit(b)
    import json as _j
    saved = _j.loads((Path(tmp) / 'l.json').read_text(encoding='utf-8'))
    check('hashes trimmed <= max_entries', len(saved['hashes']) <= 5, str(len(saved['hashes'])))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)