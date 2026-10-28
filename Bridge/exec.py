"""Bridge/exec.py - block parser, replay-guard, ops (read/write/run/list/mkdir/hash).

Contract per AUDIT section 29:
- Watermark (last_processed_id) + content hash persisted in file, not memory.
- Block with id <= watermark -> SKIP (stale), no exec.
- Same id with different hash -> WARN to stale_blocks.log + SKIP.
- Only last N assistant messages scanned (adapter enforces SCAN_LAST_MSGS).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


H = "#" * 3
BEGIN = H + "BEGIN" + H
CONTENT = H + "CONTENT" + H
END = H + "END" + H

ID_RE = re.compile(r"^[A-Z]{4}[0-9]{4}$")


@dataclass
class Block:
    id: str
    op: str
    path: str | None = None
    cmd: str | None = None
    cwd: str | None = None
    timeout: int = 60
    content: str = ""

    def content_hash(self) -> str:
        h = hashlib.sha256()
        h.update(self.id.encode())
        h.update(b"\x00")
        h.update(self.op.encode())
        h.update(b"\x00")
        h.update((self.path or "").encode())
        h.update(b"\x00")
        h.update((self.cmd or "").encode())
        h.update(b"\x00")
        h.update(self.content.encode())
        return h.hexdigest()


def parse_blocks(text: str) -> list[Block]:
    out: list[Block] = []
    if not text or BEGIN not in text:
        return out
    pat = re.compile(re.escape(BEGIN) + r"(.*?)" + re.escape(END), re.DOTALL)
    for m in pat.finditer(text):
        inner = m.group(1)
        sep_idx = inner.find(CONTENT)
        if sep_idx >= 0:
            headers = inner[:sep_idx]
            body = inner[sep_idx + len(CONTENT):]
            body = body.lstrip("\r\n").rstrip()
        else:
            headers = inner
            body = ""
        h: dict[str, str] = {}
        for line in headers.splitlines():
            i = line.find(":")
            if i < 0:
                continue
            k = line[:i].strip().lower()
            v = line[i + 1:].strip()
            if k:
                h[k] = v
        bid = h.get("id", "")
        bop = h.get("op", "")
        if not ID_RE.match(bid):
            continue
        if not bop:
            continue
        try:
            to = int(h.get("timeout", "60") or 60)
        except Exception:
            to = 60
        out.append(Block(
            id=bid, op=bop,
            path=h.get("path"), cmd=h.get("cmd"), cwd=h.get("cwd"),
            timeout=to, content=body,
        ))
    return out


class Ledger:
    """Watermark + hashes. Persisted in file, not memory."""

    def __init__(self, ledger_path: Path, stale_log_path: Path, max_entries: int = 500):
        self.path = ledger_path
        self.stale_log = stale_log_path
        self.max_entries = max_entries
        self.watermark: str = ""
        self.hashes: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.watermark = str(data.get("watermark", ""))
            self.hashes = dict(data.get("hashes", {}))
        except Exception:
            self.watermark = ""
            self.hashes = {}

    def _save(self) -> None:
        if len(self.hashes) > self.max_entries:
            keys = sorted(self.hashes.keys())
            for k in keys[: len(keys) - self.max_entries]:
                del self.hashes[k]
        data = {"watermark": self.watermark, "hashes": self.hashes}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, self.path)

    def _stale(self, block: Block, reason: str) -> None:
        try:
            self.stale_log.parent.mkdir(parents=True, exist_ok=True)
            line = "%s\t%s\t%s\t%s\t%s\n" % (
                time.strftime("%Y-%m-%dT%H:%M:%S"),
                block.id, block.op, block.content_hash()[:16], reason,
            )
            with self.stale_log.open("a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

    def check(self, block: Block) -> tuple[bool, str]:
        # Order: dup -> collision -> watermark. More specific reasons first.
        prev = self.hashes.get(block.id)
        if prev is not None:
            if prev == block.content_hash():
                self._stale(block, "dup_same_hash")
                return False, "stale: duplicate"
            self._stale(block, "id_collision_diff_hash")
            return False, "stale: id_collision"
        if self.watermark and block.id <= self.watermark:
            self._stale(block, "below_watermark")
            return False, "stale: below_watermark"
        return True, "ok"

    def commit(self, block: Block) -> None:
        self.hashes[block.id] = block.content_hash()
        if not self.watermark or block.id > self.watermark:
            self.watermark = block.id
        self._save()


class OpError(RuntimeError):
    pass


def safe_path(root: Path, rel: str) -> Path:
    if not rel:
        raise OpError("empty path")
    p = (root / rel).resolve()
    root_r = root.resolve()
    if p != root_r and root_r not in p.parents:
        raise OpError("escape: " + rel)
    return p


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _nw_flags() -> int:
    if sys.platform != "win32":
        return 0
    return subprocess.CREATE_NO_WINDOW


def op_read(root: Path, b: Block) -> dict[str, Any]:
    p = safe_path(root, b.path or "")
    text = p.read_text(encoding="utf-8", errors="replace")
    return {"ok": True, "path": str(p), "content": text,
            "bytes": len(text.encode("utf-8"))}


def op_write(root: Path, b: Block) -> dict[str, Any]:
    p = safe_path(root, b.path or "")
    p.parent.mkdir(parents=True, exist_ok=True)
    body = b.content
    if p.exists() and p.is_file():
        try:
            if p.read_text(encoding="utf-8") == body:
                return {"ok": True, "path": str(p), "unchanged": True,
                        "bytes": len(body.encode("utf-8"))}
        except Exception:
            pass
    p.write_text(body, encoding="utf-8")
    return {"ok": True, "path": str(p), "bytes": len(body.encode("utf-8")),
            "sha256": _sha256(p)}


def op_list(root: Path, b: Block) -> dict[str, Any]:
    p = safe_path(root, b.path or ".")
    items = []
    for x in sorted(p.iterdir()):
        try:
            items.append({"name": x.name, "is_dir": x.is_dir(),
                          "size": x.stat().st_size if x.is_file() else 0})
        except Exception:
            pass
    return {"ok": True, "path": str(p), "items": items}


def op_mkdir(root: Path, b: Block) -> dict[str, Any]:
    p = safe_path(root, b.path or "")
    p.mkdir(parents=True, exist_ok=True)
    return {"ok": True, "path": str(p)}


def op_hash(root: Path, b: Block) -> dict[str, Any]:
    p = safe_path(root, b.path or "")
    if not p.exists():
        return {"ok": False, "error": "not found"}
    return {"ok": True, "sha256": _sha256(p), "bytes": p.stat().st_size}


def op_run(root: Path, b: Block) -> dict[str, Any]:
    if not b.cmd:
        return {"ok": False, "error": "no cmd"}
    cwd = safe_path(root, b.cwd) if b.cwd else root
    t0 = time.time()
    try:
        r = subprocess.run(b.cmd, shell=True, cwd=str(cwd),
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           timeout=max(1, b.timeout),
                           creationflags=_nw_flags())
        return {"ok": r.returncode == 0, "code": r.returncode,
                "stdout": r.stdout or "", "stderr": r.stderr or "",
                "elapsed": round(time.time() - t0, 2)}
    except subprocess.TimeoutExpired:
        return {"ok": False, "code": -1, "stdout": "", "stderr": "TIMEOUT",
                "elapsed": round(time.time() - t0, 2)}


OPS = {
    "read": op_read,
    "write": op_write,
    "list": op_list,
    "mkdir": op_mkdir,
    "hash": op_hash,
    "run": op_run,
}


def execute(root: Path, block: Block) -> dict[str, Any]:
    fn = OPS.get(block.op)
    if not fn:
        return {"ok": False, "error": "unknown op " + block.op}
    try:
        return fn(root, block)
    except OpError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__ + ": " + str(e)}
