"""Tests for Tools/boot.py (dry-run only, never spawns anything)."""
import json, socket, subprocess, sys
from pathlib import Path

ROOT = Path(r'C:/JewAI')
BOOT = ROOT / 'Tools' / 'boot.py'
OUT = Path(__file__).resolve().parent.parent.parent / Path('logs/runtime/_v5_boot_test.txt')

lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond:
        lines.append('OK   ' + name)
    else:
        fails += 1
        lines.append('FAIL ' + name + ' ' + detail)

def run_boot(*args):
    r = subprocess.run([sys.executable, str(BOOT)] + list(args),
                       capture_output=True, text=True, timeout=30,
                       encoding='utf-8', errors='replace',
                       creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
    try:
        j = json.loads(r.stdout) if r.stdout else {}
    except Exception:
        j = {}
    return r, j

# --server --dry-run: occupy 8670 in-process, expect rc=1 ok=false busy_before=true
import socket as _sk
_occupy = _sk.socket(_sk.AF_INET, _sk.SOCK_STREAM)
_occupy.setsockopt(_sk.SOL_SOCKET, _sk.SO_REUSEADDR, 1)
try:
    _occupy.bind(('127.0.0.1', 8670)); _occupy.listen(1)
    _occupied = True
except Exception:
    _occupied = False
try:
    r, j = run_boot('--server', '--dry-run')
    res = (j.get('results') or [{}])[0]
    if _occupied:
        check('server dry-run exits 1 when 8670 busy', r.returncode == 1, 'rc=%d' % r.returncode)
        check('server dry-run ok=false', res.get('ok') is False, str(res))
        check('server dry-run reports pid', isinstance(res.get('pid'), int) or res.get('pid') is None, str(res.get('pid')))
        check('server dry-run busy_before true', res.get('busy_before') is True, str(res.get('busy_before')))
    else:
        check('server dry-run SKIP (8670 not occupiable)', True)
finally:
    try: _occupy.close()
    except Exception: pass

# --channel A --dry-run: Chrome A down, no spawn, reports dry
r, j = run_boot('--channel', 'A', '--dry-run')
results = j.get('results') or []
targets = {x.get('target'): x for x in results}
check('channel A dry-run returns chrome:A', 'chrome:A' in targets, str(list(targets.keys())))
# Chrome A not running -> dry spawn
check('chrome A dry-run ok (or already)', targets.get('chrome:A', {}).get('ok') is True, str(targets.get('chrome:A')))

# --channel C --dry-run: bridge dry
r, j = run_boot('--channel', 'C', '--dry-run')
targets = {x.get('target'): x for x in (j.get('results') or [])}
check('bridge:C dry present', 'bridge:C' in targets, str(list(targets.keys())))

# --all --dry-run --no-chrome --no-bridge: only server step
r, j = run_boot('--all', '--dry-run', '--no-chrome', '--no-bridge')
targets = [x.get('target') for x in (j.get('results') or [])]
check('all no-chrome no-bridge: only server', targets == ['server'], str(targets))

# bad args
r, _ = run_boot('--channel', 'Z')
check('bad channel exits non-zero', r.returncode != 0, 'rc=%d' % r.returncode)

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)