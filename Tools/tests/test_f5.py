"""F5 tests: llm stub, mail stub, rag_channel roundtrip, new routes on 8671."""
import json, shutil, sys, tempfile, threading, time, urllib.request, urllib.error, socket
from pathlib import Path

ROOT = Path(r'C:/JewAI')
sys.path.insert(0, str(ROOT))

import dataclasses
from Core.config import load as load_config
from Mainframe import web, api, llm, mail, rag_channel

OUT = Path(__file__).resolve().parent.parent.parent / Path('logs/runtime/_v5_f5_test.txt')
lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond:
        lines.append('OK   ' + name)
    else:
        fails += 1
        lines.append('FAIL ' + name + ' ' + detail)

tmp = tempfile.mkdtemp(prefix='v5f5_')
try:
    cfg0 = load_config()
    import socket as _sk
    _s0 = _sk.socket(); _s0.bind(('127.0.0.1', 0)); PORT = _s0.getsockname()[1]; _s0.close()
    cfg = dataclasses.replace(cfg0, root=Path(tmp), chat_port=PORT)
    # copy config.json into tmp root? No: llm/mail read cfg.path("config.json").
    # point at our tmp root/config.json (missing -> empty dict -> not_configured)
    # create empty config.json so reads do not fail
    (Path(tmp) / 'config.json').write_text('{}', encoding='utf-8')

    # ---- llm stub ----
    st = llm.status(cfg)
    check('llm not configured', st.get('configured') is False, str(st))
    r = llm.query(cfg, 'hi')
    check('llm query -> error', r.get('ok') is False and 'not configured' in r.get('error', ''), str(r))

    # ---- mail stub ----
    st = mail.status(cfg)
    check('mail not configured', st.get('configured') is False, str(st))
    r = mail.send(cfg, 'subj', 'body')
    check('mail send -> error', r.get('ok') is False and 'not configured' in r.get('error', ''), str(r))

    # ---- rag_channel ----
    (Path(tmp) / 'logs').mkdir(exist_ok=True)
    r = rag_channel.push(cfg, 'D', 'F', 'hello alice')
    check('rag push ok', r.get('ok') is True)
    r = rag_channel.push(cfg, 'D', 'ALL', 'broadcast')
    check('rag push broadcast ok', r.get('ok') is True)
    r = rag_channel.pull(cfg, 'F', since_ts=0)
    texts = [e.get('text') for e in r.get('entries', [])]
    check('rag pull F gets direct', 'hello alice' in texts, str(texts))
    check('rag pull F gets ALL', 'broadcast' in texts, str(texts))
    r2 = rag_channel.pull(cfg, 'A', since_ts=0)
    texts2 = [e.get('text') for e in r2.get('entries', [])]
    check('rag pull A skips F-only', 'hello alice' not in texts2, str(texts2))
    check('rag pull A gets ALL', 'broadcast' in texts2, str(texts2))
    r3 = rag_channel.pull(cfg, 'F', since_ts=time.time() + 1)
    check('rag pull since empty', len(r3.get('entries', [])) == 0)

    # ---- server routes on 8671 ----
    busy = False  # dynamic port, always free
    if busy:
        lines.append('SKIP server routes: 8671 busy')
    else:
        routes = {
            ('GET', '/api/health'): api.health,
            ('GET', '/api/llm'): lambda c, p, b: llm.status(c),
            ('POST', '/api/llm/query'): lambda c, p, b: llm.query(c, (b or {}).get('text', '')),
            ('GET', '/api/mail'): lambda c, p, b: mail.status(c),
            ('POST', '/api/mail/send'): lambda c, p, b: mail.send(c, (b or {}).get('subject', ''), (b or {}).get('body', '')),
            ('POST', '/api/rag/push'): lambda c, p, b: rag_channel.push(c, (b or {}).get('from', '?'), (b or {}).get('to', 'ALL'), (b or {}).get('text', '')),
            ('GET', '/api/rag/pull/'): lambda c, p, b: rag_channel.pull(c, p.rstrip('/').split('/')[-1].upper(), 0.0),
        }
        srv = web.make_server(cfg, routes)
        th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
        time.sleep(0.5)
        base = 'http://127.0.0.1:%d' % PORT
        def call(path, method='GET', body=None):
            data = None
            headers = {}
            if body is not None:
                data = json.dumps(body).encode('utf-8')
                headers['Content-Type'] = 'application/json'
            req = urllib.request.Request(base + path, data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=5) as r:
                    return r.status, json.loads(r.read().decode('utf-8', 'replace'))
            except urllib.error.HTTPError as e:
                return e.code, {}
            except Exception as e:
                return None, {'error': repr(e)}
        code, j = call('/api/health')
        check('GET /api/health 200', code == 200)
        code, j = call('/api/llm')
        check('GET /api/llm configured=false', code == 200 and j.get('configured') is False, str(j)[:100])
        code, j = call('/api/llm/query', method='POST', body={'text': 'x'})
        check('POST /api/llm/query ok=false', code == 200 and j.get('ok') is False, str(j)[:100])
        code, j = call('/api/mail')
        check('GET /api/mail configured=false', code == 200 and j.get('configured') is False, str(j)[:100])
        code, j = call('/api/rag/push', method='POST', body={'from': 'D', 'to': 'F', 'text': 'route msg'})
        check('POST /api/rag/push ok', code == 200 and j.get('ok') is True, str(j)[:100])
        code, j = call('/api/rag/pull/F')
        check('GET /api/rag/pull/F has route msg', code == 200 and any(e.get('text') == 'route msg' for e in j.get('entries', [])), str(j)[:200])
        srv.shutdown(); time.sleep(0.3)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)