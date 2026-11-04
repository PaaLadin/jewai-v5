import os, sys, time, subprocess, json, shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))

# 1. Check compile
r = subprocess.run([sys.executable, '-m', 'py_compile', str(HERE / 'guard.py')],
                   capture_output=True, text=True)
print('compile:', r.returncode == 0)
if r.returncode != 0:
    print(r.stderr)
    sys.exit(1)

# 2. Setup temp root
T = HERE / ('_tg_' + str(int(time.time())))
(T / 'logs' / 'guard').mkdir(parents=True)
(T / 'Tools').mkdir()
shutil.copy2(HERE / 'guard.py', T / 'Tools' / 'guard.py')
# dummy kick.py to verify call
(T / 'Tools' / 'kick.py').write_text(
    'import sys\n'
    'open("C:/Jeho/Sandbox/A/_test_guard_kick.txt", "a").write("kicked " + " ".join(sys.argv[1:]) + "\\n")\n'
    'sys.exit(0)\n', encoding='utf-8')

cfg = {
    'root': str(T), 'bind': '127.0.0.1', 'chat_port': 18670, 'doh_proxy_port': 19899,
    'letters': ['A','B'], 
    'channels': {
        'A': {'name': 'T', 'agent': 19999, 'cdp': 19998, 'prefix': 'AAAA', 'extension': 'e', 'model': 'deepseek'},
        'B': {'name': 'U', 'agent': 19997, 'cdp': 19997, 'prefix': 'BBAA', 'extension': 'e', 'model': 'deepseek'}
    },
    'thresholds': {}, 'timeouts': {}, 'version': 't'
}
(T / 'config.json').write_text(json.dumps(cfg), encoding='utf-8')
os.environ['JEWAI_CONFIG'] = str(T / 'config.json')

# We need to run guard.py as a module from T/root
env = os.environ.copy()
env['PYTHONPATH'] = str(T)

guard_py = str(T / 'Tools' / 'guard.py')
kick_file = HERE / '_test_guard_kick.txt'

# 3. Test DONE path (no kick should happen)
if kick_file.exists(): kick_file.unlink()
print('test DONE path...')
# arm with 2 sec timeout, then immediately call done
subprocess.run([sys.executable, guard_py, 'start', '--target', '19998', '--timeout', '2'], env=env, check=True, capture_output=True)
subprocess.run([sys.executable, guard_py, 'done'], env=env, check=True, capture_output=True)
time.sleep(3) # wait for checker to finish
if not kick_file.exists():
    print('DONE path PASS: no kick')
else:
    print('DONE path FAIL: kick happened')

# 4. Test ALERT path (kick should happen)
if kick_file.exists(): kick_file.unlink()
print('test ALERT path...')
# arm with 1 sec timeout, no done
subprocess.run([sys.executable, guard_py, 'start', '--target', '19998', '--timeout', '1'], env=env, check=True, capture_output=True)
time.sleep(2.5) # wait for checker to finish and kick
if kick_file.exists():
    content = kick_file.read_text(encoding='utf-8')
    if '--to B' in content and '[GUARD-ALERT]' in content:
        print('ALERT path PASS: kicked B')
    else:
        print('ALERT path FAIL: wrong kick content', content)
else:
    print('ALERT path FAIL: no kick')

print('TEST DONE')