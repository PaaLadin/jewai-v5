import http.server, json, os, shutil, secrets, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PORT = 8671

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
                ignore = shutil.ignore_patterns('.git', '__pycache__', '*.pyc', 'logs', 'runtime', 'Agents', 'Profiles', 'Archive', 'media', 'backups')
                shutil.copytree(ROOT, target, dirs_exist_ok=True, ignore=ignore)
                log("Files copied.")
            else:
                log("Same directory, skip copy.")
            base_port = cfg.get('basePort', 8760)
            n = cfg.get('agentCount', 4)
            chat_port = cfg.get('chatPort', 8670)
            proxy_port = cfg.get('proxyPort', 9999)
            for d in ['Core', 'Bridge', 'Adapters', 'Mainframe', 'Rebirth', 'Tools', 'Agents', 'Templates', 'logs']:
                os.makedirs(os.path.join(target, d), exist_ok=True)
            letters = list("ABCDEFGHIJ")[:n]
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
            chrome_exe = next((p for p in chrome_paths if os.path.exists(p)), None)
            
            for L in letters:
                os.makedirs(os.path.join(target, 'Agents', L), exist_ok=True)
                prof_dir = os.path.join(target, 'Profiles', L)
                os.makedirs(prof_dir, exist_ok=True)
                if chrome_exe:
                    log(f"Initializing Chrome profile for {L}...")
                    try:
                        # Spawn chrome briefly to generate profile, then kill it
                        p = subprocess.Popen([chrome_exe, f'--user-data-dir={prof_dir}', '--no-first-run', '--no-default-browser-check', 'about:blank'],
                                             creationflags=subprocess.CREATE_NO_WINDOW)
                        time.sleep(2)
                        p.terminate()
                        log(f"Profile {L} initialized.")
                    except Exception as e:
                        log(f"Failed to init profile {L}: {e}")
                else:
                    log("WARNING: Chrome not found. Profiles will be created on first launch.")
            config = {
                "root": target, "agent_port_base": base_port, "n_agents": n,
                "chat_port": chat_port, "proxy_port": proxy_port,
                "letters": letters,
                "channels": {L: {"agent": base_port + i, "cdp": 9220 + i, "prefix": "AAAA" if L == "A" else L + L + "AA"} for i, L in enumerate(letters)}
            }
            with open(os.path.join(target, 'config.json'), 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            log("Config saved.")
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
            spawn("Mainframe", [mf], target)
            time.sleep(1.5)
        for L in letters:
            agent_port = channels.get(L, {}).get('agent')
            if not agent_port: continue
            candidates = [
                os.path.join(target, 'Bridge', 'agent.py'),
                os.path.join(target, 'Bridge', 'daemon.py'),
                os.path.join(target, 'Bridge', 'run.py'),
                os.path.join(target, 'Agents', L, 'agent.py'),
            ]
            found = None
            for c in candidates:
                if os.path.exists(c):
                    found = c
                    break
            if found:
                spawn(f"Agent {L}", [found, str(agent_port)], target)
            else:
                log(f"Agent {L}: no agent script found, skipped.")
        log(f"Launch complete. Mainframe: http://127.0.0.1:{chat_port}/")
        return "\n".join(log_lines)

if __name__ == '__main__':
    os.chdir(HERE)
    with http.server.ThreadingHTTPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()