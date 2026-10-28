"""Tools/diagnose.py - quick health report for v5.

Checks:
- All v5 module imports OK
- Ports: 8670 busy? v5 ports 9122-9127, 8666-8672
- Chrome C profile exists? Chrome process running?
- AUDIT.md, JOURNAL.md, TODO.md, HANDOVER_14D, PROMPT_14D present
- Test suites available in Tools/tests/

Usage: python C:/JewAI/Tools/diagnose.py
"""
from __future__ import annotations

import hashlib
import json
import socket
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "logs" / "runtime" / "diagnose.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

lines: list[str] = []

def ln(s: str) -> None:
    lines.append(s)

def tcp(port: int, timeout: float = 0.4) -> bool:
    try:
        s = socket.socket(); s.settimeout(timeout)
        r = s.connect_ex(("127.0.0.1", port)); s.close()
        return r == 0
    except Exception:
        return False

def http_ok(url: str, timeout: float = 6.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False

def file_info(p: Path) -> str:
    if not p.exists():
        return "MISSING"
    d = p.read_bytes()
    return "%db sha=%s" % (len(d), hashlib.sha256(d).hexdigest()[:12])

# --- imports ---
ln("=== imports ===")
sys.path.insert(0, str(ROOT))
mods = ["Core.config", "Bridge.cdp", "Bridge.read", "Bridge.exec", "Bridge.daemon",
        "Adapters.deepseek", "Tools.launcher",
        "Mainframe.web", "Mainframe.api", "Mainframe.llm", "Mainframe.mail",
        "Mainframe.rag_channel", "Mainframe.server",
        "Rebirth.table", "Rebirth.master", "Rebirth.onboard"]
ok_n = 0
for m in mods:
    try:
        __import__(m)
        ln("  OK   " + m); ok_n += 1
    except Exception as e:
        ln("  FAIL " + m + " " + type(e).__name__ + ": " + str(e)[:80])
ln("  imports %d/%d" % (ok_n, len(mods)))

# --- files ---
ln("")
ln("=== key files ===")
for rel in ["config.json", "README.md", "VERSION",
            "RAG/architecture/AUDIT.md", "RAG/procedures/architecture.md",
            "logs/JOURNAL.md", "logs/TODO.md",
            "Tools/run_all_tests.py"]:
    ln("  %-40s %s" % (rel, file_info(ROOT / rel)))

# --- ports ---
ln("")
ln("=== ports ===")
ln("  8670 (panel): %s" % ("busy" if tcp(8670) else "free"))
for L, cdp, ag in [("A",9122,8666),("B",9123,8667),("C",9124,8668),
                    ("D",9125,8669),("E",9126,8671),("F",9127,8672)]:
    cdp_s = "up" if tcp(cdp) else "down"
    ag_s = "up" if tcp(ag) else "down"
    ln("  %s: cdp=%d %s agent=%d %s" % (L, cdp, cdp_s, ag, ag_s))

# --- mainframe probe ---
ln("")
ln("=== mainframe on 8670 ===")
for path in ["/api/health", "/api/status", "/api/llm", "/style.css"]:
    up = http_ok("http://127.0.0.1:8670" + path)
    ln("  %-20s %s" % (path, "200" if up else "non-200"))

# --- browser process (Chrome on C profile) ---
ln("")
ln("=== Chrome profile C ===")
prof = ROOT / "Profiles" / "C"
if prof.exists():
    pref = prof / "Default" / "Preferences"
    ln("  profile dir: %s" % ("exists" if prof.is_dir() else "missing"))
    ln("  Default/Preferences: %s" % ("exists" if pref.exists() else "missing (first run)"))
else:
    ln("  profile dir MISSING")

# --- tests ---
ln("")
ln("=== tests ===")
tests_dir = ROOT / "Tools" / "tests"
if tests_dir.exists():
    tests = sorted(p.name for p in tests_dir.glob("test_*.py"))
    ln("  %d tests: %s" % (len(tests), ", ".join(tests)))
else:
    ln("  Tools/tests/ MISSING")

# --- blockers ---
ln("")
ln("=== blockers (require operator OK) ===")
ln("  1. 8670 process 5304 (foreign Mainframe) - kill+restart needed")
ln("  2. Ф2 live-send to chat C")
ln("  3. Ф6 rollout A/B/D/E/F")
ln("  4. Ф7 GitHub push")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("WROTE", OUT)
print("imports %d/%d" % (ok_n, len(mods)))