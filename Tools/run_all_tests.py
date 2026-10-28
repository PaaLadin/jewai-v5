"""Run all v5 tests, produce summary. Exit 0 if all pass, 1 otherwise.

Usage: python C:/DeepSeek/sandbox/_v5/run_all_tests.py
"""
import subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TESTS_DIR = HERE / "tests"
OUT = HERE.parent / "logs" / "runtime" / "_v5_all_tests.txt"
OUT.parent.mkdir(parents=True, exist_ok=True)

TESTS = [
    ('test_imports.py', 'module imports'),
    ('test_smoke.py', 'parse/ledger/ops'),
    ('test_daemon.py', 'daemon cycle (fakes)'),
    ('test_mainframe_8671.py', 'mainframe routes on 8671'),
    ('test_rebirth.py', 'series/gate/neighbor'),
    ('test_f5.py', 'llm/mail/rag + routes'),
    ('test_edge_cases.py', 'parser/Ledger edge cases'),
    ('test_cdp_read_launcher.py', 'cdp/read/launcher'),
    ('test_f5_configured.py', 'llm/mail configured'),
    ('test_daemon_timing.py', 'daemon timing gates'),
    ('test_server_subprocess.py', 'server subprocess deploy'),
    ('test_adapters_qwen_alice.py', 'qwen/alice adapters'),
    ('test_run_entrypoint.py', 'run.py entrypoint'),
    ('test_boot.py', 'boot orchestrator'),
    ('test_ext_agent.py', 'extension agent.py'),
    ('test_council.py', 'council chat/personal'),
    ('test_mainframe_ext.py', 'mainframe extended (status/health/chat/svc)'),
    ('test_launchpad.py', 'launchpad status/boot/stop'),
    ('test_fs.py', 'fs raw file serving'),
    ('test_cycle.py', 'rebirth CDP cycle'),
    ('test_doh_proxy.py', 'doh proxy cache+connect'),
]

lines = []
total_ok = 0
total_fail = 0
t0 = time.time()
for fname, label in TESTS:
    p = (TESTS_DIR / fname) if (TESTS_DIR / fname).exists() else (HERE / fname)
    if not p.exists():
        lines.append('MISSING %s' % fname)
        total_fail += 1
        continue
    r = subprocess.run([sys.executable, str(p)], capture_output=True, text=True,
                       timeout=120, cwd=str(HERE))
    status = 'PASS' if r.returncode == 0 else 'FAIL'
    if r.returncode == 0:
        total_ok += 1
    else:
        total_fail += 1
    lines.append('%s %-32s %s' % (status, fname, label))
    if r.returncode != 0:
        # capture tail of stdout/stderr for diagnosis
        tail = ((r.stdout or '') + (r.stderr or ''))[-400:]
        lines.append('  tail: %r' % tail)

elapsed = round(time.time() - t0, 1)
lines.append('')
lines.append('--- %d/%d pass, %d fail, %ss ---' % (total_ok, len(TESTS), total_fail, elapsed))
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE %s' % OUT)
sys.exit(0 if total_fail == 0 else 1)