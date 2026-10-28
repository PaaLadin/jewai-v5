"""F5 configured-path tests: fake LLM HTTP server, fake SMTP server.

Proves llm.query and mail.send actually work when config.llm / config.mail set.
"""
import json, shutil, socket, sys, tempfile, threading, time
from email import message_from_bytes
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(r'C:/JewAI')
sys.path.insert(0, str(ROOT))

import dataclasses
from Core.config import load as load_config
from Mainframe import llm, mail

OUT = Path(r'C:/DeepSeek/logs/D/_v5_f5_configured.txt')
lines = []
fails = 0

def check(name, cond, detail=''):
    global fails
    if cond:
        lines.append('OK   ' + name)
    else:
        fails += 1
        lines.append('FAIL ' + name + ' ' + detail)

# --- fake LLM server (POST /v1/chat/completions) ---
class FakeLLM(BaseHTTPRequestHandler):
    last_body: dict | None = None
    def log_message(self, *a): pass
    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0)
        raw = self.rfile.read(n) if n else b''
        try:
            FakeLLM.last_body = json.loads(raw.decode('utf-8')) if raw else {}
        except Exception:
            FakeLLM.last_body = {'_raw': raw[:200].decode('utf-8', 'replace')}
        resp = {"choices": [{"message": {"role": "assistant", "content": "fake reply"}}]}
        data = json.dumps(resp).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

s = socket.socket(); s.bind(('127.0.0.1', 0)); llm_port = s.getsockname()[1]; s.close()
llm_srv = HTTPServer(('127.0.0.1', llm_port), FakeLLM)
threading.Thread(target=llm_srv.serve_forever, daemon=True).start()
time.sleep(0.3)

# --- fake SMTP server (minimal: 220, 250, 250, 250 DATA->354, then 250 after .) ---
class FakeSMTP(threading.Thread):
    received: list = []
    def __init__(self, port):
        super().__init__(daemon=True)
        self.port = port
        self.stop_flag = False
        self.srv = socket.socket()
        self.srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.srv.bind(('127.0.0.1', port))
        self.srv.listen(5)
    def run(self):
        while not self.stop_flag:
            try:
                self.srv.settimeout(1.0)
                cli, _ = self.srv.accept()
            except Exception:
                continue
            try:
                cli.sendall(b'220 fake\r\n')
                in_data = False
                buf = b''
                while True:
                    chunk = cli.recv(4096)
                    if not chunk:
                        break
                    buf += chunk
                    while b'\r\n' in buf:
                        line, buf = buf.split(b'\r\n', 1)
                        if in_data:
                            if line == b'.':
                                in_data = False
                                cli.sendall(b'250 OK\r\n')
                            else:
                                FakeSMTP.received.append(line)
                            continue
                        cmd = line.upper()
                        if cmd.startswith(b'EHLO') or cmd.startswith(b'HELO'):
                            cli.sendall(b'250-fake\r\n250 OK\r\n')
                        elif cmd.startswith(b'MAIL FROM') or cmd.startswith(b'RCPT TO'):
                            cli.sendall(b'250 OK\r\n')
                        elif cmd.startswith(b'DATA'):
                            cli.sendall(b'354 Send\r\n')
                            in_data = True
                        elif cmd.startswith(b'QUIT'):
                            cli.sendall(b'221 Bye\r\n'); break
                        else:
                            cli.sendall(b'250 OK\r\n')
            except Exception:
                pass
            finally:
                try: cli.close()
                except Exception: pass
    def stop(self):
        self.stop_flag = True
        try: self.srv.close()
        except Exception: pass

s = socket.socket(); s.bind(('127.0.0.1', 0)); smtp_port = s.getsockname()[1]; s.close()
smtp = FakeSMTP(smtp_port)
smtp.start()
time.sleep(0.3)

tmp = tempfile.mkdtemp(prefix='v5f5c_')
try:
    cfg0 = load_config()
    cfg = dataclasses.replace(cfg0, root=Path(tmp))

    # --- llm configured ---
    (Path(tmp) / 'config.json').write_text(json.dumps({
        "llm": {"host": "127.0.0.1", "port": llm_port,
                "path": "/v1/chat/completions", "model": "test-model"},
    }), encoding='utf-8')
    st = llm.status(cfg)
    check('llm configured', st['configured'] is True, str(st))
    r = llm.query(cfg, 'hello llm', temperature=0.1, max_tokens=64)
    check('llm query ok', r.get('ok') is True, str(r)[:200])
    check('llm response has choices', 'choices' in (r.get('response') or {}), str(r)[:200])
    body = FakeLLM.last_body or {}
    check('llm body has model', body.get('model') == 'test-model', str(body)[:200])
    check('llm body has messages', isinstance(body.get('messages'), list) and len(body['messages']) == 1)
    check('llm body content', body['messages'][0]['content'] == 'hello llm', str(body)[:200])

    # llm not reachable -> error
    (Path(tmp) / 'config.json').write_text(json.dumps({
        "llm": {"host": "127.0.0.1", "port": 1, "path": "/x"},
    }), encoding='utf-8')
    r = llm.query(cfg, 'x', timeout=2)
    check('llm unreachable error', r.get('ok') is False, str(r)[:120])

    # --- mail configured ---
    (Path(tmp) / 'config.json').write_text(json.dumps({
        "mail": {"smtp_host": "127.0.0.1", "smtp_port": smtp_port,
                 "from_addr": "from@x", "to_addr": "to@y",
                 "use_tls": False, "password": ""},
    }), encoding='utf-8')
    st = mail.status(cfg)
    check('mail configured', st['configured'] is True, str(st))
    r = mail.send(cfg, 'Test subject', 'Test body line1\nline2')
    check('mail send ok', r.get('ok') is True, str(r)[:200])
    time.sleep(0.5)
    joined = b'\n'.join(FakeSMTP.received)
    check('smtp got DATA', len(FakeSMTP.received) > 0, str(FakeSMTP.received)[:200])
    check('smtp body has subject line or content', b'Subject' in joined or b'Test' in joined, joined[:200])
finally:
    try: llm_srv.shutdown()
    except Exception: pass
    smtp.stop()
    shutil.rmtree(tmp, ignore_errors=True)

lines.append('--- fails=%d ---' % fails)
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s fails=%d' % (OUT, fails))
sys.exit(1 if fails else 0)