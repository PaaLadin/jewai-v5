import http.server, json, os, socketserver, shutil, secrets
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PORT = 8671
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HERE, **kwargs)
    def do_POST(self):
        if self.path == '/api/install':
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length).decode('utf-8'))
            try:
                log = self.run_install(data)
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
        target = os.path.abspath(cfg.get('root', 'C:\\JewAI'))
        log = [f"Целевая папка: {target}"]
        if ROOT.lower() != target.lower():
            log.append("Копирование файлов проекта...")
            ignore = shutil.ignore_patterns('.git', '__pycache__', '*.pyc', 'logs', 'runtime', 'Agents')
            shutil.copytree(ROOT, target, dirs_exist_ok=True, ignore=ignore)
            log.append("Файлы скопированы.")
        else:
            log.append("Установка на месте (source == target). Копирование пропущено.")
        base_port = cfg.get('basePort', 8760)
        n = cfg.get('agentCount', 4)
        chat_port = cfg.get('chatPort', 8670)
        proxy_port = cfg.get('proxyPort', 9999)
        for d in ['Core', 'Bridge', 'Adapters', 'Mainframe', 'Rebirth', 'Tools', 'Agents', 'Templates', 'logs']:
            os.makedirs(os.path.join(target, d), exist_ok=True)
        letters = list("ABCDEFGHIJ")[:n]
        for L in letters:
            os.makedirs(os.path.join(target, 'Agents', L), exist_ok=True)
        config = {
            "root": target, "agent_port_base": base_port, "n_agents": n,
            "chat_port": chat_port, "proxy_port": proxy_port,
            "letters": letters,
            "channels": {L: {"agent": base_port + i, "cdp": 9220 + i, "prefix": "AAAA" if L == "A" else L + L + "AA"} for i, L in enumerate(letters)}
        }
        cfg_path = os.path.join(target, 'config.json')
        with open(cfg_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        log.append(f"Конфигурация сохранена в {cfg_path}")
        tok_path = os.path.join(target, '.agent_token')
        if not os.path.exists(tok_path):
            with open(tok_path, 'w', encoding='utf-8') as f:
                f.write(secrets.token_urlsafe(32))
            log.append(".agent_token создан.")
        log.append("Установка завершена успешно.")
        return "\n".join(log)
if __name__ == '__main__':
    os.chdir(HERE)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()