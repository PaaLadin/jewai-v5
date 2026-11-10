"""Tools/lada_rag.py - подготовка чанков RAG для Lada.

Берёт RAG-документы v5, режет на чанки по ~1500 символов с перекрытием 200,
сохраняет в RAG/lada_chunks.jsonl (одна строка = {id, source, chunk, bytes, sha}).

Usage:
  python Tools/lada_rag.py            # сборка RAG/lada_chunks.jsonl
  python Tools/lada_rag.py --stats    # только статистика
"""
import argparse, hashlib, io, json, os, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CHUNKS_PATH = ROOT / "RAG" / "lada_chunks.jsonl"

# Какие документы включаем (ключевые для Lada)
SOURCES = [
    "RAG/procedures/BEHAVIOR.md",
    "RAG/procedures/SYSTEM_MESSAGES.md",
    "RAG/procedures/REBIRTH.md",
    "RAG/procedures/ADAPTERS.md",
    "RAG/procedures/KICK_PROTOCOL.md",
    "RAG/procedures/ALIVE_AND_SERVICES.md",
    "RAG/procedures/ADDONS_CANDIDATES.md",
    "RAG/INDEX.md",
    "RAG/architecture/ARCHITECTURE.md",
    "Templates/PROMPT_ACTIVATION.md",
    "README.md",
]
CHUNK_SIZE = 1500
OVERLAP = 200


def chunk_text(text, size=CHUNK_SIZE, overlap=OVERLAP):
    """Режет текст по границам абзацев, если возможно."""
    chunks = []
    n = len(text)
    pos = 0
    while True:
        end = min(pos + size, n)
        if end < n:
            # ищем последний разделитель абзаца в 2-й половине
            cut = text.rfind(chr(10)*2, pos + size // 2, end)
            if cut > 0:
                end = cut
        chunk = text[pos:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        new_pos = end - overlap
        if new_pos <= pos:
            new_pos = pos + max(1, size // 2)
        pos = new_pos
    return chunks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()

    if a.stats:
        if not CHUNKS_PATH.exists():
            print("MISS:", CHUNKS_PATH); return 2
        total = sum(1 for _ in open(CHUNKS_PATH, encoding="utf-8"))
        print("chunks:", total, "size:", CHUNKS_PATH.stat().st_size, "b")
        return 0

    CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    out = open(CHUNKS_PATH, "w", encoding="utf-8")
    total = 0
    by_source = {}
    for rel in SOURCES:
        src = ROOT / rel
        if not src.exists():
            print("MISS:", rel); continue
        txt = src.read_text(encoding="utf-8", errors="replace")
        # нормализуем, чтобы не было \r
        txt = txt.replace("\r\n", "\n").replace("\r", "\n")
        parts = chunk_text(txt)
        for i, part in enumerate(parts):
            sha = hashlib.sha256(part.encode("utf-8")).hexdigest()[:16]
            entry = {
                "id": "%s#%03d" % (Path(rel).stem, i),
                "source": rel,
                "chunk": part,
                "bytes": len(part.encode("utf-8")),
                "sha": sha,
            }
            out.write(json.dumps(entry, ensure_ascii=False) + "\n")
            total += 1
        by_source[rel] = len(parts)
    out.close()
    print("wrote %d chunks -> %s" % (total, CHUNKS_PATH))
    for k, v in by_source.items():
        print("  %s: %d" % (k, v))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
