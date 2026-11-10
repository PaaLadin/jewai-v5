import json, uuid, time
from pathlib import Path

CHATS_DIR = Path("Profiles/A/chats")

def list_chats():
    CHATS_DIR.mkdir(parents=True, exist_ok=True)
    res = []
    for f in CHATS_DIR.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            res.append({"id": f.stem, "title": d.get("title", "New Chat"), "updated": f.stat().st_mtime})
        except: pass
    return sorted(res, key=lambda x: x["updated"], reverse=True)

def create_chat(title="New Chat"):
    cid = str(uuid.uuid4())[:8]
    CHATS_DIR.mkdir(parents=True, exist_ok=True)
    (CHATS_DIR / f"{cid}.json").write_text(json.dumps({"title": title, "messages": []}, ensure_ascii=False), encoding="utf-8")
    return cid

def get_chat(cid):
    p = CHATS_DIR / f"{cid}.json"
    if not p.exists(): return []
    return json.loads(p.read_text(encoding="utf-8")).get("messages", [])

def append_message(cid, role, text):
    p = CHATS_DIR / f"{cid}.json"
    d = {"title": "New Chat", "messages": []}
    if p.exists(): d = json.loads(p.read_text(encoding="utf-8"))
    d["messages"].append({"role": role, "content": text, "ts": time.time()})
    if role == "user" and d["title"] == "New Chat" and len(d["messages"]) == 1:
        d["title"] = text[:30] + "..."
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return True
def delete_chat(cid):
    p = CHATS_DIR / f"{cid}.json"
    if p.exists(): p.unlink()
    return True
