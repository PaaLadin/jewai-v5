"""Test extended Mainframe on 8671: full status/health schema + chat + svc routes."""
import json, shutil, sys, tempfile, threading, time, urllib.request, urllib.error, socket
from pathlib import Path

ROOT = Path(r'C:/JewAI')
sys.path.insert(0, str(ROOT))

import dataclasses
from Core.config import load as load_config
from Mainframe import web, api, llm, mail, rag_channel, council, health, svc_api

OUT = Path(__file__).resolve().parent.parent.parent / Path('logs/runtime/_v5_mf_ext_test.txt')
lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond: lines.append('OK   ' + name)
    else: fails += 1; lines.append('FAIL ' + name + ' ' + detail)

tmp = Path(tempfile.mkdtemp(prefix='v5mfx_'))
try:
    cfg0 = load_config()
    import socket as _sk
    _s0 = _sk.socket(); _s0.bind(("127.0.0.1", 0)); PORT = _s0.getsockname()[1]; _s0.close()
    cfg = dataclasses.replace(cfg0, root=tmp, chat_port=PORT)

    # port check (dynamic PORT chosen above; always free)
    busy = False
    if busy:
        OUT.write_text('\n'.join(lines) + '\n--- ABORT port busy ---\n', encoding='utf-8')
        print('ABORT'); sys.exit(1)

    routes = {
        ("GET", "/api/health"): lambda c, p, b: health.collect(c),
        ("POST", "/api/svc"): lambda c, p, b: svc_api.handle(c, (b or {}).get("channel", ""), (b or {}).get("kind", ""), (b or {}).get("action", ""), b),
        ("GET", "/api/status"): api.status,
        ("GET", "/api/messages"): lambda c, p, b: {"ok": True, "messages": council.load_messages(c, 200)},
        ("POST", "/api/send"): lambda c, p, b: council.send(c, (b or {}).get("from", "operator"), (b or {}).get("to", "ALL"), (b or {}).get("text", "")),
        ("GET", "/api/chat/"): lambda c, p, b: {"ok": True, "channel": p.rstrip("/").split("/")[-1].upper(), "messages": council.load_personal(c, p.rstrip("/").split("/")[-1].upper(), 200)},
        ("POST", "/api/chat/"): lambda c, p, b: council.send_personal(c, p.rstrip("/").split("/")[-1].upper(), (b or {}).get("from", "operator"), (b or {}).get("text", "")),
    }

    srv = web.make_server(cfg, routes)
    th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
    time.sleep(0.5)

    base = 'http://127.0.0.1:%d' % PORT
    def call(path, method='GET', body=None):
        data = json.dumps(body).encode('utf-8') if body is not None else None
        headers = {'Content-Type': 'application/json'} if data else {}
        req = urllib.request.Request(base + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=8) as r:
                return r.status, json.loads(r.read().decode('utf-8', 'replace'))
        except urllib.error.HTTPError as e:
            return e.code, {}
        except Exception as e:
            return None, {'error': repr(e)}

    # --- /api/status full schema ---
    code, j = call('/api/status')
    check('/api/status 200', code == 200, str(code))
    chans = j.get('channels', {})
    from Core.config import load as _lc0; _n0 = len(_lc0().letters); check('status dynamic channels', len(chans) == _n0, str(len(chans)) + ' vs ' + str(_n0))
    if 'C' in chans:
        c = chans['C']
        check('status C prefix CCAA', c.get('prefix') == 'CCAA', str(c.get('prefix')))
        check('status C model deepseek', c.get('model') == 'deepseek', str(c.get('model')))
        check('status C cdp 9124', c.get('cdp') == 9124, str(c.get('cdp')))
        check('status C agent 8668', c.get('agent') == 8668, str(c.get('agent')))

    # --- /api/health matrix ---
    code, j = call('/api/health')
    check('/api/health 200', code == 200, str(code))
    check('health ok', j.get('ok') is True)
    matrix = j.get('matrix', {})
    check('health matrix dynamic', len(matrix) == _n0, str(len(matrix)) + ' vs ' + str(_n0))
    if 'C' in matrix:
        h = matrix['C']
        for f in ('content', 'agent', 'watchdog', 'recovery', 'lastId', 'cmds_from_start'):
            check('health C has ' + f, f in h, str(h))
    check('health alerts list', isinstance(j.get('alerts'), list))

    # --- /api/send + /api/messages ---
    code, j = call('/api/send', method='POST', body={'from': 'operator', 'to': 'ALL', 'text': 'test broadcast'})
    check('/api/send ok', code == 200 and j.get('ok') is True, str(j)[:120])
    code, j = call('/api/messages')
    check('/api/messages ok', code == 200 and j.get('ok') is True)
    msgs = j.get('messages', [])
    check('messages has test broadcast', any(m.get('text') == 'test broadcast' for m in msgs), str(len(msgs)))

    # --- /api/chat/C ---
    code, j = call('/api/chat/C', method='POST', body={'from': 'operator', 'text': 'hello C personal'})
    check('/api/chat/C POST ok', code == 200 and j.get('ok') is True, str(j)[:120])
    code, j = call('/api/chat/C')
    check('/api/chat/C GET ok', code == 200 and j.get('ok') is True)
    check('chat/C has msg', any(m.get('text') == 'hello C personal' for m in j.get('messages', [])), str(len(j.get('messages', []))))

    # --- /api/chat/C ACL: from D should fail ---
    code, j = call('/api/chat/C', method='POST', body={'from': 'D', 'text': 'unauthorized'})
    check('/api/chat/C ACL blocks D', j.get('ok') is False and 'forbidden' in j.get('error', ''), str(j)[:120])

    # --- /api/svc: bad params ---
    code, j = call('/api/svc', method='POST', body={'channel': 'Z', 'kind': 'watchdog', 'action': 'start'})
    check('/api/svc bad channel', code == 200 and j.get('ok') is False, str(j)[:120])

    srv.shutdown(); time.sleep(0.3)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)