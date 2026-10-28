"""Tests for Adapters/qwen.py and Adapters/alice.py with mocked CDP."""
import sys
from pathlib import Path

ROOT = Path(r'C:/JewAI')
sys.path.insert(0, str(ROOT))

from Adapters.qwen import Qwen
from Adapters.alice import Alice
from Bridge.exec import Block

OUT = Path(r'C:/DeepSeek/logs/D/_v5_adapters_test.txt')
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
block_ok = f'{H}BEGIN{H}\nid: CCAA0001\nop: read\npath: x\n{H}END{H}'

# ---- Qwen normalize ----
check('qwen normalize NBSP', Qwen._normalize('a\u00a0b') == 'a b')
check('qwen normalize CRLF', Qwen._normalize('a\r\nb') == 'a\nb')
check('qwen gutter strip', '1' not in Qwen._normalize('1\ncode\n2').split('\n'), repr(Qwen._normalize('1\ncode\n2')))
check('qwen gutter keeps code', Qwen._normalize('1\ncode\n2') == 'code', repr(Qwen._normalize('1\ncode\n2')))

# ---- Alice normalize ----
check('alice normalize NBSP', Alice._normalize('a\u00a0b') == 'a b')
check('alice normalize CRLF', Alice._normalize('a\r\nb') == 'a\nb')
check('alice keeps digits', Alice._normalize('1\ncode\n2') == '1\ncode\n2')

# ---- collect_blocks via mocked CDP ----
class FakeCDPGlued:
    def __init__(self, glued):
        self.glued = glued
    def eval_expr(self, expr):
        if 'glued' in expr or 'querySelectorAll' in expr:
            return self.glued
        return ''

q = Qwen()
blocks = q.collect_blocks(FakeCDPGlued(block_ok))
check('qwen collect 1 block', len(blocks) == 1, str(blocks))
if blocks:
    check('qwen block id', blocks[0].id == 'CCAA0001')

a = Alice()
blocks = a.collect_blocks(FakeCDPGlued(block_ok))
check('alice collect 1 block', len(blocks) == 1, str(blocks))
if blocks:
    check('alice block id', blocks[0].id == 'CCAA0001')

# empty glued -> empty blocks
check('qwen empty glued -> []', q.collect_blocks(FakeCDPGlued('')) == [])
check('alice empty glued -> []', a.collect_blocks(FakeCDPGlued('')) == [])

# dedupe: two blocks same id, only one returned
glued2 = block_ok + '\n' + block_ok
blocks = q.collect_blocks(FakeCDPGlued(glued2))
check('qwen dedupe by id', len(blocks) == 1, str(blocks))

# ---- send_text: mocked CDP that simulates textarea clearing after Enter ----
class FakeCDPSend:
    def __init__(self, clears_after=1):
        self.calls = []
        self.clears_after = clears_after
        self.enter_count = 0
        self.filled = ''
    def eval_expr(self, expr):
        self.calls.append(expr[:40])
        if 'value' in expr and 'setter.call' in expr:
            self.filled = 'FILLED'
            return True
        if 'return ta ? ta.value' in expr or "return ta ? ta.value : ''" in expr:
            if self.enter_count >= self.clears_after:
                return ''
            return self.filled or ''
        if 'KeyboardEvent' in expr:
            self.enter_count += 1
            return None
        if 'querySelector' in expr:
            return True
        if 'button' in expr or 'message-input-right-button-send' in expr:
            # Qwen send DIV click - count as clear too
            self.enter_count += 1
            return True
        return None

# Qwen send: first click clears (clears_after=1)
qcdp = FakeCDPSend(clears_after=1)
ok = Qwen().send_text(qcdp, 'hello')
check('qwen send_text returns True when click clears', ok, 'enter_count=%d filled=%r' % (qcdp.enter_count, qcdp.filled))

# Alice send: Enter x2 clears
acdp = FakeCDPSend(clears_after=1)
ok = Alice().send_text(acdp, 'hello')
check('alice send_text returns True when Enter clears', ok, 'enter_count=%d filled=%r' % (acdp.enter_count, acdp.filled))

# send_text with no textarea -> False
class FakeNoTA:
    def eval_expr(self, expr):
        if 'querySelector' in expr and 'return false' in expr:
            return False
        if 'querySelector' in expr:
            return None
        return None
# Note: our fill code returns false when no ta; check that path
check('qwen no textarea -> False', Qwen().send_text(FakeNoTA(), 'x') is False)
check('alice no textarea -> False', Alice().send_text(FakeNoTA(), 'x') is False)

# ---- verify_prompt_hits ----
class FakeBody:
    def __init__(self, body): self.body = body
    def eval_expr(self, expr):
        if 'innerText' in expr: return self.body
        return ''
check('qwen verify 2/3', Qwen().verify_prompt_hits(FakeBody('m1 m2'), ['m1','m2','m3']) == 2)
check('alice verify 0/2', Alice().verify_prompt_hits(FakeBody('x'), ['m1','m2']) == 0)

# ---- hosts / selectors ----
check('qwen host', Qwen.HOST == 'chat.qwen.ai')
check('alice host', Alice.HOST == 'alice.yandex.ru')
check('qwen textarea', Qwen.TEXTAREA_SELECTOR == 'textarea.message-input-textarea')
check('alice textarea', Alice.TEXTAREA_SELECTOR == 'textarea.AliceInput-Textarea')

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)