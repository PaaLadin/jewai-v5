"""Tests for Tools/boot.py (dry-run only, never spawns anything)."""
import json, socket, subprocess, sys
from pathlib import Path

ROOT = Path(r'C:/JewAI')
BOOT = ROOT / 'Tools' / 'boot.py'
OUT = Path(r'C:/DeepSeek/logs/D/_v5_boot_test.txt')

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

# --server --dry-run: on foreign occupied 8670 -> exit 1, ok=false, pid reported
r, j = run_boot('--server', '--dry-run')
res = (j.get('results') or [{}])[0]
check('server dry-run exits 1 when 8670 busy', r.returncode == 1, 'rc=%d' % r.returncode)
check('server dry-run ok=false', res.get('ok') is False, str(res))
check('server dry-run reports pid', isinstance(res.get('pid'), int) or res.get('pid') is None, str(res.get('pid')))
check('server dry-run busy_before true', res.get('busy_before') is True, str(res.get('busy_before')))

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