"""Unit test for Daemon.tick(): mock adapter+cdp, real exec+ledger.

Proves full cycle: collect -> ledger check -> execute -> fmt_report -> send.
No Chrome, no real chat.
"""
import shutil, sys, tempfile
from pathlib import Path

ROOT = Path(r'C:/JewAI')
sys.path.insert(0, str(ROOT))

from Core.config import Config, Channel
from Bridge.exec import Block
from Bridge.daemon import Daemon

OUT = Path(r'C:/DeepSeek/logs/D/_v5_daemon_test.txt')
lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond:
        lines.append('OK   ' + name)
    else:
        fails += 1
        lines.append('FAIL ' + name + ' ' + detail)

# --- fake config / channel ---
tmp = Path(tempfile.mkdtemp(prefix='v5dm_'))
try:
    ch = Channel(letter='C', name='TestC', agent_port=9998, cdp_port=9997,
                 prefix='CCAA', extension='extension', model='deepseek')
    cfg = Config(
        root=tmp, bind='127.0.0.1', chat_port=0, doh_proxy_port=0,
        letters=('C',), channels={'C': ch},
        thresholds={}, timeouts={'cdp_poll': 100, 'stable_ms': 50,
                                  'coalesce_ms': 50, 'min_gap_ms': 0},
        version='test',
    )

    H = '#' * 3
    block_text = (
        f'{H}BEGIN{H}\nid: CCAA0001\nop: write\npath: t.txt\n'
        f'{H}CONTENT{H}\nhello-daemon\n{H}END{H}'
    )
    blocks_batch = [[Block(id='CCAA0001', op='write', path='t.txt', content='hello-daemon')]]

    class FakeCDP:
        def eval_expr(self, expr):
            # stable-gate: pre-count 5 (constant -> stable after first tick)
            if 'querySelectorAll' in expr:
                return 5
            return ''

    class FakeAdapter:
        HOST = 'fake'
        TEXTAREA_SELECTOR = 'textarea'
        MARKER = '/fake/'
        sent: list = []
        def collect_blocks(self, cdp, last_n=3):
            if blocks_batch:
                return blocks_batch[0]
            return []
        def send_text(self, cdp, text):
            self.sent.append(text)
            return True
        def verify_prompt_hits(self, cdp, markers):
            return 0
        def new_chat(self, cdp):
            return True

    daemon = Daemon(cfg, 'C', FakeAdapter())

    # first tick — sets stable baseline, no blocks
    r1 = daemon.tick(FakeCDP())
    check('tick1 no block', r1.processed == 0, str(r1))
    # second tick after stable window — processes block
    import time as _t
    _t.sleep(0.06)
    r2 = daemon.tick(FakeCDP())
    check('tick2 processed 1', r2.processed == 1, str(r2))
    check('write executed', (tmp / 't.txt').exists())
    if (tmp / 't.txt').exists():
        check('write content', (tmp / 't.txt').read_text(encoding='utf-8').strip() == 'hello-daemon')
    check('report sent once', len(daemon.adapter.sent) == 1, str(daemon.adapter.sent))
    if daemon.adapter.sent:
        rep = daemon.adapter.sent[0]
        check('report head', rep.startswith('[AGENT REPORT]'))
        check('report has id', 'CCAA0001' in rep)
        check('report has next_id', 'next_id: CCAA0002' in rep, rep[-80:])

    # third tick — ledger blocks replay
    blocks_batch[0] = [Block(id='CCAA0001', op='write', path='t.txt', content='hello-daemon')]
    _t.sleep(0.06)
    daemon._last_send_at = 0.0  # bypass min_gap for test
    r3 = daemon.tick(FakeCDP())
    check('tick3 no re-process', r3.processed == 0, str(r3))

    # stale log written
    stale = tmp / 'logs' / 'bridge' / 'stale_blocks.log'
    check('stale log exists', stale.exists())
    if stale.exists():
        check('stale has entry', 'CCAA0001' in stale.read_text(encoding='utf-8'))

finally:
    shutil.rmtree(tmp, ignore_errors=True)

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)