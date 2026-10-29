"""Daemon timing gates: min_gap, inflight-reset, coalesce, stable-gate behavior."""
import shutil, sys, tempfile, time
from pathlib import Path

ROOT = Path(r'C:/JewAI')
sys.path.insert(0, str(ROOT))

from Core.config import Config, Channel
from Bridge.exec import Block
from Bridge.daemon import Daemon

OUT = Path(__file__).resolve().parent.parent.parent / Path('logs/runtime/_v5_daemon_timing.txt')
lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond:
        lines.append('OK   ' + name)
    else:
        fails += 1
        lines.append('FAIL ' + name + ' ' + detail)

tmp = Path(tempfile.mkdtemp(prefix='v5dt_'))
try:
    ch = Channel(letter='C', name='TestC', agent_port=9998, cdp_port=9997,
                 prefix='CCAA', extension='extension', model='deepseek')
    cfg = Config(
        root=tmp, bind='127.0.0.1', chat_port=0, doh_proxy_port=0,
        letters=('C',), channels={'C': ch},
        thresholds={},
        timeouts={'cdp_poll': 10, 'stable_ms': 30, 'coalesce_ms': 10, 'min_gap_ms': 0},
        version='test',
    )

    class FakeCDP:
        def __init__(self, precount):
            self.precount = precount
        def eval_expr(self, expr):
            if 'querySelectorAll' in expr:
                return self.precount
            return ''

    class FakeAdapter:
        HOST = 'fake'
        TEXTAREA_SELECTOR = 'textarea'
        MARKER = '/fake/'
        blocks: list = []
        sent: list = []
        def collect_blocks(self, cdp, last_n=3):
            return list(FakeAdapter.blocks)
        def send_text(self, cdp, text):
            FakeAdapter.sent.append(text)
            return True
        def verify_prompt_hits(self, cdp, markers):
            return 0
        def new_chat(self, cdp):
            return True

    # ---- stable-gate ----
    daemon = Daemon(cfg, 'C', FakeAdapter())
    FakeAdapter.blocks = [Block(id='CCAA0001', op='write', path='a.txt', content='x')]
    r = daemon.tick(FakeCDP(5))
    check('tick1 no stable, no process', r.processed == 0, str(r))
    time.sleep(0.05)
    r = daemon.tick(FakeCDP(5))
    check('tick2 stable, processed 1', r.processed == 1, str(r))

    # ---- min_gap ----
    cfg2 = Config(root=tmp, bind='127.0.0.1', chat_port=0, doh_proxy_port=0,
                  letters=('C',), channels={'C': ch},
                  thresholds={},
                  timeouts={'cdp_poll': 10, 'stable_ms': 30, 'coalesce_ms': 10, 'min_gap_ms': 5000},
                  version='test')
    d2 = Daemon(cfg2, 'C', FakeAdapter())
    FakeAdapter.sent = []
    FakeAdapter.blocks = [Block(id='CCAA0002', op='write', path='b.txt', content='y')]
    d2.tick(FakeCDP(5)); time.sleep(0.05)
    r = d2.tick(FakeCDP(5))
    check('first send ok', r.processed == 1 and len(FakeAdapter.sent) == 1, str(r))
    # immediate next: min_gap=5000 blocks
    FakeAdapter.blocks = [Block(id='CCAA0003', op='write', path='c.txt', content='z')]
    r = d2.tick(FakeCDP(5))
    check('min_gap blocks immediate send', r.processed == 0, str(r))
    # manually clear last_send to allow
    d2._last_send_at = 0.0
    r = d2.tick(FakeCDP(5))
    check('after min_gap cleared, sends', r.processed == 1, str(r))

    # ---- inflight reset ----
    d3 = Daemon(cfg, 'C', FakeAdapter())
    d3._inflight_since = time.time() - 50  # 50s ago > 45s timeout
    FakeAdapter.sent = []
    FakeAdapter.blocks = [Block(id='CCAA0004', op='write', path='d.txt', content='w')]
    d3.tick(FakeCDP(5)); time.sleep(0.05)
    r = d3.tick(FakeCDP(5))
    check('inflight timeout reset allows', r.processed == 1, str(r))

    # ---- stable-gate change ----
    d4 = Daemon(cfg, 'C', FakeAdapter())
    FakeAdapter.sent = []
    FakeAdapter.blocks = [Block(id='CCAA0005', op='write', path='e.txt', content='v')]
    d4.tick(FakeCDP(5))  # baseline 5
    # count changes to 6 -> not stable yet
    r = d4.tick(FakeCDP(6))
    check('precount change breaks stable', r.processed == 0, str(r))
    time.sleep(0.05)
    r = d4.tick(FakeCDP(6))
    check('after change stable, processes', r.processed == 1, str(r))

finally:
    shutil.rmtree(tmp, ignore_errors=True)

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)