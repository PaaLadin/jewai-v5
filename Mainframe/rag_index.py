"""RAG Index — SQLite FTS5 для чанков RAG-документов.

Использование из кода:
    from Mainframe import rag_index
    rag_index.build_index()        # пересобрать индекс
    rag_index.search("BUG-017")    # найти чанки
    rag_index.stats()              # {chunks: N, db_size: N}

DB: Profiles/A/rag_index.db
"""
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / "RAG"
DB_PATH = ROOT / "Profiles" / "A" / "rag_index.db"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


def _chunks_from_text(text, source):
    """Нарезает текст на чанки с перекрытием. Возвращает [(idx, content)]."""
    out = []
    text = text.strip()
    if not text:
        return out
    # Пробуем резать по абзацам/заголовкам
    paragraphs = []
    current = ""
    for line in text.split("\n"):
        if line.startswith("#") and current.strip():
            paragraphs.append(current.strip())
            current = line + "\n"
        else:
            current += line + "\n"
    if current.strip():
        paragraphs.append(current.strip())

    # Склеиваем абзацы в чанки, пока не достигнем CHUNK_SIZE
    buf = ""
    idx = 0
    for para in paragraphs:
        if len(buf) + len(para) > CHUNK_SIZE and buf:
            out.append((idx, buf.strip()))
            idx += 1
            # перекрытие: берём хвост предыдущего чанка
            tail = buf[-CHUNK_OVERLAP:] if len(buf) > CHUNK_OVERLAP else buf
            buf = tail + "\n\n" + para
        else:
            buf += ("\n\n" if buf else "") + para
    if buf.strip():
        out.append((idx, buf.strip()))

    # Если получился один огромный чанк (документ без абзацев) — режем грубо
    final = []
    for i, (_, chunk) in enumerate(out):
        if len(chunk) <= CHUNK_SIZE * 1.5:
            final.append((i, chunk))
        else:
            for j in range(0, len(chunk), CHUNK_SIZE - CHUNK_OVERLAP):
                piece = chunk[j:j+CHUNK_SIZE]
                if piece.strip():
                    final.append((len(final), piece))
    return [(i, c) for i, (_, c) in enumerate(final)]


def build_index():
    """Читает все RAG/**/*.md, режет на чанки, пишет в SQLite FTS5. Возвращает dict."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Удаляем старую базу
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("CREATE VIRTUAL TABLE chunks USING fts5(source, chunk_idx, content)")
        conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        
        total_chunks = 0
        total_files = 0
        
        if RAG_DIR.exists():
            for md_file in sorted(RAG_DIR.rglob("*.md")):
                try:
                    text = md_file.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                rel = str(md_file.relative_to(ROOT)).replace("\\", "/")
                chunks = _chunks_from_text(text, rel)
                for idx, content in chunks:
                    conn.execute(
                        "INSERT INTO chunks (source, chunk_idx, content) VALUES (?, ?, ?)",
                        (rel, idx, content)
                    )
                    total_chunks += 1
                total_files += 1
        
        conn.execute("INSERT INTO meta (key, value) VALUES (?, ?)", ("files", str(total_files)))
        conn.execute("INSERT INTO meta (key, value) VALUES (?, ?)", ("chunks", str(total_chunks)))
        conn.execute("INSERT INTO meta (key, value) VALUES (?, ?)", ("built_at", str(os.path.getmtime(DB_PATH) if DB_PATH.exists() else 0)))
        conn.commit()
    finally:
        conn.close()

    return {"ok": True, "files": total_files, "chunks": total_chunks, "db_path": str(DB_PATH), "db_size": DB_PATH.stat().st_size if DB_PATH.exists() else 0}


def search(query, limit=5):
    """Поиск по FTS5. Возвращает список чанков."""
    if not DB_PATH.exists():
        return {"ok": False, "error": "index not built, call index_rag first"}
    
    conn = sqlite3.connect(str(DB_PATH))
    try:
        # FTS5: санитизация — убираем спецсимволы (,-,_,*,",(),:)
        import re as _re
        cleaned = _re.sub(r'[\-\_\*\"\(\)\:\,\.]', ' ', query)
        cleaned = ' '.join(cleaned.split())  # убираем лишние пробелы
        # Если в запросе несколько слов — ищем по OR (любое из слов)
        words = cleaned.split()
        if not words:
            return {"ok": False, "error": "empty query"}
        fts_q = ' OR '.join(f'"{w}"' for w in words if w)
        
        rows = []
        try:
            rows = conn.execute(
                "SELECT source, chunk_idx, content FROM chunks WHERE chunks MATCH ? ORDER BY rank LIMIT ?",
                (fts_q, limit)
            ).fetchall()
        except sqlite3.OperationalError:
            pass
        
        # Fallback на LIKE, если FTS не нашёл
        if not rows:
            like_pat = f"%{query}%"
            rows = conn.execute(
                "SELECT source, chunk_idx, content FROM chunks WHERE content LIKE ? LIMIT ?",
                (like_pat, limit)
            ).fetchall()
        
        results = [
            {"source": r[0], "chunk_idx": r[1], "content": r[2][:500]}
            for r in rows
        ]
        return {"ok": True, "query": query, "count": len(results), "results": results}
    finally:
        conn.close()


def stats():
    """Возвращает статистику индекса."""
    if not DB_PATH.exists():
        return {"ok": False, "error": "no index", "db_path": str(DB_PATH)}
    
    conn = sqlite3.connect(str(DB_PATH))
    try:
        chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        meta = {r[0]: r[1] for r in conn.execute("SELECT key, value FROM meta").fetchall()}
        return {
            "ok": True,
            "db_path": str(DB_PATH),
            "db_size": DB_PATH.stat().st_size,
            "chunks": chunks,
            "meta": meta,
        }
    finally:
        conn.close()