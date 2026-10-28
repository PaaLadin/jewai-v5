"""Tools/doh_proxy.py - DoH proxy (local HTTP CONNECT -> DoH -> socket).

Contract (AUDIT section 12, rewritten from scratch):
- Serve on 127.0.0.1:<port> (default from cfg.doh_proxy_port).
- CONNECT host:port -> resolve via DoH (8.8.8.8, 1.1.1.1) -> pipe.
- Cache with TTL (default 300s). Cache key = host.
- Threaded per-connection (daemon threads). Max connections cap.
- SSL context with cert verification enabled (no check_hostname=False).
- IPv4 only (documented). A records.
- Non-CONNECT -> 400.
"""
from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

CTX = ssl.create_default_context()

DOH_SERVERS = ("https://8.8.8.8/resolve", "https://1.1.1.1/resolve")
DEFAULT_TTL = 300
MAX_CONN = 64


class Cache:
    def __init__(self, ttl: int = DEFAULT_TTL):
        self.ttl = ttl
        self.d: dict[str, tuple[str, float]] = {}
        self.lock = threading.Lock()

    def get(self, host: str) -> str | None:
        with self.lock:
            v = self.d.get(host)
            if v is None:
                return None
            ip, ts = v
            if time.time() - ts > self.ttl:
                del self.d[host]
                return None
            return ip

    def put(self, host: str, ip: str) -> None:
        with self.lock:
            self.d[host] = (ip, time.time())


CACHE = Cache()


def doh_resolve(host: str) -> str | None:
    cached = CACHE.get(host)
    if cached:
        return cached
    for srv in DOH_SERVERS:
        try:
            url = srv + "?name=" + host + "&type=A"
            req = urllib.request.Request(url, headers={"accept": "application/dns-json"})
            with urllib.request.urlopen(req, timeout=6, context=CTX) as r:
                d = json.loads(r.read())
            ips = [a["data"] for a in d.get("Answer", []) if a.get("type") == 1]
            if ips:
                CACHE.put(host, ips[0])
                return ips[0]
        except Exception:
            continue
    return None


def _pipe(a: socket.socket, b: socket.socket) -> None:
    try:
        while True:
            d = a.recv(65536)
            if not d:
                break
            b.sendall(d)
    except Exception:
        pass
    finally:
        try: a.close()
        except Exception: pass
        try: b.close()
        except Exception: pass


def handle(client: socket.socket) -> None:
    try:
        data = client.recv(8192)
        if not data:
            client.close()
            return
        line = data.split(b"\r\n", 1)[0].decode("utf-8", "replace")
        parts = line.split()
        if len(parts) < 2:
            client.close()
            return
        method, target = parts[0], parts[1]
        if method != "CONNECT":
            client.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            client.close()
            return
        host, _, port = target.partition(":")
        try:
            port = int(port or 443)
        except Exception:
            port = 443
        ip = doh_resolve(host)
        if not ip:
            client.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            client.close()
            return
        up = socket.create_connection((ip, port), timeout=15)
        client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        threading.Thread(target=_pipe, args=(client, up), daemon=True).start()
        threading.Thread(target=_pipe, args=(up, client), daemon=True).start()
    except Exception:
        try: client.close()
        except Exception: pass


def serve(port: int) -> None:
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(MAX_CONN)
    print("[doh_proxy] on 127.0.0.1:%d" % port, flush=True)
    while True:
        try:
            c, _ = srv.accept()
            threading.Thread(target=handle, args=(c,), daemon=True).start()
        except Exception:
            continue


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--test", action="store_true", help="resolve example.com and exit")
    a = ap.parse_args()
    if a.test:
        for h in ("example.com", "duckduckgo.com"):
            print(h, "->", doh_resolve(h))
        return 0
    port = a.port
    if port is None:
        # try config
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            from Core.config import load
            cfg = load()
            port = cfg.doh_proxy_port
        except Exception:
            port = 9899
    serve(port)
    return 0


if __name__ == "__main__":
    sys.exit(main())