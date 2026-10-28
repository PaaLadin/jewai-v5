import http.server, json, os, socketserver
HERE = os.path.dirname(os.path.abspath(__file__))
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
        target = cfg.get('root', 'C:\\JewAI')
        base_port = cfg.get('basePort', 8760)
        n = cfg.get('agentCount', 4)
        chat_port = cfg.get('chatPort', 8670)
        proxy_port = cfg.get('proxyPort', 9999)
        log = []
        log.append(f"Создание структуры в {target}...")
        for d in ['Core', 'Bridge', 'Adapters', 'Mainframe', 'Rebirth', 'Tools', 'Agents', 'Templates', 'logs']:
            os.makedirs(os.path.join(target, d), exist_ok=True)
        log.append("Копирование исходников...")
        config = {
            "root": target, "agent_port_base": base_port, "n_agents": n,
            "chat_port": chat_port, "proxy_port": proxy_port,
            "letters": list("ABCDEFGHIJ")[:n],
            "channels": {L: {"agent": base_port + i, "cdp": 9220 + i, "prefix": "AAAA" if L == "A" else L + L + "AA"} for i, L in enumerate("ABCDEFGHIJ"[:n])}
        }
        cfg_path = os.path.join(target, 'config.json')
        with open(cfg_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        log.append(f"Конфигурация сохранена в {cfg_path}")
        log.append("Установка завершена успешно.")
        return "\n".join(log)
if __name__ == '__main__':
    os.chdir(HERE)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Installer UI on http://127.0.0.1:{PORT}")
        httpd.serve_forever()