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
        f"--disable-extensions-except={ext}",
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
        _ext_ok = _wait_extension_target(ch.cdp_port, wait_sec=15.0)
        if _ext_ok:
            for _attempt in range(1, 11):
                storage_ok = _push_storage(cfg, letter, ch)
                if storage_ok:
                    print("[launcher] push_storage OK ch=%s try=%d" % (letter, _attempt), flush=True)
                    break
                time.sleep(1)
            if not storage_ok:
                print("[launcher] push_storage FAILED x10 ch=%s cdp=%d" % (letter, ch.cdp_port), flush=True)
        else:
            print("[launcher] push_storage SKIP ch=%s cdp=%d no_ext_target" % (letter, ch.cdp_port), flush=True)
    return {"ok": ok, "pid": p.pid, "cdp": ch.cdp_port, "first_run": first_run, "storage": storage_ok}


def _push_storage(cfg, letter: str, ch) -> bool:
    """Push agentUrl/token/channel/name into chrome.storage.local via CDP."""
    try:
        import json as _json
        import urllib.request as _ur
        with _ur.urlopen("http://127.0.0.1:%d/json/list" % ch.cdp_port, timeout=5) as r:
            targets = _json.loads(r.read().decode("utf-8"))
        # 7C B-27: collect ALL extension targets (SW may be suspended, sidepanel may not exist yet)
        ext_targets = [t for t in targets if (t.get("url", "") or "").startswith("chrome-extension://")]
        if not ext_targets:
            return False
        # prefer sidepanel > any page > any other
        ext_targets.sort(key=lambda t: (0 if "sidepanel" in t.get("url", "") else
                                        1 if t.get("type") == "page" else 2))
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
        # 7C B-24: set + read back + verify actual values
        expected_keys = ["agentUrl", "token", "channel", "name"]
        expr = (
            "(async () => {"
            "  await chrome.storage.local.set(" + _json.dumps(payload) + ");"
            "  const s = await chrome.storage.local.get(null);"
            "  const want = " + _json.dumps(payload) + ";"
            "  const mism = [];"
            "  for (const k in want) { if (String(s[k] || '') !== String(want[k] || '')) mism.push(k); }"
            "  return {ok: mism.length === 0, mism: mism, got: s};"
            "})()"
        )
        try:
            import websocket
        except Exception:
            return False
        # 7C B-27b: try every extension target until one verifies
        last_err = ""
        for tgt in ext_targets:
            ws_url = tgt.get("webSocketDebuggerUrl")
            if not ws_url:
                continue
            try:
                ws = websocket.create_connection(ws_url, timeout=5)
            except Exception as _e:
                last_err = "ws connect: %s" % _e
                continue
            try:
                cmd = _json.dumps({"id": 1, "method": "Runtime.evaluate",
                                   "params": {"expression": expr, "awaitPromise": True, "returnByValue": True}})
                ws.send(cmd)
                resp = ws.recv()
                try:
                    obj = _json.loads(resp)
                    val = obj.get("result", {}).get("result", {}).get("value") or {}
                    if isinstance(val, dict) and val.get("ok") is True:
                        return True
                    if isinstance(val, dict):
                        last_err = "mismatch: %s" % val.get("mism")
                except Exception as _e:
                    last_err = "parse: %s" % _e
            finally:
                try: ws.close()
                except Exception: pass
        if last_err:
            print("[launcher] push_storage FAILED after %d targets: %s" % (len(ext_targets), last_err), flush=True)
        return False
    except Exception:
        return False


def _wait_extension_target(cdp_port: int, wait_sec: float = 15.0) -> bool:
    import json as _j
    import urllib.request as _u
    t0 = time.time()
    while (time.time() - t0) < wait_sec:
        try:
            with _u.urlopen("http://127.0.0.1:%d/json/list" % cdp_port, timeout=2) as r:
                targets = _j.loads(r.read().decode("utf-8"))
            for x in targets:
                u = x.get("url", "") or ""
                if u.startswith("chrome-extension://"):
                    return True
        except Exception:
            pass
        time.sleep(0.5)
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