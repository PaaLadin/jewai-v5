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
        time.sleep(1.0)
    print("[launcher] Ext target NOT found after %.1fs" % (time.time()-t0), flush=True)
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
        "--disable-features=DisableLoadExtensionCommandLineSwitch,RestoreSessionOnStartup",
        "--enable-features=AllowLegacyExtensionFlags",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-background-timer-throttling",
        "--no-first-run",
        "--no-default-browser-check",
        # 8C B-33b: removed --restore-last-session (Chrome ignores URL arg when restoring)
        "--hide-crash-restore-bubble",
    ]
    if not no_proxy:
        args.append(f"--proxy-server=127.0.0.1:{cfg.doh_proxy_port}")
    # 7C B-33: open onboarding when flag not set, REGARDLESS of first_run.
    # (Previous version opened onboarding only on empty profile; existing profiles -> chat)
    _onb_flag = profile.parent / "logs" / "onboarding_disabled.flag"
    _want_onboarding = (not _onb_flag.exists())
    _onb_url = "http://127.0.0.1:%d/onboarding" % ch.agent_port
    # 8C B-07/B-08/B-33: onboarding via CDP after wait_cdp (args URL ignored on restore)
    if (not _want_onboarding) and first_run:
        args.append(start_url)

    if dry:
        return {"ok": True, "dry": True, "args": args, "first_run": first_run}

    # 8C B-33c: if onboarding wanted, prepare clean-start state:
    # (a) delete Sessions/* and Tabs_* so Chrome cannot crash-restore old tabs
    # (b) set profile.exit_type=Normal so crash-bubble is not triggered
    if _want_onboarding:
        try:
            sess_dir = profile / "Default" / "Sessions"
            if sess_dir.is_dir():
                for f in sess_dir.iterdir():
                    try:
                        if f.is_file() and (f.name.startswith("Session_") or f.name.startswith("Tabs_")):
                            f.unlink()
                    except Exception:
                        pass
            pref_path = profile / "Default" / "Preferences"
            if pref_path.is_file():
                import json as _jp
                try:
                    pdata = _jp.loads(pref_path.read_text(encoding="utf-8"))
                    pdata.setdefault("profile", {})["exit_type"] = "Normal"
                    pdata["profile"]["exited_cleanly"] = True
                    tmp = pref_path.with_suffix(".tmp")
                    tmp.write_text(_jp.dumps(pdata), encoding="utf-8")
                    tmp.replace(pref_path)
                except Exception:
                    pass
        except Exception:
            pass
    # 8C B-44: warn when chrome_path is not CfT — system Chrome 137+ ignores --load-extension
    try:
        _chrome_str = str(chrome).lower().replace("\\", "/")
        _is_cft = "chrome-for-testing" in _chrome_str
        if not _is_cft:
            print("[launcher] WARN (B-44): chrome_path is NOT Chrome for Testing: %s" % chrome, flush=True)
            print("[launcher] WARN (B-44): Chrome 137+ ignores --load-extension for unpacked ext.\n                Extension may not load; sidepanel/onboarding will not appear.\n                Fix: install CfT (Tools/chrome-for-testing) or point config.chrome_path to it.", flush=True)
    except Exception:
        pass
    nw = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    p = subprocess.Popen(
        args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=nw | (subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0),
    )
    ok = wait_cdp(ch.cdp_port, wait_sec=20.0)
    # 8C B-07/B-08/B-33: open onboarding via CDP
    if ok and _want_onboarding:
        _onb_ok = _force_onboarding_tab(ch.cdp_port, _onb_url, timeout=10)
        print("[launcher] force_onboarding ch=%s ok=%s" % (letter, _onb_ok), flush=True)
        # 8C B-33b: bring Chrome window to foreground (AppActivate)
        try:
            import time as _t2
            _t2.sleep(0.4)
            _ps = ("$w = New-Object -ComObject WScript.Shell; "
                   "1..5 | ForEach-Object { $null = $w.AppActivate(" + str(p.pid) + "); Start-Sleep -Milliseconds 200 }")
            subprocess.run(["powershell", "-NoProfile", "-Command", _ps],
                           capture_output=True, timeout=8,
                           creationflags=(subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0))
        except Exception:
            pass
    storage_ok = False
    if ok:
        _ext_ok = _wait_extension_target(ch.cdp_port, wait_sec=45.0, ext_path=ext)
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


def _force_onboarding_tab(cdp_port: int, onb_url: str, timeout: float = 10.0) -> bool:
    """8C B-07/B-08/B-33b: create onboarding tab, activate, close other page tabs."""
    import json as _j
    import urllib.request as _u
    import urllib.parse as _up
    import time as _t
    t0 = _t.time()
    q = _up.quote(onb_url, safe="")
    nid = None
    while (_t.time() - t0) < timeout:
        try:
            req = _u.Request("http://127.0.0.1:%d/json/new?%s" % (cdp_port, q), method="PUT")
            with _u.urlopen(req, timeout=5) as r:
                obj = _j.loads(r.read().decode("utf-8"))
                nid = obj.get("id")
                if nid:
                    break
        except Exception:
            pass
        _t.sleep(0.5)
    if not nid:
        return False
    _t.sleep(0.6)
    # 8C B-33b: close other page tabs so onboarding is the only visible tab
    try:
        import websocket as _ws
        with _u.urlopen("http://127.0.0.1:%d/json/list" % cdp_port, timeout=3) as r:
            targets = _j.loads(r.read().decode("utf-8"))
        other_ids = [t.get("id") for t in targets
                     if t.get("type") == "page" and t.get("id") and t.get("id") != nid]
        if other_ids:
            with _u.urlopen("http://127.0.0.1:%d/json/version" % cdp_port, timeout=3) as r:
                ver = _j.loads(r.read().decode("utf-8"))
            bws = ver.get("webSocketDebuggerUrl")
            if bws:
                w = _ws.create_connection(bws, timeout=5)
                for _i, _oid in enumerate(other_ids, start=1):
                    try:
                        w.send(_j.dumps({"id": _i, "method": "Target.closeTarget",
                                         "params": {"targetId": _oid}}))
                        _t.sleep(0.1)
                    except Exception:
                        pass
                try:
                    w.send(_j.dumps({"id": 999, "method": "Target.activateTarget",
                                     "params": {"targetId": nid}}))
                    _t.sleep(0.3)
                except Exception:
                    pass
                try: w.close()
                except Exception: pass
    except Exception:
        pass
    try:
        _u.urlopen("http://127.0.0.1:%d/json/activate/%s" % (cdp_port, nid), timeout=3).read()
    except Exception:
        pass
    return True


def _push_storage(cfg, letter: str, ch) -> bool:
    """Push agentUrl/token/channel/name into chrome.storage.local via CDP."""
    try:
        import json as _json
        import urllib.request as _ur
        with _ur.urlopen("http://127.0.0.1:%d/json/list" % ch.cdp_port, timeout=5) as r:
            targets = _json.loads(r.read().decode("utf-8"))
        ext_targets = [t for t in targets if (t.get("url", "") or "").startswith("chrome-extension://")]
        if not ext_targets: return False
        
        ext_targets.sort(key=lambda t: (0 if "sidepanel" in t.get("url", "") else 1 if t.get("type") == "page" else 2))
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
        expr = (
            "(async () => {"
            "  try {"
            "    if (typeof chrome === 'undefined') return 'ERROR: chrome undefined';"
            "    if (typeof chrome.storage === 'undefined') return 'ERROR: chrome.storage undefined. chrome keys: ' + Object.keys(chrome).join(',');"
            "    await chrome.storage.local.set(" + _json.dumps(payload) + ");"
            "    const s = await chrome.storage.local.get(null);"
            "    const want = " + _json.dumps(payload) + ";"
            "    const mism = [];"
            "    for (const k in want) { if (String(s[k] || '') !== String(want[k] || '')) mism.push(k); }"
            "    return mism.length === 0 ? 'OK' : 'MISMATCH:' + mism.join(',');"
            "  } catch(e) { return 'ERROR:' + e.message; }"
            "})()"
        )
        
        last_err = "no targets"
        for tgt in ext_targets:
            ws_url = tgt.get("webSocketDebuggerUrl")
            if not ws_url: continue
            try:
                import websocket
                ws = websocket.create_connection(ws_url, timeout=5)
                # wait a bit for JS context to be ready
                time.sleep(1.0)
                ws.send(_json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": expr, "awaitPromise": True, "returnByValue": True}}))
                resp_str = ws.recv()
                ws.close()
                resp = _json.loads(resp_str)
                
                if "exceptionDetails" in resp.get("result", {}):
                    last_err = "Exception: " + str(resp["result"]["exceptionDetails"])
                    continue
                    
                val = resp.get("result", {}).get("result", {}).get("value")
                if val == "OK":
                    return True
                else:
                    last_err = str(val)
            except Exception as _e:
                last_err = "ws error: %s" % _e
                
        print("[launcher] push_storage FAILED after %d targets: %s" % (len(ext_targets), last_err), flush=True)
        return False
    except Exception as e:
        print("[launcher] push_storage outer error: %s" % e, flush=True)
        return False



def _ext_id_from_path(path: str) -> str:
    import hashlib
    norm = str(path).replace("/", "\\").lower()
    h = hashlib.sha256(norm.encode("utf-8")).hexdigest()[:32]
    return "".join(chr(ord("a") + int(c, 16)) for c in h)


def _get_loaded_ext_id(cdp_port: int) -> str:
    """Open chrome://extensions via CDP, parse the shadow DOM, return the first extension ID."""
    try:
        import json as _json
        import urllib.request as _ur
        import urllib.parse as _up
        import websocket
        
        # 1. Create a new tab for chrome://extensions
        url = "chrome://extensions"
        req = _ur.Request("http://127.0.0.1:%d/json/new?%s" % (cdp_port, _up.quote(url)), method="PUT")
        tab = _json.loads(_ur.urlopen(req, timeout=5).read())
        
        import time as _t
        _t.sleep(1.5)  # wait for render
        
        # 2. Connect via WS and extract IDs from shadow DOM
        ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=5)
        expr = """
        (() => {
            const mgr = document.querySelector('extensions-manager');
            if (!mgr) return 'NO_MGR';
            const list = mgr.shadowRoot.querySelector('extensions-item-list');
            if (!list) return 'NO_LIST';
            const items = list.shadowRoot.querySelectorAll('extensions-item');
            return Array.from(items).map(i => i.id).join(',');
        })()
        """
        ws.send(_json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": expr, "returnByValue": True}}))
        resp = _json.loads(ws.recv())
        ws.close()
        
        ids_str = resp.get("result", {}).get("result", {}).get("value", "")
        
        # Close the tab
        _ur.urlopen("http://127.0.0.1:%d/json/close/%s" % (cdp_port, tab["id"]), timeout=3)
        
        if not ids_str or ids_str in ("NO_MGR", "NO_LIST"):
            return ""
        return ids_str.split(",")[0].strip()
    except Exception as e:
        print("[launcher] _get_loaded_ext_id failed: %s" % e, flush=True)
        return ""


def _open_ext_sidepanel(cdp_port: int, ext_path: str) -> bool:
    try:
        import urllib.request as _u
        import urllib.parse as _up
        eid = _get_loaded_ext_id(cdp_port)
        if not eid:
            print("[launcher] _open_ext_sidepanel: could not detect ext ID", flush=True)
            return False
        url = "chrome-extension://%s/sidepanel.html" % eid
        req = _u.Request("http://127.0.0.1:%d/json/new?%s" % (cdp_port, _up.quote(url)), method="PUT")
        _u.urlopen(req, timeout=5).read()
        print("[launcher] forced ext sidepanel open: %s" % eid, flush=True)
        return True
    except Exception as e:
        print("[launcher] force sidepanel failed: %s" % e, flush=True)
        return False


def _wait_extension_target(cdp_port: int, wait_sec: float = 45.0, ext_path: str = "") -> bool:
    import json as _j
    import urllib.request as _u
    t0 = time.time()
    forced = False
    while (time.time() - t0) < wait_sec:
        try:
            with _u.urlopen("http://127.0.0.1:%d/json/list" % cdp_port, timeout=2) as r:
                targets = _j.loads(r.read().decode("utf-8"))
            for x in targets:
                u = x.get("url", "") or ""
                if u.startswith("chrome-extension://"):
                    print("[launcher] Ext target found after %.1fs" % (time.time()-t0), flush=True)
                    return True
        except Exception:
            pass
        if not forced and ext_path and (time.time() - t0) > 5.0:
            _open_ext_sidepanel(cdp_port, ext_path)
            forced = True
        time.sleep(1.0)
    print("[launcher] Ext target NOT found after %.1fs" % (time.time()-t0), flush=True)
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