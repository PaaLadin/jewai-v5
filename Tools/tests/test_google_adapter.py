import sys
sys.path.insert(0, r'C:/JewAI')

from Adapters.google import Google
import io, contextlib, pathlib as _p
_OUT = _p.Path(r'C:/JewAI/logs/runtime/_v5_google_test.txt')
_OUT.parent.mkdir(parents=True, exist_ok=True)
_BUF = io.StringIO()
contextlib.redirect_stdout(_BUF).__enter__()


def check(name, cond, detail=''):
    print(('OK   ' if cond else 'FAIL ') + name + (' ' + detail if detail and not cond else ''))


g = Google()
check('HOST', g.HOST == 'google.com')
check('MARKER', g.MARKER == '/search')


class FakeCDP:
    """Scripted fake: cur_value call#1 returns ''; after insert, confirm returns ''."""
    def __init__(self, busy=False):
        self.busy = busy
        self.insert_seen = False
        self.enter_calls = 0
        self.click_calls = 0
        self.call_log = []
    def eval_expr(self, expr):
        # Order of checks matters: execCommand is unique to insertText step.
        if 'document.execCommand' in expr:
            self.insert_seen = True
            return True
        # _cur_value probes: distinguish busy vs empty
        if 'return (t.value' in expr or 't.value : ' in expr or 't.value !== undefined' in expr:
            return 'user typing' if self.busy else ''
        # _is_textarea probe
        if 'return t.tagName' in expr:
            return 'TEXTAREA'
        # verify_prompt_hits body
        if 'document.body' in expr:
            return 'hello'
        return ''
    def call(self, method, params=None):
        self.call_log.append(method)
        if method == 'Input.dispatchKeyEvent':
            self.enter_calls += 1
        if 'Mouse' in method:
            self.click_calls += 1
        return {}


# --- happy path ---
f = FakeCDP(busy=False)
ok = g.send_text(f, 'hello')
check('send_text returns True', ok is True)
check('execCommand insertText used', f.insert_seen)
check('Enter via CDP: 2 events (keyDown+keyUp)', f.enter_calls == 2, str(f.enter_calls))
check('NO mouse click on send button', f.click_calls == 0, str(f.click_calls))

# --- busy guard ---
b = FakeCDP(busy=True)
ok2 = g.send_text(b, 'should not send')
check('busy textarea -> False', ok2 is False)
check('busy: no enter events', b.enter_calls == 0)
check('busy: no insert attempted', b.insert_seen is False)

# --- verify_prompt_hits ---
class V:
    def eval_expr(self, e):
        return 'BEGIN AGENT ACK'
check('verify_prompt_hits counts', g.verify_prompt_hits(V(), ['BEGIN', 'AGENT', 'NOPE']) == 2)

print('DONE')
_out = _BUF.getvalue()
_OUT.write_text(_out, encoding='utf-8')
import sys as _s
_s.exit(1 if 'FAIL' in _out else 0)