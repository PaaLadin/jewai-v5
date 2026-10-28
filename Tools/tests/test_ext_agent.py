"""Test extension agent.py on port 8699 with temporary root.

Steps:
1. Copy agent.py to temp dir with .agent_token
2. Spawn python agent.py 8699
3. POST /write, /read, /list, /hash, /run (X-Token auth)
4. Kill process.
"""
import json, os, shutil, socket, subprocess, sys, tempfile, time, urllib.request, urllib.error
from pathlib import Path

SRC_AGENT = Path(r'C:/JewAI/Templates/extension/agent.py')
OUT = Path(r'C:/DeepSeek/logs/D/_v5_ext_agent_test.txt')
lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond: lines.append('OK   ' + name)
    else: fails += 1; lines.append('FAIL ' + name + ' ' + detail)

def port_free(port):
    s = socket.socket(); s.settimeout(0.3)
    try: return s.connect_ex(('127.0.0.1', port)) != 0
    finally: s.close()

TEST_PORT = 8699
check('port %d free' % TEST_PORT, port_free(TEST_PORT))
if not port_free(TEST_PORT):
    OUT.write_text('\n'.join(lines) + '\n--- ABORT ---\n', encoding='utf-8')
    print('ABORT port busy'); sys.exit(1)

tmp = Path(tempfile.mkdtemp(prefix='v5ext_'))
try:
    # install agent.py in tmp/extension/
    ext = tmp / 'extension'
    ext.mkdir()
    shutil.copyfile(SRC_AGENT, ext / 'agent.py')
    token = 'test_token_12345'
    (ext / '.agent_token').write_text(token, encoding='utf-8')

    # fake root config.json so agent finds root
    (tmp / 'config.json').write_text('{}', encoding='utf-8')

    env = dict(os.environ)
    env['JEWAI_ROOT'] = str(tmp)
    env['PYTHONIOENCODING'] = 'utf-8'

    proc = subprocess.Popen([sys.executable, str(ext / 'agent.py'), str(TEST_PORT)],
                            cwd=str(ext), env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
    time.sleep(1.5)

    def call(path, body=None, token_hdr=None):
        url = 'http://127.0.0.1:%d%s' % (TEST_PORT, path)
        headers = {'Content-Type': 'application/json'}
        if token_hdr:
            headers['X-Token'] = token_hdr
        data = json.dumps(body).encode('utf-8') if body is not None else None
        req = urllib.request.Request(url, data=data, headers=headers,
                                     method='POST' if data is not None else 'GET')
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, json.loads(r.read().decode('utf-8', 'replace'))
        except urllib.error.HTTPError as e:
            return e.code, {}
        except Exception as e:
            return None, {'error': repr(e)}

    # ping without token
    code, j = call('/ping')
    check('GET /ping 200', code == 200, str(code))
    check('ping ok', j.get('ok') is True, str(j))
    check('ping version 5.0.0', j.get('version') == '5.0.0', str(j.get('version')))

    # unauthorized write
    code, j = call('/write', {'path': 'x.txt', 'content': 'hi'})
    check('write without token -> 401', code == 401, str(code))

    # authorized write
    code, j = call('/write', {'path': 'sub/a.txt', 'content': 'hello ext'}, token_hdr=token)
    check('write with token ok', code == 200 and j.get('ok') is True, str(j)[:120])
    check('write file exists', (tmp / 'sub' / 'a.txt').exists())
    if (tmp / 'sub' / 'a.txt').exists():
        check('write content correct', (tmp / 'sub' / 'a.txt').read_text(encoding='utf-8') == 'hello ext')

    # read
    code, j = call('/read', {'path': 'sub/a.txt'}, token_hdr=token)
    check('read ok', code == 200 and j.get('content') == 'hello ext', str(j)[:120])

    # list
    code, j = call('/list', {'path': 'sub'}, token_hdr=token)
    check('list ok', code == 200 and any(x['name'] == 'a.txt' for x in j.get('items', [])), str(j)[:120])

    # hash
    code, j = call('/hash', {'path': 'sub/a.txt'}, token_hdr=token)
    check('hash sha256 64hex', code == 200 and j.get('ok') and len(j.get('sha256', '')) == 64, str(j)[:80])

    # run
    code, j = call('/run', {'cmd': 'echo hello_run', 'timeout': 10}, token_hdr=token)
    check('run ok', code == 200 and j.get('ok') is True, str(j)[:120])
    check('run stdout', 'hello_run' in (j.get('stdout') or ''), str(j.get('stdout', ''))[:80])

    # escape
    code, j = call('/read', {'path': '../escape.txt'}, token_hdr=token)
    check('escape blocked', code == 500 or (j.get('ok') is False), str(j)[:120])

    # wrong token
    code, j = call('/read', {'path': 'sub/a.txt'}, token_hdr='wrong')
    check('wrong token -> 401', code == 401, str(code))

    # cleanup
    proc.terminate()
    try: proc.communicate(timeout=5)
    except Exception: proc.kill()

finally:
    shutil.rmtree(tmp, ignore_errors=True)

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)