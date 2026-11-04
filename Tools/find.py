"""sandbox/find.py - fast tree search for JewAI v5.

Replaces rglob / Get-ChildItem -Recurse, which hang on Chrome profiles.
Port of DeepSeek sandbox/find.py (AUDIT section 9).

Usage:
  python Tools/find.py "*.py"
  python Tools/find.py "pattern" --text
  python Tools/find.py "*.md" --dir rag
  python Tools/find.py "*.py" --dir C:\\Jeho\\RAG

Excludes by default: .git, runtime, models, chrome-*-data, backups,
node_modules, .venv, __pycache__, .pytest_cache, Profiles, logs/runtime.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_EXCLUDES = (
    ".git", "runtime", "models", "backups", "node_modules", ".venv",
    "__pycache__", ".pytest_cache", "Profiles", "chrome-for-testing",
    "chrome-data", "chrome_data",
)

MAX_HITS = 100
MAX_LINE = 150


def _is_excluded(path: Path, excludes: tuple) -> bool:
    parts = {p.lower() for p in path.parts}
    for ex in excludes:
        if ex.lower() in parts:
            return True
    return False


def _iter_files(base: Path, excludes: tuple):
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if not _is_excluded(Path(d), excludes)]
        for fn in filenames:
            p = Path(dirpath) / fn
            if not _is_excluded(p, excludes):
                yield p


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def search_by_name(base: Path, pattern: str, excludes: tuple) -> list:
    hits = []
    for p in _iter_files(base, excludes):
        if fnmatch.fnmatch(p.name, pattern):
            hits.append(f"{_rel(p)}")
            if len(hits) >= MAX_HITS:
                break
    return hits


def search_by_text(base: Path, needle: str, excludes: tuple) -> list:
    hits = []
    needle_l = needle.lower()
    for p in _iter_files(base, excludes):
        if len(hits) >= MAX_HITS:
            break
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, 1):
                    if needle_l in line.lower():
                        text = line.strip()[:MAX_LINE]
                        hits.append(f"{_rel(p)}:{i}: {text}")
                        if len(hits) >= MAX_HITS:
                            break
        except Exception:
            continue
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern", help="name glob or text substring")
    ap.add_argument("--text", action="store_true", help="search file contents")
    ap.add_argument("--dir", default="", help="base directory (default: project root)")
    ap.add_argument("--exclude", default="", help="extra exclude, comma-separated")
    a = ap.parse_args()

    base = Path(a.dir).resolve() if a.dir else ROOT
    if not base.exists():
        print(f"error: not found: {base}")
        return 2

    excludes = DEFAULT_EXCLUDES
    if a.exclude:
        excludes = excludes + tuple(x.strip() for x in a.exclude.split(",") if x.strip())

    if a.text:
        hits = search_by_text(base, a.pattern, excludes)
    else:
        hits = search_by_name(base, a.pattern, excludes)

    for h in hits:
        print(h)
    print(f"--- hits={len(hits)} ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())