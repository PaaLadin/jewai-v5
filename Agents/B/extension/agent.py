"""Extension/agent.py - HTTP endpoint for a channel.

Contract (from AUDIT section 18, rewritten from scratch):
- ThreadingHTTPServer on 127.0.0.1:<port>.
- X-Token auth (from .agent_token in extension dir).
- GET /ping -> ok, root, version, uptime.
- POST ops: /read, /write, /list, /mkdir, /delete, /hash, /run.
- All paths inside ROOT (config.root() via env).
- No /voice, /notify, /sandbox (excluded from v5).
"""
import hashlib, json, os, secrets, subprocess, sys, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# ROOT: from env JEWAI_ROOT, else walk up until config.json found
HERE = Path(__file__).resolve().parent
_env_root = os.environ.get("JEWAI_ROOT")
if _env_root:
    ROOT = Path(_env_root).resolve()
else:
    ROOT = HERE
    while ROOT.parent != ROOT:
        if (ROOT / "config.json").exists():
            break
        ROOT = ROOT.parent
    else:
        ROOT = HERE

TOKEN_FILE = HERE / ".agent_token"
if TOKEN_FILE.exists():
    TOKEN = TOKEN_FILE.read_text(encoding="utf-8").strip()
else:
    TOKEN = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(TOKEN, encoding="utf-8")

START = time.time()
VERSION = "5.0.0"


def _nw():
    if sys.platform != "win32":
        return 0
    return subprocess.CREATE_NO_WINDOW


def safe_path(rel):
    if not rel:
        raise ValueError("empty path")
    p = (ROOT / rel).resolve()
    if p != ROOT and ROOT not in p.parents:
        raise ValueError("escape: " + str(rel))
    return p


def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _auth(self):
        return self.headers.get("X-Token") == TOKEN

    def _j(self, code, obj):
        d = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Token")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Content-Length", str(len(d)))
        self.end_headers()
        self.wfile.write(d)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n)) if n else {}

    def do_OPTIONS(self):
        self._j(200, {"ok": True})

    def do_GET(self):
        if self.path == "/ping":
            return self._j(200, {"ok": True, "root": str(ROOT), "version": VERSION,
                                 "uptime": round(time.time() - START, 1)})
        return self._j(404, {"error": "not found"})

    def do_POST(self):
        if not self._auth():
            return self._j(401, {"error": "unauthorized"})
        try:
            b = self._body()
            op = self.path
            if op == "/read":
                p = safe_path(b["path"])
                t = p.read_text(encoding="utf-8", errors="replace")
                return self._j(200, {"ok": True, "path": str(p), "content": t,
                                     "bytes": len(t.encode("utf-8"))})
            if op == "/write":
                p = safe_path(b["path"])
                p.parent.mkdir(parents=True, exist_ok=True)
                c = b.get("content", "")
                if p.exists() and p.is_file():
                    try:
                        if p.read_text(encoding="utf-8") == c:
                            return self._j(200, {"ok": True, "path": str(p), "unchanged": True,
                                                 "bytes": len(c.encode("utf-8"))})
                    except Exception:
                        pass
                p.write_text(c, encoding="utf-8")
                return self._j(200, {"ok": True, "path": str(p),
                                     "bytes": len(c.encode("utf-8")), "sha256": sha256(p)})
            if op == "/list":
                p = safe_path(b.get("path", "."))
                items = []
                for x in sorted(p.iterdir()):
                    try:
                        items.append({"name": x.name, "is_dir": x.is_dir(),
                                      "size": x.stat().st_size if x.is_file() else 0})
                    except Exception:
                        pass
                return self._j(200, {"ok": True, "path": str(p), "items": items})
            if op == "/mkdir":
                p = safe_path(b["path"])
                p.mkdir(parents=True, exist_ok=True)
                return self._j(200, {"ok": True, "path": str(p)})
            if op == "/delete":
                p = safe_path(b["path"])
                if p.is_dir():
                    import shutil as _s; _s.rmtree(p)
                else:
                    p.unlink()
                return self._j(200, {"ok": True})
            if op == "/hash":
                p = safe_path(b["path"])
                if not p.exists():
                    return self._j(200, {"ok": False, "error": "not found"})
                return self._j(200, {"ok": True, "sha256": sha256(p), "bytes": p.stat().st_size})
            if op == "/run":
                cmd = b["cmd"]
                cwd = safe_path(b.get("cwd", "."))
                to = int(b.get("timeout", 60))
                t0 = time.time()
                try:
                    r = subprocess.run(cmd, shell=True, cwd=str(cwd),
                                       capture_output=True, text=True,
                                       encoding="utf-8", errors="replace",
                                       timeout=to, creationflags=_nw())
                    return self._j(200, {"ok": r.returncode == 0, "code": r.returncode,
                                         "stdout": r.stdout, "stderr": r.stderr,
                                         "elapsed": round(time.time() - t0, 2)})
                except subprocess.TimeoutExpired:
                    return self._j(200, {"ok": False, "code": -1, "stdout": "",
                                         "stderr": "TIMEOUT", "elapsed": round(time.time() - t0, 2)})
            return self._j(404, {"error": "unknown op " + op})
        except Exception as e:
            return self._j(500, {"error": type(e).__name__ + ": " + str(e)})


def _port_busy(port):
    import socket as s
    c = s.socket(s.AF_INET, s.SOCK_STREAM)
    c.settimeout(0.5)
    try:
        if c.connect_ex(("127.0.0.1", port)) == 0:
            return True
    finally:
        c.close()
    b = s.socket(s.AF_INET, s.SOCK_STREAM)
    try:
        b.bind(("127.0.0.1", port))
        return False
    except OSError:
        return True
    finally:
        b.close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8666
    if _port_busy(port):
        print("[guard] port", port, "busy, exit")
        sys.exit(0)
    print("[agent] v" + VERSION + " root=" + str(ROOT) + " port=" + str(port))
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()