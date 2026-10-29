"""Tests for Bridge/run.py entrypoint: adapter selection, --once with dead/alive channel."""
import socket, subprocess, sys
from pathlib import Path

ROOT = Path(r'C:/JewAI')
RUN = ROOT / 'Bridge' / 'run.py'
OUT = Path(__file__).resolve().parent.parent.parent / Path('logs/runtime/_v5_run_test.txt')

lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond:
        lines.append('OK   ' + name)
    else:
        fails += 1
        lines.append('FAIL ' + name + ' ' + detail)

# test 1: adapter mapping from _adapter_for
sys.path.insert(0, str(ROOT))
from Bridge.run import _adapter_for
from Adapters.deepseek import DeepSeek
from Adapters.qwen import Qwen
from Adapters.alice import Alice

check('adapter deepseek', isinstance(_adapter_for('deepseek'), DeepSeek))
check('adapter qwen', isinstance(_adapter_for('qwen'), Qwen))
check('adapter alice', isinstance(_adapter_for('alice'), Alice))
check('adapter unknown -> deepseek', isinstance(_adapter_for('nonsense'), DeepSeek))

# test 2: subprocess --once against isolated config (cdp=9999 dead, not live 9122)
import json as _j, os as _o, tempfile as _tf
_iso_cfg_data = _j.loads((ROOT / 'config.json').read_text(encoding='utf-8'))
for _L in _iso_cfg_data.get('channels', {}):
    _iso_cfg_data['channels'][_L]['cdp'] = 9999
_iso_dir = Path(_tf.mkdtemp(prefix='v5run_'))
_iso_cfg = _iso_dir / 'config.json'
_iso_cfg.write_text(_j.dumps(_iso_cfg_data, indent=2, ensure_ascii=False), encoding='utf-8')
_iso_env = _o.environ.copy()
_iso_env['JEWAI_CONFIG'] = str(_iso_cfg)
r = subprocess.run([sys.executable, str(RUN), '--channel', 'A', '--once'],
                   capture_output=True, text=True, timeout=30,
                   encoding='utf-8', errors='replace',
                   env=_iso_env,
                   creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
import shutil as _sh
_sh.rmtree(_iso_dir, ignore_errors=True)
check('E --once exit 2', r.returncode == 2, 'rc=%d stdout=%r' % (r.returncode, (r.stdout or '')[:120]))
check('E --once no traceback', 'Traceback' not in (r.stderr or ''), (r.stderr or '')[:200])
check('E --once has no_chat_target', 'no_chat_target' in (r.stdout or ''), (r.stdout or '')[:120])

# test 3: --help exits 0
r = subprocess.run([sys.executable, str(RUN), '--help'],
                   capture_output=True, text=True, timeout=10,
                   encoding='utf-8', errors='replace',
                   creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
check('--help exit 0', r.returncode == 0, 'rc=%d' % r.returncode)
check('--help mentions channel', '--channel' in (r.stdout or ''), (r.stdout or '')[:200])

# test 4: invalid channel exits non-zero (argparse error -> 2)
r = subprocess.run([sys.executable, str(RUN), '--channel', 'Z', '--once'],
                   capture_output=True, text=True, timeout=10,
                   encoding='utf-8', errors='replace',
                   creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
check('bad channel exits non-zero', r.returncode != 0, 'rc=%d' % r.returncode)

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)