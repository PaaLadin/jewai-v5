"""Tests for Bridge/cdp.py (find_chat, CDP wrapper), Bridge/read.py (mocked CDP),
Tools/launcher.py dry-run and helpers."""
import json, socket, sys, threading, urllib.request, urllib.error, shutil, tempfile
from pathlib import Path

ROOT = Path(r'C:/JewAI')
sys.path.insert(0, str(ROOT))

import dataclasses
from Core.config import load as load_config, Channel, Config
from Bridge.cdp import CDPError, CDP, find_chat
from Bridge.read import read_text, read_textarea, read_heartbeat, current_url
from Tools.launcher import launch, wait_cdp, _cdp_up, DEFAULT_START_URL

OUT = Path(__file__).resolve().parent.parent.parent / Path('logs/runtime/_v5_cdp_test.txt')
lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond:
        lines.append('OK   ' + name)
    else:
        fails += 1
        lines.append('FAIL ' + name + ' ' + detail)

# --- find_chat: mock /json/list via local http server on random port ---
class _FakeTargets:
    def __init__(self, targets):
        self.targets = targets
    def serve(self, port):
        from http.server import BaseHTTPRequestHandler, HTTPServer
        data = json.dumps(self.targets).encode('utf-8')
        class H(BaseHTTPRequestHandler):
            def log_message(self, *a): pass
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        srv = HTTPServer(('127.0.0.1', port), H)
        th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
        return srv

# pick free port
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()

fake = _FakeTargets([
    {'type': 'page', 'url': 'https://chat.deepseek.com/a/chat/s/abc', 'webSocketDebuggerUrl': 'ws://fake/1'},
    {'type': 'page', 'url': 'https://other.com/', 'webSocketDebuggerUrl': 'ws://fake/2'},
    {'type': 'other', 'url': 'https://chat.deepseek.com/a/chat/s/xx', 'webSocketDebuggerUrl': 'ws://fake/3'},
])
srv = fake.serve(port)

try:
    t = find_chat(port, 'chat.deepseek.com', '/a/chat/s/')
    check('find_chat found', t is not None and 'deepseek' in t.get('url', ''), str(t))
    t2 = find_chat(port, 'deepseek.com', '/a/chat/s/')  # no match -> fallback host
    check('find_chat fallback to host', t2 is not None and 'deepseek' in t2.get('url', ''), str(t2))
    t3 = find_chat(port, 'nomatch.example', '/a/chat/s/')
    check('find_chat no match -> None', t3 is None, str(t3))
finally:
    srv.shutdown()

# --- read.py with mocked CDP class ---
class FakeCDP:
    def __init__(self, values):
        self.values = values
    def eval_expr(self, expr):
        for key, val in self.values.items():
            if key in expr:
                return val
        return None

cfg = load_config()
ch = cfg.channel('C')

# read_text
c = FakeCDP({'innerText': 'hello body'})
check('read_text', read_text(c) == 'hello body', repr(read_text(c)))

# read_textarea: textarea selector and value
class FakeCDP2:
    def eval_expr(self, expr):
        if 'querySelector' in expr:
            return {'found': True, 'value': 'hi', 'len': 2}
        return None
r = read_textarea(FakeCDP2(), 'textarea')
check('read_textarea found', r['found'] and r['value'] == 'hi', str(r))

# read_textarea missing
class FakeCDP3:
    def eval_expr(self, expr):
        if 'querySelector' in expr:
            return {'found': False, 'value': '', 'len': 0}
        return None
r = read_textarea(FakeCDP3(), 'textarea')
check('read_textarea missing', not r['found'], str(r))

# read_heartbeat
class FakeHB:
    def __init__(self, v): self.v = v
    def eval_expr(self, expr):
        if 'dsbHeartbeat' in expr: return self.v
        return None
r = read_heartbeat(FakeHB(''))
check('heartbeat absent -> stale', r['present'] is False and r['stale'] is True, str(r))
import time
now_ms = int(time.time() * 1000)
r = read_heartbeat(FakeHB(str(now_ms)))
check('heartbeat fresh', r['present'] and not r['stale'], str(r))
r = read_heartbeat(FakeHB(str(now_ms - 30000)))
check('heartbeat old -> stale', r['present'] and r['stale'], str(r))

# --- launcher ---
# DEFAULT_START_URL
check('DEFAULT_START_URL has deepseek', 'deepseek' in DEFAULT_START_URL)
# dry-run
r = launch(cfg, 'C', dry=True)
check('launcher dry-run ok', r.get('ok') is True and r.get('dry') is True, str(r))
check('launcher dry has user-data-dir', any('--user-data-dir' in a for a in r.get('args', [])), str(r.get('args', [])[:3]))
check('launcher dry has cdp port', any('--remote-debugging-port=9124' in a for a in r.get('args', [])), str(r.get('args', [])[:3]))
r2 = launch(cfg, 'C', dry=True, no_proxy=True)
check('launcher no_proxy skips --proxy-server', not any('--proxy-server' in a for a in r2.get('args', [])))

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)