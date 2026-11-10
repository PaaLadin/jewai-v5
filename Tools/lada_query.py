"""Tools/lada_query.py - запрос к Lada с RAG-контекстом.

Ищет top-K чанков (простой keyword-scoring без embeddings), формирует
prompt "Ты Lada, помощник JewAI. Вот фрагменты документации: ... Вопрос: ...",
шлёт в Lada через Mainframe/llm.py, возвращает ответ.

Usage:
  python Tools/lada_query.py --q "как работает rebirth?" --topk 3
  python Tools/lada_query.py --q "..." --no-rag   # без контекста
"""
import argparse, io, json, sys, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
CHUNKS_PATH = ROOT / "RAG" / "lada_chunks.jsonl"


def load_chunks():
    if not CHUNKS_PATH.exists():
        return []
    out = []
    with open(CHUNKS_PATH, encoding="utf-8") as f:
        for ln in f:
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
    return out


def score(query, chunk):
    """Простой keyword-score: доля токенов запроса, найденных в чанке."""
    q_tokens = set(re.findall(r"\w+", query.lower()))
    if not q_tokens:
        return 0.0
    c_lower = chunk.lower()
    hits = sum(1 for t in q_tokens if t in c_lower)
    return hits / len(q_tokens)


def top_k(query, chunks, k=3):
    scored = [(score(query, c["chunk"]), c) for c in chunks]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for s, c in scored[:k] if s > 0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", required=True)
    ap.add_argument("--topk", type=int, default=3)
    ap.add_argument("--no-rag", action="store_true")
    ap.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args()

    chunks = [] if a.no_rag else load_chunks()
    selected = top_k(a.q, chunks, a.topk) if chunks else []

    if selected:
        ctx = "\n\n".join("[%s]\n%s" % (c["id"], c["chunk"]) for c in selected)
        prompt = (
            "Ты Lada, локальный помощник проекта JewAI. Отвечай кратко по-русски.\n"
            "Ниже — фрагменты документации:\n\n" + ctx +
            "\n\nВопрос: " + a.q + "\n\nОтвет:"
        )
    else:
        prompt = a.q

    from Core.config import load as load_config
    from Mainframe.llm import query as llm_query
    cfg = load_config()
    r = llm_query(cfg, prompt, max_tokens=400, timeout=a.timeout)
    if not r.get("ok"):
        print("FAIL:", r.get("error"), (r.get("body") or "")[:200])
        return 2
    resp = r.get("response") or {}
    choices = resp.get("choices") or []
    if choices:
        print(choices[0].get("message", {}).get("content", ""))
    print("")
    print("--- meta ---")
    print("chunks used:", len(selected))
    for c in selected:
        print("  %s (%s, %d b)" % (c["id"], c["source"], c["bytes"]))
    print("usage:", json.dumps(resp.get("usage", {}), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())