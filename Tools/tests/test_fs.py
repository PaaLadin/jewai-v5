"""Test /fs route: valid files 200, escape 403, missing 404."""
import json, shutil, sys, tempfile, threading, time, urllib.request, urllib.error, socket
from pathlib import Path

ROOT = Path(r'C:/JewAI')
sys.path.insert(0, str(ROOT))

import dataclasses
from Core.config import load as load_config
from Mainframe import web, controls

OUT = Path(r'C:/DeepSeek/logs/D/_v5_fs_test.txt')
lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond: lines.append('OK   ' + name)
    else: fails += 1; lines.append('FAIL ' + name + ' ' + detail)

tmp = Path(tempfile.mkdtemp(prefix='v5fs_'))
try:
    # create test files in tmp
    (tmp / 'a.md').write_text('hello', encoding='utf-8')
    (tmp / 'sub').mkdir()
    (tmp / 'sub' / 'index.html').write_text('<h1>sub</h1>', encoding='utf-8')
    outside = tmp.parent / ('outside_' + Path(tmp).name + '.txt')
    outside.write_text('secret', encoding='utf-8')

    cfg0 = load_config()
    cfg = dataclasses.replace(cfg0, root=tmp, chat_port=8671)

    # port check
    s = socket.socket(); s.settimeout(0.3)
    busy = (s.connect_ex(('127.0.0.1', 8671)) == 0); s.close()
    if busy:
        OUT.write_text('\n'.join(lines) + '\nABORT port busy\n', encoding='utf-8')
        print('ABORT'); sys.exit(1)

    srv = web.make_server(cfg, {})
    th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
    time.sleep(0.4)

    base = 'http://127.0.0.1:8671'
    def get(path):
        try:
            with urllib.request.urlopen(base + path, timeout=5) as r:
                return r.status, r.read(), r.headers.get('Content-Type', '')
        except urllib.error.HTTPError as e:
            return e.code, b'', ''
        except Exception:
            return None, b'', ''

    code, body, ct = get('/fs/a.md')
    check('/fs/a.md 200', code == 200, str(code))
    check('/fs/a.md content hello', body == b'hello', str(body[:20]))
    check('/fs/a.md ctype text/plain', 'text/plain' in ct, ct)

    code, body, ct = get('/fs/sub')
    check('/fs/sub (dir) -> index.html 200', code == 200, str(code))
    check('/fs/sub content <h1>', b'<h1>sub</h1>' in body, str(body[:20]))
    check('/fs/sub ctype html', 'text/html' in ct, ct)

    code, body, ct = get('/fs/../outside_' + tmp.name + '.txt')
    check('/fs escape 403', code == 403, str(code))

    code, body, ct = get('/fs/missing.md')
    check('/fs missing 404', code == 404, str(code))

    srv.shutdown(); time.sleep(0.2)
finally:
    try: outside.unlink()
    except Exception: pass
    shutil.rmtree(tmp, ignore_errors=True)

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)