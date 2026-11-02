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

# 7C B-25: one token per installation (root .agent_token wins over per-channel)
def _find_token_file():
    # 7C B-25b: prefer ROOT token (install-wide), then per-channel fallback
    cands = [
        ROOT / ".agent_token",
        HERE / ".agent_token",
    ]
    for c in cands:
        try:
            if c.exists():
                return c
        except Exception:
            pass
    return None

TOKEN_FILE = _find_token_file()
if TOKEN_FILE is not None:
    TOKEN = TOKEN_FILE.read_text(encoding="utf-8").strip()
else:
    TOKEN_FILE = HERE / ".agent_token"
    TOKEN = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(TOKEN, encoding="utf-8")

START = time.time()
VERSION = "5.0.0"

# 7C B-14/B-15/B-16/B-17: channel identity from per-channel config
CHANNEL_CFG = None
# 7C fix: try per-channel layout (Profiles/<L>/config/config.json),
# then Templates layout (Templates/config/config.json), then root config.json.
_candidates = [
    HERE.parent / "config" / "config.json",           # Profiles/<L>/config/config.json (primary)
    HERE.parent.parent / "config" / "config.json",    # fallback (old layout)
    ROOT / "config.json",                              # root
]
for _cand in _candidates:
    try:
        if _cand.exists():
            CHANNEL_CFG = json.loads(_cand.read_text(encoding="utf-8"))
            break
    except Exception:
        continue
# if we loaded the root config.json, we need to descend into channels[<L>]
if CHANNEL_CFG and "channels" in CHANNEL_CFG and "channel" not in CHANNEL_CFG:
    _my_letter = None
    try:
        import os as _os
        # infer letter from path: .../Profiles/<L>/extension/agent.py
        _parts = HERE.parts
        if "Profiles" in _parts:
            _idx = _parts.index("Profiles")
            if _idx + 1 < len(_parts):
                _my_letter = _parts[_idx + 1]
    except Exception:
        pass
    if _my_letter and _my_letter in CHANNEL_CFG["channels"]:
        _root_cfg = CHANNEL_CFG
        CHANNEL_CFG = dict(CHANNEL_CFG["channels"][_my_letter])
        CHANNEL_CFG["channel"] = _my_letter
        CHANNEL_CFG["root"] = _root_cfg.get("root")


def _ch_letter():
    return (CHANNEL_CFG or {}).get("channel", "") or ""


def _ch_name():
    return (CHANNEL_CFG or {}).get("name", "") or "UNKNOWN"


def _logs_dir():
    if CHANNEL_CFG:
        return HERE.parent.parent / "logs"
    return ROOT / "logs"


def _pause_path():
    return _logs_dir() / "paused.json"


def _pause_state():
    pp = _pause_path()
    if not pp.exists():
        return {"paused": False}
    try:
        return json.loads(pp.read_text(encoding="utf-8"))
    except Exception:
        return {"paused": False}


def _svc_state(kind):
    ch = _ch_letter()
    if not ch:
        return {"state": "off", "alive": False, "pid": None}
    sp = _logs_dir() / ("svc_%s_%s.json" % (kind, ch))
    if not sp.exists():
        return {"state": "off", "alive": False, "pid": None}
    try:
        d = json.loads(sp.read_text(encoding="utf-8"))
        pid = d.get("pid")
        alive = False
        if pid:
            try:
                r = subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-Process -Id %d -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id" % int(pid)],
                    capture_output=True, text=True, timeout=5)
                alive = bool(r.stdout.strip())
            except Exception:
                pass
        return {"state": d.get("state", "off"), "pid": pid, "alive": alive}
    except Exception:
        return {"state": "off", "alive": False, "pid": None}


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
                                 "uptime": round(time.time() - START, 1),
                                 "channel": _ch_letter(), "name": _ch_name()})
        if self.path == "/identity":
            cfg = CHANNEL_CFG or {}
            return self._j(200, {"ok": True,
                                 "channel": _ch_letter(),
                                 "name": _ch_name(),
                                 "port": cfg.get("agent_port"),
                                 "cdp": cfg.get("cdp_port"),
                                 "prefix": cfg.get("prefix"),
                                 "model": cfg.get("model"),
                                 "root": str(ROOT),
                                 "version": VERSION})
        if self.path == "/svc_status":
            return self._j(200, {"ok": True,
                                 "watchdog": _svc_state("watchdog"),
                                 "recovery": _svc_state("recovery")})
        if self.path == "/pause_state":
            return self._j(200, {"ok": True, **_pause_state()})
        return self._j(404, {"error": "not found"})

    def do_POST(self):
        if not self._auth():
            return self._j(401, {"error": "unauthorized"})
        try:
            b = self._body()
            op = self.path
            if op == "/pause":
                pp = _pause_path()
                pp.parent.mkdir(parents=True, exist_ok=True)
                paused = bool(b.get("paused", True))
                pp.write_text(json.dumps({"paused": paused, "since": time.time(),
                                          "by": b.get("by", "operator")}, ensure_ascii=False),
                              encoding="utf-8")
                return self._j(200, {"ok": True, "paused": paused})
            if op == "/svc_toggle":
                kind = b.get("kind", "watchdog")
                action = b.get("action", "status")
                ch = _ch_letter()
                if not ch:
                    return self._j(200, {"ok": False, "error": "no channel in config"})
                if kind not in ("watchdog", "recovery"):
                    return self._j(200, {"ok": False, "error": "kind must be watchdog|recovery"})
                svc = str(ROOT / "Tools" / "svc.py")
                if action == "start":
                    args = [sys.executable, svc, "start", "--channel", ch, "--kind", kind]
                    if b.get("interval"): args += ["--interval", str(int(b["interval"]))]
                    if b.get("cooldown"): args += ["--cooldown", str(int(b["cooldown"]))]
                elif action == "stop":
                    args = [sys.executable, svc, "stop", "--channel", ch, "--kind", kind]
                else:
                    args = [sys.executable, svc, "status", "--channel", ch]
                try:
                    rr = subprocess.run(args, capture_output=True, text=True, timeout=20)
                    out = (rr.stdout or "").strip()
                    try:
                        parsed = json.loads(out) if out else {}
                    except Exception:
                        parsed = {"raw": out[:500]}
                    return self._j(200, {"ok": rr.returncode == 0, "result": parsed})
                except Exception as e:
                    return self._j(200, {"ok": False, "error": str(e)})
            if op == "/selftest":
                checks = []
                checks.append({"name": "ping", "ok": True})
                tk_ok = TOKEN_FILE.exists() and len(TOKEN) >= 16
                checks.append({"name": "token", "ok": tk_ok})
                checks.append({"name": "root", "ok": ROOT.exists()})
                checks.append({"name": "config", "ok": CHANNEL_CFG is not None})
                led = _logs_dir() / ("ledger_%s.json" % _ch_letter()) if _ch_letter() else None
                checks.append({"name": "ledger", "ok": bool(led and led.exists())})
                checks.append({"name": "svc_state", "ok": _svc_state("watchdog").get("state") is not None})
                return self._j(200, {"ok": all(c["ok"] for c in checks), "checks": checks,
                                     "channel": _ch_letter(), "name": _ch_name()})
            if op == "/reboot":
                ch = _ch_letter()
                if not ch:
                    return self._j(200, {"ok": False, "error": "no channel"})
                bridge = str(ROOT / "Bridge" / "run.py")
                if not os.path.exists(bridge):
                    return self._j(200, {"ok": False, "error": "Bridge/run.py missing"})
                try:
                    kill = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe' or Name='python.exe'\" | "
                        "Where-Object { $_.CommandLine -like '*Bridge*run.py*--channel*" + ch + "*' } | "
                        "Select-Object -ExpandProperty ProcessId"],
                        capture_output=True, text=True, timeout=10)
                    killed = [int(x) for x in (kill.stdout or "").split() if x.strip().isdigit()]
                    for pid in killed:
                        subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                                       capture_output=True, timeout=5)
                    env = os.environ.copy()
                    env["JEWAI_CONFIG"] = str(ROOT / "config.json")
                    flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0
                    p2 = subprocess.Popen([sys.executable, bridge, "--channel", ch],
                                          cwd=str(ROOT), env=env, creationflags=flags,
                                          stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return self._j(200, {"ok": True, "killed": killed, "spawned": p2.pid})
                except Exception as e:
                    return self._j(200, {"ok": False, "error": str(e)})
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
        sys.exit(1)
    print("[agent] v" + VERSION + " root=" + str(ROOT) + " port=" + str(port))
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()