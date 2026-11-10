import os, socket
from Core.config import Config

def _dir_size(path):
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += _dir_size(entry.path)
    except Exception:
        pass
    return total

def _count_files(path):
    c = 0
    try:
        for _, _, files in os.walk(path):
            c += len(files)
    except Exception:
        pass
    return c

def _tcp(port):
    s = socket.socket()
    s.settimeout(0.1)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()

def collect(cfg: Config) -> dict:
    root = cfg.root
    res = {"ok": True}
    
    dirs = {
        "sandbox": root / "Sandbox",
        "projects": root / "Projects",
        "rag": root / "RAG",
        "profiles": root / "Profiles"
    }
    for k, p in dirs.items():
        res[k] = {"size": _dir_size(str(p)), "files": _count_files(str(p))}
        
    res["services"] = {
        "llm": _tcp(1234),
        "proxy": _tcp(1235),
        "mailbot": False,
        "rebirth": False
    }
    return res
