import http.server, json, os, shutil, secrets, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PORT = 8660  # 11B: 8671 = agent E in v5

def _kill_chrome_for_target(target, log):
    """7C B-19/B-28: stop Chrome whose cmdline is under target OR ROOT (source CfT lock)."""
    import subprocess as _sp
    try:
        target_norm = os.path.abspath(target).lower().replace("\\", "/")
        root_norm = os.path.abspath(ROOT).lower().replace("\\", "/")
        cft_root = (root_norm + "/tools/chrome-for-testing/")
        ps = (
            "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
            "Where-Object { "
            "  ($_.CommandLine -and ( $_.CommandLine.ToLower().Replace('\\','/').Contains('"
            + target_norm.replace("'", "") + "') -or $_.CommandLine.ToLower().Replace('\\','/').Contains('"
            + root_norm.replace("'", "") + "') ) ) -or "
            "  ($_.ExecutablePath -and $_.ExecutablePath.ToLower().Replace('\\','/').StartsWith('"
            + cft_root.replace("'", "") + "')) "
            "} | Select-Object -ExpandProperty ProcessId"
        )
        r = _sp.run(["powershell", "-NoProfile", "-Command", ps],
                    capture_output=True, text=True, timeout=15)
        killed = []
        for line in (r.stdout or "").splitlines():
            line = line.strip()
            if line.isdigit():
                pid = int(line)
                _sp.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, timeout=5)
                killed.append(pid)
        if killed:
            log("B-19/B-28: killed Chrome pids %s (target+ROOT)" % killed)
    except Exception as _e:
        try:
            log("kill-chrome failed: %s" % _e)
        except Exception:
            pass


def _kill_python_for_target(target, log):
    """7C B-23: kill stale agent.py/Bridge/svc/doh processes from previous run of target.
    Also stale Mainframe (will be restarted by run_launch). Skips installer itself."""
    import subprocess as _sp
    try:
        target_norm = os.path.abspath(target).lower().replace("\\", "/")
        my_pid = os.getpid()
        ps = (
            "Get-CimInstance Win32_Process -Filter \"Name='python.exe' or Name='pythonw.exe'\" | "
            "Select-Object ProcessId, CommandLine | ConvertTo-Json -Compress"
        )
        r = _sp.run(["powershell", "-NoProfile", "-Command", ps],
                    capture_output=True, text=True, timeout=20)
        raw = (r.stdout or "").strip()
        if not raw:
            return
        import json as _json
        try:
            items = _json.loads(raw)
        except Exception:
            return
        if isinstance(items, dict):
            items = [items]
        killed = []
        for it in items:
            try:
                pid = int(it.get("ProcessId"))
            except Exception:
                continue
            if pid == my_pid:
                continue
            cmd = (it.get("CommandLine") or "").lower().replace("\\", "/")
            if target_norm not in cmd:
                continue
            # match known components (avoid killing random)
            if not any(k in cmd for k in ["agent.py", "bridge/run.py", "bridge\\run.py",
                                          "tools/svc.py", "tools\\svc.py",
                                          "doh_proxy.py", "mainframe/server.py", "mainframe\\server.py"]):
                continue
            try:
                _sp.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, timeout=5)
                killed.append(pid)
            except Exception:
                pass
        if killed:
            log("B-23: killed stale python pids %s for target %s" % (killed, target_norm))
    except Exception as _e:
        try:
            log("B-23 kill-python failed: %s" % _e)
        except Exception:
            pass


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HERE, **kwargs)
    def log_message(self, format, *args):
        pass
    def do_POST(self):
        if self.path == '/shutdown':
            # 7C B-03: explicit shutdown (user clicks Close on failure page)
            try:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"ok": true, "shutdown": true}')
                self.wfile.flush()
            except Exception:
                pass
            import threading
            threading.Timer(0.3, lambda: os._exit(0)).start()
            return
        if self.path in ('/api/install', '/api/launch'):
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8')) if length else {}
            try:
                if self.path == '/api/install':
                    log = self.run_install(data)
                else:
                    log = self.run_launch(data)
                res = {"ok": True, "log": log}
            except Exception as e:
                res = {"ok": False, "error": str(e)}
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))
        else:
            self.send_error(404)
    def run_install(self, cfg):
        target = os.path.abspath(cfg.get('root', 'C:\\JewAI_v5'))
        log_lines = []
        os.makedirs(target, exist_ok=True)
        log_path = os.path.join(target, 'install.log')
        def log(msg):
            log_lines.append(msg)
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(msg + "\n")
        try:
            log(f"Target: {target}")
            # 10C BUG-010: проверка Python-зависимостей до копирования.
            # websocket-client нужен для Bridge/cdp.py, Tools/launcher.py push_storage,
            # Tools/kick_cdp.py. Без него Bridge A не стартует, launcher не пушит agentUrl
            # в sidepanel -> autodetect не находит агента -> "Failed to fetch".
            _need = ["websocket"]
            _missing = []
            for _m in _need:
                try:
                    __import__(_m)
                except Exception:
                    _missing.append(_m)
            if _missing:
                log(f"10C: отсутствуют Python-модули: {_missing}. Пробую pip install...")
                _req_src = os.path.join(ROOT, "requirements.txt")
                _req_dst = os.path.join(target, "requirements.txt")
                _pip_ok = False
                if os.path.isfile(_req_src):
                    try:
                        _r = subprocess.run(
                            [sys.executable, "-m", "pip", "install", "-r", _req_src],
                            capture_output=True, text=True, timeout=180,
                            encoding="utf-8", errors="replace")
                        for _ln in (_r.stdout or "").splitlines()[-4:]:
                            log("  pip: " + _ln[:200])
                        if _r.returncode != 0:
                            log("  pip rc=%d stderr=%s" % (_r.returncode, (_r.stderr or "")[:300]))
                        else:
                            _pip_ok = True
                    except Exception as _e:
                        log("  pip ERR: %r" % _e)
                else:
                    # fallback: ставим поштучно известные пакеты
                    _pkg = {"websocket": "websocket-client"}
                    try:
                        _args = [sys.executable, "-m", "pip", "install"] + [_pkg.get(m, m) for m in _missing]
                        _r = subprocess.run(_args, capture_output=True, text=True, timeout=180,
                                            encoding="utf-8", errors="replace")
                        if _r.returncode == 0:
                            _pip_ok = True
                    except Exception as _e:
                        log("  pip ERR: %r" % _e)
                # Перепроверка
                _still = []
                for _m in _missing:
                    try:
                        __import__(_m)
                    except Exception:
                        _still.append(_m)
                if _still:
                    raise RuntimeError(
                        "10C BUG-010: не установлены Python-модули: %s.\n"
                        "  Ручной фикс: %s -m pip install -r %s\n"
                        "  На Windows Python из Microsoft Store ограничивает pip - поставь с python.org."
                        % (_still, sys.executable, _req_src)
                    )
                log("10C: зависимости OK после установки.")
            else:
                log("10C: Python-зависимости в порядке.")
            # 8C B-35: kill Chrome BEFORE copying CfT from ROOT (was WinError 32).
            _kill_chrome_for_target(target, log)
            _kill_python_for_target(target, log)
            if os.path.abspath(ROOT).lower() == os.path.abspath(target).lower():
                # 8C B-43: same-dir install. Templates/extension NOT refreshed from source.
                log("WARNING (B-43): source == target (%s). Files not copied. Templates/extension"
                    " will keep whatever is on disk. For a clean install, run install.bat from"
                    " a SEPARATE source dir into a fresh target dir." % target)
            if ROOT.lower() != target.lower():
                log("Copying files...")
                # 8C B-35: exclude 'chrome-for-testing' — CfT copied later with retry+kill
                ignore = shutil.ignore_patterns('.git', '__pycache__', '*.pyc', 'logs', 'runtime', 'Agents', 'Profiles', 'Archive', 'media', 'backups', '.agent_token', 'start-*.bat', 'stop-*.bat', 'restart-*.bat', 'server-*.bat', 'create-shortcut.bat', 'chrome-for-testing')
                shutil.copytree(ROOT, target, dirs_exist_ok=True, ignore=ignore)
                log("Files copied.")
            else:
                log("Same directory, skip copy.")
            base_port = int(cfg.get('basePort', 8680))  # 7C B-32: v5 default base_port
            n = int(cfg.get('agentCount', 1))
            chat_port = int(cfg.get('chatPort', 8670))
            proxy_port = int(cfg.get('proxyPort', 9899))

            # 11B + 7C B-32: preflight port validation with AUTO-SHIFT (no hard failure).
            installer_port = PORT  # module-level, 8660
            if chat_port == installer_port:
                raise ValueError(
                    "chat_port (%d) == installer port (%d). "
                    "Choose another chat port (e.g. 8670)." % (chat_port, installer_port)
                )
            if proxy_port == installer_port or proxy_port == chat_port:
                raise ValueError(
                    "proxy_port (%d) conflicts with installer (%d) or chat (%d)." % (proxy_port, installer_port, chat_port)
                )
            # 7C B-32: auto-shift base_port and cdp_base if they would collide with
            # installer/chat/proxy within the [base, base+n-1] range.
            reserved = {installer_port, chat_port, proxy_port}
            def _range_collides(start, count):
                return any((start + i) in reserved for i in range(count))
            if _range_collides(base_port, n):
                old_base = base_port
                base_port = max(reserved) + 20
                # re-check, bump again if needed (paranoid)
                while _range_collides(base_port, n):
                    base_port += 20
                log("B-32 auto-shift: base_port %d conflicted with reserved %s within %d agents; shifted to %d" %
                    (old_base, sorted(reserved), n, base_port))
            cdp_base = 9122
            if _range_collides(cdp_base, n):
                old_cdp = cdp_base
                cdp_base = max(reserved) + 20
                while _range_collides(cdp_base, n):
                    cdp_base += 20
                log("B-32 auto-shift: cdp_base %d conflicted within %d agents; shifted to %d" %
                    (old_cdp, n, cdp_base))
            # explicit last-line check (should never trigger after shifts)
            for _i in range(n):
                _ap = base_port + _i
                _cp = cdp_base + _i
                if _ap in reserved:
                    raise ValueError("agent port %d STILL conflicts after auto-shift" % _ap)
                if _cp in reserved:
                    raise ValueError("cdp port %d STILL conflicts after auto-shift" % _cp)
            for d in ['Core', 'Bridge', 'Adapters', 'Mainframe', 'Rebirth', 'Tools', 'Templates', 'logs', 'Projects', 'Archive', 'Profiles']:
                os.makedirs(os.path.join(target, d), exist_ok=True)
                # 12B: ensure logs/JOURNAL.md and logs/TODO.md
                os.makedirs(os.path.join(target, 'logs'), exist_ok=True)
                for tpl_name in ('JOURNAL.md', 'TODO.md'):
                    tpl_src = os.path.join(ROOT, 'Templates', 'logs', tpl_name)
                    tpl_dst = os.path.join(target, 'logs', tpl_name)
                    if os.path.exists(tpl_src) and not os.path.exists(tpl_dst):
                        shutil.copyfile(tpl_src, tpl_dst)
                        log(f"Seeded logs/{tpl_name}")
            # 10C BUG-008/BUG-009: ищем CfT (Chrome for Testing) ДО init профилей.
            # Без CfT Chrome 137+ игнорирует --load-extension (B-44) - блокер.
            def _find_cft():
                cands = []
                cands.append((os.path.join(ROOT, "tools", "chrome-for-testing"), "ROOT/tools"))
                cands.append((os.path.join(target, "tools", "chrome-for-testing"), "target/tools"))
                _cfgp = os.path.join(target, "config.json")
                if os.path.exists(_cfgp):
                    try:
                        _c = json.loads(open(_cfgp, encoding="utf-8").read())
                        _cp = _c.get("chrome_path") or ""
                        if _cp and os.path.isfile(_cp) and "chrome-for-testing" in _cp.lower():
                            cands.insert(0, (os.path.dirname(_cp), "config.chrome_path"))
                    except Exception:
                        pass
                for _dir, _src in cands:
                    _exe = os.path.join(_dir, "chrome.exe")
                    if os.path.isfile(_exe):
                        return _exe, _src
                return None, None
            cft_exe, cft_src_name = _find_cft()
            if cft_exe is None:
                # 10C BUG-008 (полный фикс): CfT не найден - пробуем скачать.
                # Скрипт Tools/get_cft.py тянет официальный chrome-win64.zip
                # с googlechromelabs.github.io и кладёт в target/tools/chrome-for-testing.
                _gcft = os.path.join(target, "Tools", "get_cft.py")
                if not os.path.exists(_gcft):
                    _gcft = os.path.join(ROOT, "Tools", "get_cft.py")
                if os.path.exists(_gcft):
                    log("10C: CfT не найден, скачиваю через get_cft.py (~448 MB, 1-3 мин)...")
                    try:
                        _dst_cft = os.path.join(target, "tools", "chrome-for-testing")
                        _r = subprocess.run(
                            [sys.executable, _gcft, "--dest", _dst_cft],
                            capture_output=True, text=True, timeout=900,
                            encoding="utf-8", errors="replace")
                        for _line in (_r.stdout or "").splitlines()[-6:]:
                            log("  gcft: " + _line[:200])
                        if _r.returncode != 0:
                            log("10C: get_cft.py rc=%d; stderr=%s" % (_r.returncode, (_r.stderr or "")[:300]))
                    except Exception as _e:
                        log("10C: get_cft.py ERR: %r" % _e)
                    cft_exe, cft_src_name = _find_cft()
            if cft_exe is None:
                raise RuntimeError(
                    "10C BUG-008: Chrome for Testing (CfT) не найден.\n"
                    "  Проверены: ROOT/tools, target/tools, config.chrome_path.\n"
                    "  Без CfT Chrome 137+ НЕ загрузит unpacked extension (B-44).\n"
                    "  Автоскачивание через Tools/get_cft.py провалилось (см. лог выше).\n"
                    "  Проверь интернет / прокси, или скачай вручную:\n"
                    "  https://googlechromelabs.github.io/chrome-for-testing/\n"
                    "  chrome-win64.zip -> распаковать в <target>/tools/chrome-for-testing/.\n"
                    "  Или задай config.chrome_path на существующий chrome.exe."
                )
            log(f"10C CfT: {cft_exe} (from {cft_src_name})")
            _tc = os.path.join(target, "config.json")
            try:
                _tcj = json.loads(open(_tc, encoding="utf-8").read()) if os.path.exists(_tc) else {}
                _tcj["chrome_path"] = cft_exe
                open(_tc, "w", encoding="utf-8").write(json.dumps(_tcj, ensure_ascii=False, indent=2))
                log(f"10C chrome_path -> {cft_exe}")
            except Exception as _e:
                log(f"10C chrome_path write WARN: {_e}")
            letters = list("ABCDEFGHIJ")[:n]
            chrome_paths = [
                cft_exe,  # 10C: CfT приоритет (системный Chrome 137+ не грузит ext)
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
            chrome_exe = next((p for p in chrome_paths if os.path.exists(p)), None)
            
            # 7C B-19/B-23: kill stale Chrome and python processes from previous run
            _kill_chrome_for_target(target, log)
            _kill_python_for_target(target, log)
            
            tmpl_ext = os.path.join(target, 'Templates', 'extension')
            for L in letters:
                agent_root = os.path.join(target, 'Profiles', L)
                for sub in ('chrome', 'config', 'logs', 'docs', 'extension'):
                    os.makedirs(os.path.join(agent_root, sub), exist_ok=True)
                ext_dir = os.path.join(agent_root, 'extension')
                if os.path.isdir(tmpl_ext):
                    try:
                        shutil.copytree(tmpl_ext, ext_dir, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                        log(f"Extension copied for {L}")
                    except Exception as e:
                        log(f"Extension copy failed for {L}: {e}")
                chrome_dir = os.path.join(agent_root, 'chrome')
                if chrome_exe:
                    log(f"Initializing Chrome profile for {L}...")
                    try:
                        p = subprocess.Popen([chrome_exe, f'--user-data-dir={chrome_dir}',
                                             f'--load-extension={ext_dir}',
                                             '--no-first-run', '--no-default-browser-check', '--hide-crash-restore-bubble',
                                             'about:blank'],
                                             creationflags=subprocess.CREATE_NO_WINDOW)
                        time.sleep(2)
                        p.terminate()
                        log(f"Profile {L} initialized.")
                    except Exception as e:
                        log(f"Failed to init profile {L}: {e}")
                else:
                    log("WARNING: Chrome not found. Profiles will be created on first launch.")
            names_raw = cfg.get('names', '')
            names_list = [x.strip() for x in names_raw.split(',') if x.strip()]
            
            channels = {}
            for i, L in enumerate(letters):
                # 7C B-05: nicer fallback for agents without an explicit name
                if i < len(names_list):
                    cname = names_list[i]
                else:
                    cname = "Agent " + L
                channels[L] = {
                    "name": cname,
                    "agent": base_port + i,
                    "cdp": cdp_base + i,
                    "prefix": "AAAA" if L == "A" else L + L + "AA",
                    "extension": "Profiles/" + L + "/extension",
                    "model": "deepseek"  # 11B: default; qwen/alice = test-only, via manual extension swap
                }
            
            config = {
                "root": target, "agent_port_base": base_port, "n_agents": n,
                "chat_port": chat_port, "proxy_port": proxy_port, "doh_proxy_port": proxy_port,
                "letters": letters,
                "channels": channels,
                "thresholds": {"rebirth_cmds": 850},
                "timeouts": {"cdp": 5, "poll_ms": 2000, "stable_ms": 1200},
                "version": "0.1.0-dev",
                # 10C BUG-008: chrome_path обязателен в config - launcher его читает.
                # Иначе Chrome A ищется в системных путях -> 137+ не грузит unpacked ext.
                "chrome_path": cft_exe if cft_exe else "",
            }
            with open(os.path.join(target, 'config.json'), 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            log("Config saved.")
            for i, L in enumerate(letters):
                ch_cfg = {
                    "channel": L,
                    "name": channels[L]["name"],
                    "prefix": channels[L]["prefix"],
                    "agent_port": channels[L]["agent"],
                    "cdp_port": channels[L]["cdp"],
                    "agent_url": "http://127.0.0.1:" + str(channels[L]["agent"]),
                    "extension": channels[L]["extension"],
                    "model": channels[L]["model"],
                    "root": target,
                    "chat_port": chat_port,
                }
                ch_cfg_path = os.path.join(target, 'Profiles', L, 'config', 'config.json')
                with open(ch_cfg_path, 'w', encoding='utf-8') as f:
                    json.dump(ch_cfg, f, indent=2, ensure_ascii=False)
            log("Per-agent configs saved.")
            # 11B: copy Chrome for Testing to target (if present in source)
            cft_src = os.path.join(ROOT, 'tools', 'chrome-for-testing')
            cft_dst = os.path.join(target, 'tools', 'chrome-for-testing')
            if os.path.isdir(cft_src) and os.path.isfile(os.path.join(cft_src, 'chrome.exe')):
                # 8C B-42: if src==dst, skip copytree (was WinError 3 after rmtree(dst))
                try:
                    _same_cft = False
                    try:
                        _same_cft = os.path.samefile(cft_src, cft_dst)
                    except (FileNotFoundError, OSError):
                        _same_cft = os.path.abspath(cft_src).lower() == os.path.abspath(cft_dst).lower()
                    if _same_cft:
                        log("B-42: CfT src==dst, skipping copy (already in place)")
                        raise Exception("__CFT_SKIP__")
                    _copy_ok = False
                    _last_err = None
                    for _try in range(1, 6):
                        try:
                            if os.path.isdir(cft_dst):
                                shutil.rmtree(cft_dst, ignore_errors=True)
                            shutil.copytree(cft_src, cft_dst, dirs_exist_ok=True)
                            _copy_ok = True
                            break
                        except Exception as _ce:
                            _last_err = _ce
                            _we = getattr(_ce, "winerror", 0)
                            if _we == 32 or "WinError 32" in str(_ce) or "cannot access" in str(_ce).lower():
                                log("B-28: CfT copy locked (try %d/5), killing chrome and retrying..." % _try)
                                _kill_chrome_for_target(target, log)
                                time.sleep(2.5)
                                continue
                            raise
                    if not _copy_ok:
                        raise _last_err or RuntimeError("CfT copy failed after 5 tries")
                    log(f"Chrome for Testing copied to {cft_dst}")
                    # set chrome_path in target config.json
                    tc = os.path.join(target, 'config.json')
                    with open(tc, 'r', encoding='utf-8') as f:
                        _cfg = json.load(f)
                    _cfg['chrome_path'] = os.path.join(cft_dst, 'chrome.exe')
                    with open(tc, 'w', encoding='utf-8') as f:
                        json.dump(_cfg, f, indent=2, ensure_ascii=False)
                    log(f"chrome_path set to CfT: {_cfg['chrome_path']}")
                except Exception as _e:
                    if "__CFT_SKIP__" in str(_e):
                        pass  # B-42: already logged above
                    else:
                        log(f"CfT copy failed: {_e}")
            else:
                log("10C: CfT copy skipped (CfT already in use: %s)" % cft_exe)
            # 11B: generate launchers (start/stop/restart per channel + server)
            # 11B: remove stale launchers copied from source before regenerating
            stale_la = os.path.join(target, 'Tools', 'launchers')
            if os.path.isdir(stale_la):
                shutil.rmtree(stale_la, ignore_errors=True)
                log("Removed stale Tools/launchers before regenerating.")
            gen_l = os.path.join(target, 'Tools', 'gen_launchers.py')
            if os.path.exists(gen_l):
                try:
                    env_g = os.environ.copy()
                    env_g["JEWAI_CONFIG"] = os.path.join(target, 'config.json')
                    gr = subprocess.run([sys.executable, gen_l], cwd=target, env=env_g,
                                        capture_output=True, text=True, timeout=30)
                    log("gen_launchers rc=%d out=%s" % (gr.returncode, (gr.stdout or '').strip()[:200]))
                except Exception as e:
                    log("gen_launchers failed: %s" % e)
            else:
                log("WARNING: Tools/gen_launchers.py not found, launchers not generated.")
            tok_path = os.path.join(target, '.agent_token')
            if not os.path.exists(tok_path):
                with open(tok_path, 'w', encoding='utf-8') as f:
                    f.write(secrets.token_urlsafe(32))
                log(".agent_token created.")
            log("Installation complete (services NOT started).")
            return "\n".join(log_lines)
        except Exception as e:
            log(f"FATAL: {e}")
            raise
    def run_launch(self, cfg):
        target = os.path.abspath(cfg.get('root', 'C:\\JewAI_v5'))
        log_lines = []
        log_path = os.path.join(target, 'install.log')
        def log(msg):
            log_lines.append(msg)
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(msg + "\n")
        cfg_path = os.path.join(target, 'config.json')
        if not os.path.exists(cfg_path):
            raise Exception("config.json not found in " + target)
        # 11B: ensure launchers exist
        gen_l = os.path.join(target, 'Tools', 'gen_launchers.py')
        if os.path.exists(gen_l) and not os.path.isdir(os.path.join(target, 'Tools', 'launchers')):
            try:
                env_g = os.environ.copy()
                env_g["JEWAI_CONFIG"] = cfg_path
                subprocess.run([sys.executable, gen_l], cwd=target, env=env_g,
                               capture_output=True, text=True, timeout=30)
                log("gen_launchers (run_launch)")
            except Exception as e:
                log("gen_launchers (run_launch) failed: %s" % e)
        with open(cfg_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        chat_port = config.get('chat_port', 8670)
        proxy_port = config.get('proxy_port', 9899)
        letters = config.get('letters', [])
        channels = config.get('channels', {})
        def spawn(name, args, cwd):
            try:
                proc = subprocess.Popen([sys.executable] + args, cwd=cwd,
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
                log(f"{name} started (pid {proc.pid})")
                return True
            except Exception as e:
                log(f"{name} failed: {e}")
                return False
        doh = os.path.join(target, 'Tools', 'doh_proxy.py')
        if os.path.exists(doh):
            spawn("DoH proxy", [doh, '--port', str(proxy_port)], target)
        mf = os.path.join(target, 'Mainframe', 'server.py')
        if os.path.exists(mf):
            log("Killing old processes on port " + str(chat_port) + "...")
            # 11B: never kill self (installer runs on PORT, chat_port might equal it)
            self_pid = os.getpid()
            kill_cmd = ("Get-NetTCPConnection -LocalPort " + str(chat_port) +
                        " -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | "
                        "Where-Object {$_ -ne 0 -and $_ -ne " + str(self_pid) + "} | "
                        "ForEach-Object { Stop-Process -Id $_ -Force }")
            if int(chat_port) == int(PORT):
                log("WARNING: chat_port == installer port; skipping kill (would kill self).")
            else:
                subprocess.run(['powershell', '-c', kill_cmd], capture_output=True)
            time.sleep(1)
            env = os.environ.copy()
            env["JEWAI_CONFIG"] = os.path.join(target, "config.json")
            mf_proc = subprocess.Popen([sys.executable, mf], cwd=target, env=env,
                             creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
            log(f"Mainframe spawned (pid {mf_proc.pid}).")
            time.sleep(2.0)
            try:
                import urllib.request as _ur
                _ur.urlopen(f"http://127.0.0.1:{chat_port}/api/health", timeout=3).read()
                log(f"Mainframe health OK on {chat_port}.")
            except Exception as _e:
                log(f"Mainframe health FAILED on {chat_port} after 2s: {type(_e).__name__}: {_e}")
        for L in letters:
            agent_port = channels.get(L, {}).get('agent')
            if not agent_port: continue
            run_py = os.path.join(target, 'Bridge', 'run.py')
            if os.path.exists(run_py):
                spawn(f"Bridge {L}", [run_py, '--channel', L], target)
            else:
                log(f"Bridge {L}: Bridge/run.py not found, skipped.")
            # 11B: also start HTTP agent (agent.py, port <agent>) per channel
            agent_py = os.path.join(target, 'Profiles', L, 'extension', 'agent.py')
            if not os.path.exists(agent_py):
                agent_py = os.path.join(target, 'Templates', 'extension', 'agent.py')
            if os.path.exists(agent_py):
                spawn(f"Agent {L}", [agent_py, str(agent_port)], target)
                # 7C bug3b: verify /ping after spawn (process may be alive but port-busy/dying)
                _ping_ok = False
                for _try in range(6):
                    time.sleep(0.5)
                    try:
                        _ur2 = __import__("urllib.request", fromlist=["urlopen"])
                        _ur2.urlopen(f"http://127.0.0.1:{agent_port}/ping", timeout=1).read()
                        _ping_ok = True
                        break
                    except Exception:
                        pass
                if _ping_ok:
                    log(f"Agent {L} /ping OK on {agent_port}.")
                else:
                    log(f"Agent {L} /ping FAILED on {agent_port} after 3s (agent.py exited? port busy? check {agent_py}).")
            else:
                log(f"Agent {L}: agent.py not found (HTTP /ping will be DOWN).")
        launcher_py = os.path.join(target, 'Tools', 'launcher.py')
        if os.path.exists(launcher_py):
            env_l = os.environ.copy()
            env_l["JEWAI_CONFIG"] = os.path.join(target, "config.json")
            for L in letters:
                try:
                    r = subprocess.run([sys.executable, launcher_py, '--channel', L],
                                       cwd=target, env=env_l, capture_output=True, text=True, timeout=60,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
                    log(f"Chrome {L} launcher rc={r.returncode} out={(r.stdout or '').strip()[:200]}")
                except Exception as e:
                    log(f"Chrome {L} launcher failed: {e}")
        else:
            log("WARNING: Tools/launcher.py not found, Chrome not started.")
        log(f"Launch complete. Mainframe: http://127.0.0.1:{chat_port}/")
        # 7C B-03: schedule self-shutdown (browser redirects to mainframe, installer no longer needed)
        def _delayed_shutdown():
            time.sleep(15)
            os._exit(0)
        import threading as _th
        _th.Thread(target=_delayed_shutdown, daemon=False).start()
        log("Installer will self-shutdown in 15s.")
        return "\n".join(log_lines)



def _kill_stale_on_port():
    my_pid = os.getpid()
    try:
        r = subprocess.run(
            ["powershell", "-c",
             "Get-NetTCPConnection -LocalPort %d -ErrorAction SilentlyContinue | "
             "Select-Object -ExpandProperty OwningProcess -Unique" % PORT],
            capture_output=True, text=True, timeout=10)
        for line in (r.stdout or "").splitlines():
            line = line.strip()
            if line.isdigit():
                pid = int(line)
                if pid and pid != my_pid:
                    subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                                   capture_output=True, timeout=5)
    except Exception:
        pass


if __name__ == '__main__':
    os.chdir(HERE)
    _kill_stale_on_port()
    with http.server.ThreadingHTTPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()