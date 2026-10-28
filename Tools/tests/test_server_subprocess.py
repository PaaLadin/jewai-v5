"""Subprocess test: actually spawn Mainframe/server.py on port 8672, probe, kill.

Proves deployment works: the same entrypoint that runs on 8670 runs on 8672.
Requires config.chat_port override via env or temp config copy.

Approach: copy config.json to tmp with chat_port=8672, run server.py with
env JEWAI_CONFIG=tmp/config.json, probe, terminate.
"""
import json, os, shutil, socket, subprocess, sys, tempfile, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(r'C:/JewAI')
OUT = Path(r'C:/DeepSeek/logs/D/_v5_server_subprocess.txt')
lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond:
        lines.append('OK   ' + name)
    else:
        fails += 1
        lines.append('FAIL ' + name + ' ' + detail)

def get(path, base):
    try:
        with urllib.request.urlopen(base + path, timeout=5) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:
        return None, repr(e)

# pick free port
s = socket.socket(); s.bind(('127.0.0.1', 0)); free_port = s.getsockname()[1]; s.close()
lines.append('free_port=%d' % free_port)

tmp = Path(tempfile.mkdtemp(prefix='v5srv_'))
cfg_copy = tmp / 'config.json'
data = json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))
data['root'] = str(ROOT)  # keep real root, only override port
data['chat_port'] = free_port
cfg_copy.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')

env = dict(os.environ)
env['JEWAI_CONFIG'] = str(cfg_copy)
env['PYTHONIOENCODING'] = 'utf-8'

proc = subprocess.Popen(
    [sys.executable, str(ROOT / 'Mainframe' / 'server.py')],
    cwd=str(ROOT),
    env=env,
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
)
try:
    # wait for port
    up = False
    for _ in range(40):
        time.sleep(0.25)
        s2 = socket.socket(); s2.settimeout(0.3)
        if s2.connect_ex(('127.0.0.1', free_port)) == 0:
            up = True; s2.close(); break
        s2.close()
    check('server port opens', up, 'port=%d' % free_port)

    base = 'http://127.0.0.1:%d' % free_port
    if up:
        code, body = get('/api/health', base)
        check('GET /api/health 200', code == 200, str(code))
        try: j = json.loads(body)
        except Exception: j = {}
        check('health ok', j.get('ok') is True, body[:80])

        code, body = get('/api/status', base)
        check('GET /api/status 200', code == 200, str(code))
        try: j = json.loads(body)
        except Exception: j = {}
        check('status 6 channels', len(j.get('channels', {})) == 6, str(len(j.get('channels', {}))))

        code, body = get('/', base)
        check('GET / 200', code == 200, str(code))
        check('index title', 'Mainframe' in body or 'JewAI' in body, body[:80])

        code, body = get('/api/llm', base)
        check('GET /api/llm 200', code == 200, str(code))
        try: j = json.loads(body)
        except Exception: j = {}
        check('llm stub not configured', j.get('configured') is False, str(j)[:100])

        code, body = get('/api/mail', base)
        check('GET /api/mail 200', code == 200, str(code))

        code, body = get('/api/rag/pull/F', base)
        check('GET /api/rag/pull/F 200', code == 200, str(code))
finally:
    try:
        proc.terminate()
        try:
            out, err = proc.communicate(timeout=5)
        except Exception:
            proc.kill()
            out, err = proc.communicate(timeout=3)
    except Exception:
        pass
    time.sleep(0.5)
    # port closed?
    s3 = socket.socket(); s3.settimeout(0.3)
    closed = (s3.connect_ex(('127.0.0.1', free_port)) != 0)
    s3.close()
    check('port closed after kill', closed, 'port=%d' % free_port)
    shutil.rmtree(tmp, ignore_errors=True)

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)