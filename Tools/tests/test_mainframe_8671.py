"""Test Mainframe in-process on alternate port 8671 (8670 is occupied by unknown process)."""
import sys, threading, time, socket, urllib.request, json
from pathlib import Path

ROOT = Path(r'C:/JewAI')
sys.path.insert(0, str(ROOT))

import dataclasses
from Core.config import load as load_config
from Mainframe import web, api, llm

out = Path(r'C:/DeepSeek/logs/D/_v5_mf_8671.txt')
lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond:
        lines.append('OK   ' + name)
    else:
        fails += 1
        lines.append('FAIL ' + name + ' ' + detail)

cfg0 = load_config()
# clone config with alternate port
cfg = dataclasses.replace(cfg0, chat_port=8671)

# port free check
s = socket.socket(); s.settimeout(0.5)
busy = (s.connect_ex(('127.0.0.1', 8671)) == 0); s.close()
check('port 8671 free', not busy)
if busy:
    out.write_text('\n'.join(lines) + '\n--- ABORT ---\n', encoding='utf-8')
    print('ABORT 8671 busy'); raise SystemExit(1)

routes = {
    ('GET', '/api/status'): api.status,
    ('GET', '/api/health'): api.health,
    ('GET', '/api/projects'): api.projects,
    ('GET', '/api/chat_url/'): api.chat_url,
    ('GET', '/api/llm'): lambda c, p, b: llm.status(c),
    ('POST', '/api/llm/query'): lambda c, p, b: llm.query(c, (b or {}).get('text', '')),
}
srv = web.make_server(cfg, routes)
th = threading.Thread(target=srv.serve_forever, daemon=True)
th.start()
time.sleep(0.6)

base = 'http://127.0.0.1:8671'
def get(path):
    import urllib.error
    try:
        with urllib.request.urlopen(base + path, timeout=5) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, (e.read() or b'').decode('utf-8', 'replace')
    except Exception as e:
        return None, repr(e)

code, body = get('/api/health')
check('/api/health 200', code == 200, str(code) + ' ' + body[:80])
try: j = json.loads(body)
except Exception: j = {}
check('/api/health ok', j.get('ok') is True, body[:80])
check('/api/health version', j.get('version') == '0.1.0-dev', str(j.get('version')))

code, body = get('/api/status')
check('/api/status 200', code == 200, str(code))
try: j = json.loads(body)
except Exception: j = {}
check('/api/status ok', j.get('ok') is True)
chans = j.get('channels', {})
check('/api/status 6 channels', len(chans) == 6, str(len(chans)))
if 'C' in chans:
    c = chans['C']
    check('/api/status C agent 8668', c.get('agent_port') == 8668, str(c.get('agent_port')))
    check('/api/status C cdp 9124', c.get('cdp_port') == 9124, str(c.get('cdp_port')))
    check('/api/status C cdp_alive true', c.get('cdp_alive') is True, str(c.get('cdp_alive')))

code, body = get('/api/projects')
check('/api/projects 200', code == 200, str(code))
try: j = json.loads(body)
except Exception: j = {}
check('/api/projects ok', j.get('ok') is True)

code, body = get('/api/llm')
check('/api/llm 200', code == 200)
try: j = json.loads(body)
except Exception: j = {}
check('/api/llm stub configured false', j.get('configured') is False)

code, body = get('/')
check('/ 200', code == 200, str(code))
check('/ title', 'JewAI v5' in body, body[:80])

code, body = get('/style.css')
check('/style.css 200', code == 200, str(code))

code, body = get('/app.js')
check('/app.js 200', code == 200, str(code))

code, body = get('/api/unknown')
check('/api/unknown 404', code == 404, str(code))

srv.shutdown()
time.sleep(0.3)

lines.append('--- fails=%d ---' % fails)
out.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (out, fails))
sys.exit(1 if fails else 0)