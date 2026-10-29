"""launchpad.py - blocks: status, boot, stop, restart.

Contract (AUDIT §28.4, rewritten):
- blocks: server (self), agent:<CH>, chrome:<CH>, doh, mailbot, rebirth.
- boot(target): spawn with tracked registry (logs/runtime/spawned.json).
- stop(target): kill ONLY spawned-by-us pids. Never by cmdline matching.
- server: self, cannot boot/stop/restart.
- doh/mailbot/rebirth: not v5 modules -> immediate refusal.
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

from Core.config import Config


def _sp_path(cfg: Config) -> Path:
    p = cfg.path("logs", "runtime", "spawned.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _sp_load(cfg: Config) -> dict:
    p = _sp_path(cfg)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _sp_save(cfg: Config, d: dict) -> None:
    _sp_path(cfg).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def _tcp(port: int, timeout: float = 0.4) -> bool:
    s = socket.socket()
    s.settimeout(timeout)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def _cdp_up(port: int, timeout: float = 0.7) -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % port, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def _pid_alive(pid: int) -> bool:
    if not pid:
        return False
    try:
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, int(pid))
        if not h:
            return False
        try:
            code = ctypes.c_ulong()
            ok = k.GetExitCodeProcess(h, ctypes.byref(code))
            return bool(ok) and code.value == 259
        finally:
            k.CloseHandle(h)
    except Exception:
        return False


def _nw() -> int:
    if sys.platform != "win32":
        return 0
    return subprocess.CREATE_NO_WINDOW


def _detach() -> int:
    if sys.platform != "win32":
        return 0
    return subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP


def _pythonw() -> str:
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        c = exe[:-len("python.exe")] + "pythonw.exe"
        if Path(c).exists():
            return c
    return exe


def _spawn(cfg: Config, args: list[str], cwd: Path, key: str) -> dict:
    try:
        p = subprocess.Popen(args, cwd=str(cwd),
                             stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=_detach())
        d = _sp_load(cfg)
        d[key] = {"pid": p.pid, "started": time.time()}
        _sp_save(cfg, d)
        return {"ok": True, "pid": p.pid, "key": key}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__ + ": " + str(e)[:200]}


def _kill(cfg: Config, key: str) -> dict:
    d = _sp_load(cfg)
    info = d.pop(key, None)
    _sp_save(cfg, d)
    if not info:
        return {"ok": True, "stopped": None, "note": "not in registry"}
    pid = info.get("pid")
    if not pid:
        return {"ok": True, "stopped": None, "note": "no pid"}
    if not _pid_alive(pid):
        return {"ok": True, "stopped": pid, "note": "already dead"}
    try:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                       capture_output=True, timeout=10,
                       creationflags=_nw())
        return {"ok": True, "stopped": pid}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}


def _block(cfg: Config, key: str) -> dict:
    if key == "server":
        return {"on": True, "self": True, "port": cfg.chat_port}
    if key.startswith("agent:"):
        L = key.split(":", 1)[1]
        ch = cfg.channels.get(L)
        if not ch:
            return {"on": False, "error": "bad channel"}
        alive = _tcp(ch.agent_port)
        return {"on": alive, "port": ch.agent_port}
    if key.startswith("chrome:"):
        L = key.split(":", 1)[1]
        ch = cfg.channels.get(L)
        if not ch:
            return {"on": False, "error": "bad channel"}
        return {"on": _tcp(ch.cdp_port), "port": ch.cdp_port, "cdp_ok": _cdp_up(ch.cdp_port)}
    if key == "doh":
        return {"on": _tcp(cfg.doh_proxy_port), "port": cfg.doh_proxy_port}
    if key in ("mailbot", "rebirth"):
        info = _sp_load(cfg).get(key) or {}
        pid = info.get("pid")
        return {"on": _pid_alive(pid) if pid else False, "pid": pid, "byfile": True}
    return {"on": False, "error": "unknown block"}


def status(cfg: Config) -> dict:
    from concurrent.futures import ThreadPoolExecutor
    keys = ["server"] + ["agent:" + L for L in cfg.channels] + ["chrome:" + L for L in cfg.channels] + ["doh", "mailbot", "rebirth"]
    blocks: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        futs = {k: ex.submit(_block, cfg, k) for k in keys}
        for k, f in futs.items():
            try:
                blocks[k] = f.result(timeout=6)
            except Exception:
                blocks[k] = {"on": False, "error": "timeout"}
    return {"ok": True, "ts": time.time(), "blocks": blocks}


def boot(cfg: Config, target: str) -> dict:
    if target == "server":
        return {"ok": False, "error": "self, cannot boot"}
    if target == "all":
        out = []
        for t in ["agent:" + L for L in cfg.channels] + ["chrome:" + L for L in cfg.channels]:
            out.append({"target": t, "result": boot(cfg, t)})
        return {"ok": True, "target": "all", "results": out}
    if target.startswith("agent:"):
        L = target.split(":", 1)[1]
        ch = cfg.channels.get(L)
        if not ch:
            return {"ok": False, "error": "bad channel"}
        if _tcp(ch.agent_port):
            return {"ok": True, "target": target, "already": True}
        # 11B: prefer per-channel extension; fallback to Templates
        script = cfg.channel_path(L, "extension", "agent.py")
        if not script.exists():
            script = cfg.path("Templates", "extension", "agent.py")
        if not script.exists():
            return {"ok": False, "error": "agent.py not found", "path": str(script)}
        # cwd = Profiles/<L>/extension (per-agent layout); Agents/ no longer used
        ext_dir = cfg.channel_path(L, "extension")
        ext_dir.mkdir(parents=True, exist_ok=True)
        return _spawn(cfg, [_pythonw(), str(script), str(ch.agent_port)], ext_dir, target)
    if target.startswith("chrome:"):
        L = target.split(":", 1)[1]
        if L not in cfg.channels:
            return {"ok": False, "error": "bad channel"}
        if _tcp(cfg.channels[L].cdp_port):
            return {"ok": True, "target": target, "already": True}
        try:
            from Tools.launcher import launch
            r = launch(cfg, L, no_proxy=True, dry=False)
            return {"ok": bool(r.get("ok")), "target": target, "pid": r.get("pid")}
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}
    if target == "doh":
        return {"ok": False, "error": "doh not implemented in v5 (Ф5)"}
    if target in ("mailbot", "rebirth"):
        return {"ok": False, "error": target + " not in v5"}
    return {"ok": False, "error": "unknown target", "target": target}


def stop(cfg: Config, target: str) -> dict:
    if target == "server":
        return {"ok": False, "error": "self, cannot stop"}
    if target == "all":
        out = []
        for t in ["chrome:" + L for L in cfg.channels] + ["agent:" + L for L in cfg.channels]:
            out.append({"target": t, "result": stop(cfg, t)})
        return {"ok": True, "target": "all", "results": out}
    if target.startswith(("agent:", "chrome:", "doh", "mailbot", "rebirth")):
        return _kill(cfg, target)
    return {"ok": False, "error": "unknown target", "target": target}


def restart(cfg: Config, target: str) -> dict:
    if target == "server":
        return {"ok": False, "error": "self, restart not allowed"}
    stop(cfg, target)
    time.sleep(1.0)
    return boot(cfg, target)