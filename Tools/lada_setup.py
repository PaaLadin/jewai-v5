"""Tools/lada_setup.py - поднять локальную LLM через llama.cpp на HERETIC.

Проблема: LM Studio CLI (lms.exe) требует GUI daemon, которого нет. Headless не умеет.
Решение: llama.cpp - headless, читает тот же .gguf напрямую.

Скрипт делает:
  1. Проверяет, отвечает ли уже 127.0.0.1:1234/v1/models. Если да - выход.
  2. Скачивает llama.cpp (Windows CPU zip, ~50 МБ) с GitHub releases в D:/JewAI_lada/.
  3. Распаковывает.
  4. Находит .gguf в .lmstudio/models (Qwen-3-VL-8B Q4_K_S).
  5. Запускает llama-server.exe -m <gguf> --port 1234 --host 127.0.0.1 -c 4096 (detached).
  6. Ждёт /v1/models.
  7. Прописывает config.json:llm.

Usage:
  python Tools/lada_setup.py
  python Tools/lada_setup.py --gguf <path>
  python Tools/lada_setup.py --port 1234
"""
import argparse, json, os, subprocess, sys, time, urllib.request, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
STATUS = ROOT / "Profiles" / "A" / "logs" / "lada_status.json"
LLAMA_DIR = Path("D:/JewAI_lada")
LLAMA_LOG = ROOT / "Profiles" / "A" / "logs" / "lada_llamacpp.log"
MODELS_DIR = Path.home() / ".lmstudio" / "models"

def _get_setup():
    try:
        return __import__("json").loads(__import__("pathlib").Path("config.json").read_text(encoding="utf-8")).get("llm_setup", {})
    except Exception:
        return {}
_SETUP = _get_setup()
_TAG = _SETUP.get("release_tag", "b12243")
_BACKEND = _SETUP.get("backend", "cuda")
_REPO = "ggml-org/llama.cpp"
_B = "cuda-12.4-x64" if _BACKEND == "cuda" else ("vulkan-x64" if _BACKEND == "vulkan" else ("cpu-x64" if _BACKEND == "cpu" else "avx2-x64"))
_REPO = "ggml-org/llama.cpp"
LLAMA_RELEASE_URL = f"https://github.com/{_REPO}/releases/download/{_TAG}/llama-{_TAG}-bin-win-{_B}.zip"



def log(msg):
    print(msg, flush=True)


def write_status(d):
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    with open(STATUS, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def probe(port):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/v1/models" % port, timeout=3) as r:
            if r.status == 200:
                m = json.loads(r.read().decode("utf-8", "replace"))
                return True, [x.get("id") for x in (m.get("data") or [])]
    except Exception:
        pass
    return False, []


def wait_ready(port, timeout=120):
    t0 = time.time()
    while time.time() - t0 < timeout:
        ok, ids = probe(port)
        if ok:
            return True, ids
        time.sleep(2)
    return False, []


def find_ggufs():
    if not MODELS_DIR.exists():
        return []
    out = []
    for root, dirs, files in os.walk(MODELS_DIR):
        for f in files:
            if f.lower().endswith(".gguf"):
                out.append(Path(root) / f)
    return out


def download_llama():
    if (LLAMA_DIR / "llama-server.exe").exists():
        log("llama.cpp already present")
        return
    LLAMA_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = LLAMA_DIR / "llama.zip"
    log("downloading llama.cpp: %s" % LLAMA_RELEASE_URL)
    urllib.request.urlretrieve(LLAMA_RELEASE_URL, zip_path)
    log("downloaded: %d MB" % (zip_path.stat().st_size // (1024*1024)))
    log("extracting...")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(LLAMA_DIR)
    zip_path.unlink()
    items = [p for p in LLAMA_DIR.iterdir() if p.is_dir()]
    for it in items:
        for f in it.iterdir():
            target = LLAMA_DIR / f.name
            if target.exists():
                continue
            f.rename(target)
        try:
            it.rmdir()
        except Exception:
            pass
    log("extracted to %s" % LLAMA_DIR)


def _write_config(port, model):
    cfg_path = ROOT / "config.json"
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        cfg = {}
    cfg["llm"] = {"host": "127.0.0.1", "port": port,
                  "path": "/v1/chat/completions", "model": model}
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=1), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gguf", default="")
    ap.add_argument("--port", type=int, default=1234)
    ap.add_argument("--ctx", type=int, default=_SETUP.get("ctx", 4096))
    a = ap.parse_args()
    result = {"ts": time.time(), "port": a.port, "stage": "start"}
    write_status(result)

    ok, models = probe(a.port)
    if ok:
        result["stage"] = "already_up"
        result["models"] = models
        _write_config(a.port, models[0] if models else "default")
        result["stage"] = "done"
        write_status(result)
        print(json.dumps({"ok": True, "stage": "already_up", "models": models}, ensure_ascii=False))
        return 0

    try:
        download_llama()
    except Exception as e:
        result["stage"] = "download_failed"
        result["error"] = repr(e)[:400]
        write_status(result)
        print(json.dumps({"ok": False, "error": result["error"]}, ensure_ascii=False))
        return 2

    server_exe = LLAMA_DIR / "llama-server.exe"
    if not server_exe.exists():
        result["stage"] = "server_exe_missing"
        result["error"] = "llama-server.exe not found in %s" % LLAMA_DIR
        write_status(result)
        print(json.dumps({"ok": False, "error": result["error"]}, ensure_ascii=False))
        return 3

    gguf = Path(a.gguf) if a.gguf else None
    if gguf is None or not gguf.exists():
        cands = find_ggufs()
        if not cands:
            result["stage"] = "no_gguf"
            result["error"] = "no .gguf found in %s" % MODELS_DIR
            write_status(result)
            print(json.dumps({"ok": False, "error": result["error"]}, ensure_ascii=False))
            return 4
        gguf = max(cands, key=lambda p: p.stat().st_size)
    result["gguf"] = str(gguf)
    result["gguf_mb"] = gguf.stat().st_size // (1024*1024)

    LLAMA_LOG.parent.mkdir(parents=True, exist_ok=True)
    logf = open(LLAMA_LOG, "ab")
    args = [str(server_exe), "-m", str(gguf), "--host", "127.0.0.1",
            "--port", str(a.port), "-c", str(a.ctx), "-ngl", "99"]
    log("starting: %s" % " ".join(args))
    try:
        proc = subprocess.Popen(
            args, cwd=str(LLAMA_DIR),
            stdout=logf, stderr=logf,
            creationflags=0x08000000 | 0x00000008 | 0x00000200,
        )
        result["llama_pid"] = proc.pid
    except Exception as e:
        result["stage"] = "spawn_failed"
        result["error"] = repr(e)[:400]
        write_status(result)
        print(json.dumps({"ok": False, "error": result["error"]}, ensure_ascii=False))
        return 5

    result["stage"] = "loading"
    write_status(result)
    ok, models = wait_ready(a.port, timeout=180)
    if not ok:
        result["stage"] = "not_ready"
        result["error"] = "server not ready in 180s, see lada_llamacpp.log"
        write_status(result)
        print(json.dumps({"ok": False, "error": result["error"]}, ensure_ascii=False))
        return 6
    result["models"] = models

    model = models[0] if models else "local"
    _write_config(a.port, model)
    result["stage"] = "done"
    result["model"] = model
    write_status(result)
    print(json.dumps({"ok": True, "port": a.port, "model": model, "models": models,
                      "gguf": str(gguf), "gguf_mb": result["gguf_mb"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
