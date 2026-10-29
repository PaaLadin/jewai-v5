"""Mainframe/http.py - HTTP server + routing for v5 panel (port 8670).

Contract:
- ThreadingHTTPServer on cfg.bind:cfg.chat_port.
- Routes (static first, then api):
  GET  /                    -> static index.html
  GET  /style.css, /app.js  -> static files
  GET  /api/status          -> collect_status()
  GET  /api/projects        -> scan_projects()
  GET  /api/health          -> simple health {ok, ts}
  GET  /api/chat_url/<CH>   -> per-channel chat url from config/session
  POST /api/boot, /api/stop, /api/restart -> launchpad (later)
- No auth in v5 alpha (loopback only). X-Token added in Ф5.
"""
from __future__ import annotations

import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from Core.config import Config


def _json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    # injected by make_server
    cfg: Config = None  # type: ignore
    routes: dict = None  # type: ignore

    def log_message(self, fmt: str, *args: Any) -> None:
        # quiet
        pass

    def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8") -> None:
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            pass

    def _send_json(self, code: int, obj: Any) -> None:
        self._send(code, _json_bytes(obj))

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        # /roadmap/<name> raw file serving from Projects/<name>/ROADMAP.{html,md}
        if path.startswith("/roadmap/"):
            import pathlib as _pl
            name = path.split("/roadmap/", 1)[1].strip("/")
            if "/" in name or name.startswith(".."):
                return self._send(403, b"forbidden", "text/plain")
            for base_rel in ("Projects", "project"):
                base = self.cfg.path(base_rel)
                if not base.exists():
                    continue
                for fn, ctype in (("ROADMAP.html", "text/html; charset=utf-8"),
                                   ("ROADMAP.md", "text/markdown; charset=utf-8")):
                    f = base / name / fn
                    if f.exists():
                        return self._send(200, f.read_bytes(), ctype)
            return self._send(404, b"roadmap not found", "text/plain")
        # /fs/ raw file serving (non-JSON, delegates to controls.fs_read)
        if path.startswith("/fs/"):
            try:
                from Mainframe import controls
                code, body, ctype = controls.fs_read(self.cfg, path)
                return self._send(code, body, ctype)
            except Exception as e:
                return self._send(500, b"fs error", "text/plain")
        # static first
        static_dir = self.cfg.path("Mainframe", "static")
        if path in ("/", "/index.html"):
            f = static_dir / "index.html"
            if f.exists():
                return self._send(200, f.read_bytes(), "text/html; charset=utf-8")
            return self._send(404, b"index.html missing", "text/plain")
        if path in ("/style.css", "/app.js"):
            f = static_dir / path.lstrip("/")
            if f.exists():
                ct = "text/css; charset=utf-8" if path.endswith(".css") else "application/javascript; charset=utf-8"
                return self._send(200, f.read_bytes(), ct)
            return self._send(404, b"missing", "text/plain")
        # api
        fn = self.routes.get(("GET", path))
        if fn is not None:
            try:
                obj = fn(self.cfg, path, {})
                return self._send_json(200, obj)
            except Exception as e:
                return self._send_json(500, {"ok": False, "error": type(e).__name__ + ": " + str(e)})
        # prefix routes (chat_url/<CH>)
        for (method, prefix), fn in self.routes.items():
            if method == "GET" and prefix.endswith("/") and path.startswith(prefix):
                try:
                    obj = fn(self.cfg, path, {})
                    return self._send_json(200, obj)
                except Exception as e:
                    return self._send_json(500, {"ok": False, "error": type(e).__name__ + ": " + str(e)})
        return self._send_json(404, {"ok": False, "error": "not found", "path": path})

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            body = {}
        fn = self.routes.get(("POST", path))
        if fn is None:
            for (method, prefix), pf in self.routes.items():
                if method == "POST" and prefix.endswith("/") and path.startswith(prefix):
                    fn = pf
                    break
        if fn is None:
            return self._send_json(404, {"ok": False, "error": "not found", "path": path})
        try:
            obj = fn(self.cfg, path, body)
            return self._send_json(200, obj)
        except Exception as e:
            return self._send_json(500, {"ok": False, "error": type(e).__name__ + ": " + str(e)})


def make_server(cfg: Config, routes: dict) -> ThreadingHTTPServer:
    handler = type("BoundHandler", (Handler,), {"cfg": cfg, "routes": routes})
    return ThreadingHTTPServer((cfg.bind, cfg.chat_port), handler)


def run(cfg: Config, routes: dict) -> None:
    httpd = make_server(cfg, routes)
    print("Mainframe on http://%s:%d" % (cfg.bind, cfg.chat_port), flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass