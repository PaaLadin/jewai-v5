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







def inject_tabs(html: str, static_dir: Path) -> str:
    tabs_dir = static_dir / "tabs"
    if tabs_dir.exists():
        for tab_file in tabs_dir.glob("*.html"):
            tab_id = tab_file.stem
            content = tab_file.read_text(encoding="utf-8")
            start_str = f'id="tab-{tab_id}"'
            if start_str in html:
                start_idx = html.find(start_str)
                section_start = html.rfind('<section', 0, start_idx)
                section_end = html.find('</section>', start_idx) + len('</section>')
                if section_start != -1 and section_end != -1:
                    old_section = html[section_start:section_end]
                    new_section = old_section.replace('</section>', content + '</section>')
                    html = html.replace(old_section, new_section)
    return html

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
            self._cors()
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            pass

    def _send_json(self, code: int, obj: Any) -> None:
        self._send(code, _json_bytes(obj))

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Token")
        self.send_header("Access-Control-Max-Age", "600")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

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
                html = f.read_text(encoding="utf-8")
                html = inject_tabs(html, static_dir)
                return self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
            return self._send(404, b"index.html missing", "text/plain")
        # Static assets: any file in Mainframe/static/ with known extension
        import os as _os
        STATIC_EXTS = (".css", ".js", ".html", ".png", ".jpg", ".svg", ".ico", ".woff", ".woff2", ".ttf")
        STATIC_CT = {
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".html": "text/html; charset=utf-8",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".woff": "font/woff",
            ".woff2": "font/woff2",
            ".ttf": "font/ttf",
        }
        if path.startswith("/") and any(path.endswith(ext) for ext in STATIC_EXTS):
            # защита от escape
            safe = path.lstrip("/").replace("..", "")
            f = static_dir / safe
            if f.exists() and f.is_file():
                ct = STATIC_CT.get(_os.path.splitext(safe)[1].lower(), "application/octet-stream")
                return self._send(200, f.read_bytes(), ct)
            return self._send(404, b"missing", "text/plain")
        # 7C B-12: wiki page (how-to for beginners)
        if path == "/api/wiki":
            f = static_dir / "wiki_data.json"
            if f.exists():
                body = f.read_text(encoding="utf-8").encode("utf-8")
                return self._send(200, body, "application/json; charset=utf-8")
            return self._send(404, b"wiki_data.json missing", "text/plain")
        if path in ("/wiki", "/wiki.html", "/help", "/howto"):
            f = static_dir / "wiki.html"
            if f.exists():
                return self._send(200, f.read_bytes(), "text/html; charset=utf-8")
            return self._send(404, b"wiki.html missing", "text/plain")
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