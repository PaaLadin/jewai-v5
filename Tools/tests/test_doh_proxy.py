"""Test Tools/doh_proxy.py: cache, doh_resolve (network), serve loop."""
import shutil, socket, subprocess, sys, tempfile, threading, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(r'C:/JewAI')
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'Tools'))

from Tools import doh_proxy

OUT = Path(__file__).resolve().parent.parent.parent / Path('logs/runtime/_v5_doh_test.txt')
lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond: lines.append('OK   ' + name)
    else: fails += 1; lines.append('FAIL ' + name + ' ' + str(detail))

# --- cache ---
c = doh_proxy.Cache(ttl=1)
check('cache miss', c.get('a') is None)
c.put('a', '1.2.3.4')
check('cache hit', c.get('a') == '1.2.3.4')
time.sleep(1.1)
check('cache expired', c.get('a') is None)

# --- doh_resolve network (may fail offline, skip if so) ---
ip = doh_proxy.doh_resolve('example.com')
if ip:
    check('doh_resolve example.com returns IPv4', '.' in ip and ip.count('.') == 3, ip)
    # second call from cache
    t0 = time.time()
    ip2 = doh_proxy.doh_resolve('example.com')
    el = time.time() - t0
    check('doh_resolve second fast (cache)', el < 0.1, '%.3fs' % el)
    check('doh_resolve cached equal', ip == ip2)
else:
    lines.append('SKIP doh_resolve (no network or DoH blocked)')

# --- serve loop + CONNECT on free port ---
s = socket.socket(); s.bind(('127.0.0.1', 0)); free = s.getsockname()[1]; s.close()
th = threading.Thread(target=doh_proxy.serve, args=(free,), daemon=True); th.start()
time.sleep(0.6)

# bad method -> 400
try:
    c1 = socket.create_connection(('127.0.0.1', free), timeout=3)
    c1.sendall(b"GET / HTTP/1.1\r\n\r\n")
    resp = c1.recv(200)
    c1.close()
    check('non-CONNECT -> 400', b'400' in resp, resp[:60])
except Exception as e:
    check('non-CONNECT test', False, repr(e)[:80])

# CONNECT to unresolvable host -> 502 (if no network, ok to be 502)
try:
    c2 = socket.create_connection(('127.0.0.1', free), timeout=3)
    c2.sendall(b"CONNECT no-such-host-xyz-12345.invalid:443 HTTP/1.1\r\n\r\n")
    resp = c2.recv(200)
    c2.close()
    check('CONNECT unresolvable -> 502', b'502' in resp, resp[:60])
except Exception as e:
    check('CONNECT 502 test', False, repr(e)[:80])

# CONNECT to localhost closed port: 502
try:
    c3 = socket.create_connection(('127.0.0.1', free), timeout=3)
    c3.sendall(b"CONNECT localhost:1 HTTP/1.1\r\n\r\n")
    resp = c3.recv(200)
    c3.close()
    # localhost may resolve via DoH to 127.0.0.1 or fail
    check('CONNECT localhost:1 responds', b'200' in resp or b'502' in resp, resp[:60])
except Exception as e:
    check('CONNECT localhost:1', False, repr(e)[:80])

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)