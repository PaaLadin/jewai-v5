"""Tools/launcher.py — запуск Chrome для канала.

Контракт (по AUDIT §13):
- CLI: --channel <CH> [--no-proxy] [--dry-run] [--first-run-url URL]
- Профиль: <root>/Profiles/<CH>, создаётся если нет.
- CDP-порт из config.channels.<CH>.cdp.
- Флаги Chrome: user-data-dir, remote-debugging-port, load-extension, proxy-server,
  disable-backgrounding-occluded-windows, disable-renderer-backgrounding,
  disable-background-timer-throttling, no-first-run, no-default-browser-check,
  restore-last-session, hide-crash-restore-bubble.
- При первом запуске (нет Default/Preferences) — открыть стартовый URL.
- Ждёт /json/version с таймаутом (poll, не фиксированный sleep).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from Core.config import load as load_config

DEFAULT_START_URL = {
    "deepseek": "https://chat.deepseek.com/",
    "qwen": "https://chat.qwen.ai/",
    "alice": "https://alice.yandex.ru/",
}


def _chrome_exe(cfg=None) -> Path:
    # 11B: priority
    # 1) config.chrome_path override (for tests / custom installs)
    # 2) Chrome for Testing in <root>/tools/chrome-for-testing/chrome.exe
    # 3) regular Chrome in standard locations
    if cfg is not None:
        try:
            override = getattr(cfg, "chrome_path", None) or None
            if not override:
                # config.json may have it as plain key
                import json as _j
                raw = _j.loads((cfg.root / "config.json").read_text(encoding="utf-8"))
                override = raw.get("chrome_path")
            if override:
                p = Path(override)
                if p.exists():
                    return p
        except Exception:
            pass
        try:
            cft = cfg.path("tools", "chrome-for-testing", "chrome.exe")
            if cft.exists():
                return cft
        except Exception:
            pass
    cands = [
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
    ]
    for c in cands:
        if c.exists():
            return c
    raise FileNotFoundError("chrome.exe not found (config.chrome_path, tools/chrome-for-testing/chrome.exe, standard locations all missing)")


def _cdp_up(port: int, timeout: float = 0.7) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def wait_cdp(port: int, wait_sec: float = 15.0) -> bool:
    t0 = time.time()
    while time.time() - t0 < wait_sec:
        if _cdp_up(port):
            return True
        time.sleep(0.5)
    return False


def launch(cfg, letter: str, no_proxy: bool = False, dry: bool = False) -> dict:
    ch = cfg.channel(letter)
    chrome = _chrome_exe(cfg)
    # 11B: per-agent chrome dir under Profiles/<L>/chrome
    profile = cfg.channel_path(letter, "chrome")
    profile.mkdir(parents=True, exist_ok=True)
    ext = cfg.path(ch.extension)
    start_url = DEFAULT_START_URL.get(ch.model, "https://chat.deepseek.com/")

    first_run = not (profile / "Default" / "Preferences").exists()

    args = [
        str(chrome),
        f"--user-data-dir={profile}",
        f"--remote-debugging-port={ch.cdp_port}",
        f"--load-extension={ext}",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-background-timer-throttling",
        "--no-first-run",
        "--no-default-browser-check",
        "--restore-last-session",
        "--hide-crash-restore-bubble",
    ]
    if not no_proxy:
        args.append(f"--proxy-server=127.0.0.1:{cfg.doh_proxy_port}")
    if first_run:
        args.append(start_url)

    if dry:
        return {"ok": True, "dry": True, "args": args, "first_run": first_run}

    nw = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    p = subprocess.Popen(
        args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=nw | (subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0),
    )
    ok = wait_cdp(ch.cdp_port, wait_sec=20.0)
    storage_ok = False
    if ok:
        storage_ok = _push_storage(cfg, letter, ch)
    return {"ok": ok, "pid": p.pid, "cdp": ch.cdp_port, "first_run": first_run, "storage": storage_ok}


def _push_storage(cfg, letter: str, ch) -> bool:
    """Push agentUrl/token/channel/name into chrome.storage.local via CDP."""
    try:
        import json as _json
        import urllib.request as _ur
        with _ur.urlopen("http://127.0.0.1:%d/json/list" % ch.cdp_port, timeout=5) as r:
            targets = _json.loads(r.read().decode("utf-8"))
        ext_target = None
        for t in targets:
            u = t.get("url", "")
            if u.startswith("chrome-extension://") and "sidepanel" in u:
                ext_target = t; break
        if not ext_target:
            for t in targets:
                if t.get("url", "").startswith("chrome-extension://"):
                    ext_target = t; break
        if not ext_target:
            return False
        token = ""
        tok_path = cfg.path(".agent_token")
        if tok_path.exists():
            token = tok_path.read_text(encoding="utf-8").strip()
        payload = {
            "agentUrl": "http://127.0.0.1:%d" % ch.agent_port,
            "token": token,
            "channel": letter,
            "name": ch.name,
        }
        expr = ("chrome.storage.local.set(%s).then(() => 'ok').catch(e => 'err:' + e)"
                % _json.dumps(payload))
        try:
            import websocket
        except Exception:
            return False
        ws = websocket.create_connection(ext_target["webSocketDebuggerUrl"], timeout=5)
        try:
            cmd = _json.dumps({"id": 1, "method": "Runtime.evaluate",
                               "params": {"expression": expr, "awaitPromise": True, "returnByValue": True}})
            ws.send(cmd)
            resp = ws.recv()
            return '"result"' in resp
        finally:
            ws.close()
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True, choices=["A", "B", "C", "D", "E", "F"])
    ap.add_argument("--no-proxy", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--config", default=None)
    a = ap.parse_args()
    cfg = load_config(a.config)
    r = launch(cfg, a.channel, no_proxy=a.no_proxy, dry=a.dry_run)
    print(r)
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())