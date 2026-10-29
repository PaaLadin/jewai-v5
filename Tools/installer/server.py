import http.server, json, os, shutil, secrets, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PORT = 8660  # 11B: 8671 = agent E in v5

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HERE, **kwargs)
    def log_message(self, format, *args):
        pass
    def do_POST(self):
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
            if ROOT.lower() != target.lower():
                log("Copying files...")
                ignore = shutil.ignore_patterns('.git', '__pycache__', '*.pyc', 'logs', 'runtime', 'Agents', 'Profiles', 'Archive', 'media', 'backups', '.agent_token')
                shutil.copytree(ROOT, target, dirs_exist_ok=True, ignore=ignore)
                log("Files copied.")
            else:
                log("Same directory, skip copy.")
            base_port = int(cfg.get('basePort', 8666))  # 11B: v5 default
            n = cfg.get('agentCount', 4)
            chat_port = cfg.get('chatPort', 8670)
            proxy_port = cfg.get('proxyPort', 9999)
            for d in ['Core', 'Bridge', 'Adapters', 'Mainframe', 'Rebirth', 'Tools', 'Templates', 'logs', 'Projects', 'Archive', 'Profiles']:
                os.makedirs(os.path.join(target, d), exist_ok=True)
            letters = list("ABCDEFGHIJ")[:n]
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
            chrome_exe = next((p for p in chrome_paths if os.path.exists(p)), None)
            
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
                cname = names_list[i] if i < len(names_list) else L
                channels[L] = {
                    "name": cname,
                    "agent": base_port + i,
                    "cdp": 9122 + i,
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
                "version": "0.1.0-dev"
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
        proxy_port = config.get('proxy_port', 9999)
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
            kill_cmd = f"Get-NetTCPConnection -LocalPort {chat_port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | Where-Object {{$_ -ne 0}} | ForEach-Object {{ Stop-Process -Id $_ -Force }}"
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
                spawn(f"Agent {L}", [run_py, '--channel', L], target)
            else:
                log(f"Agent {L}: Bridge/run.py not found, skipped.")
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
        return "\n".join(log_lines)

if __name__ == '__main__':
    os.chdir(HERE)
    with http.server.ThreadingHTTPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()