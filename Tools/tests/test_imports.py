"""Smoke test: все модули v5 импортируются без ошибок. Не запускает Chrome/сеть."""
import sys
from pathlib import Path

ROOT = Path(r'C:/JewAI')
sys.path.insert(0, str(ROOT))

results = []

def check(name, fn):
    try:
        fn()
        results.append((name, 'OK', ''))
    except Exception as e:
        results.append((name, 'FAIL', f'{type(e).__name__}: {e}'))

def _core_config():
    from Core.config import load
    cfg = load()
    assert cfg.letters == ('A','B','C','D','E','F'), cfg.letters
    assert cfg.chat_port == 8670, cfg.chat_port
    assert len(cfg.channels) == 6
    assert cfg.channel('A').agent_port == 8666
    assert cfg.channel('F').cdp_port == 9127

def _bridge_cdp():
    from Bridge.cdp import CDPError, list_targets, find_chat, CDP, connect
    assert CDPError
    assert callable(find_chat)

def _bridge_read():
    from Bridge.read import read_text, read_heartbeat, read_textarea, current_url, find_sidepanel

def _bridge_exec():
    from Bridge.exec import Block, parse_blocks, Ledger, execute, safe_path, OpError
    # parse_blocks на пустом
    assert parse_blocks('') == []
    assert parse_blocks('no block here') == []
    # простой блок
    H = '#' * 3
    text = f'{H}BEGIN{H}\nid: AAAA0001\nop: read\npath: x\n{H}END{H}'
    bs = parse_blocks(text)
    assert len(bs) == 1, bs
    assert bs[0].id == 'AAAA0001'
    assert bs[0].op == 'read'
    assert bs[0].path == 'x'

def _bridge_daemon():
    from Bridge.daemon import Daemon, DaemonResult

def _adapters():
    from Adapters.deepseek import DeepSeek
    assert DeepSeek.HOST == 'chat.deepseek.com'
    assert DeepSeek.TEXTAREA_SELECTOR == 'textarea'

def _tools_launcher():
    from Tools.launcher import wait_cdp, launch, _chrome_exe
    assert callable(wait_cdp)

check('Core.config', _core_config)
check('Bridge.cdp', _bridge_cdp)
check('Bridge.read', _bridge_read)
check('Bridge.exec', _bridge_exec)
check('Bridge.daemon', _bridge_daemon)
check('Adapters.deepseek', _adapters)
check('Tools.launcher', _tools_launcher)

out = Path(__file__).resolve().parent.parent.parent / Path('logs/runtime/_v5_imports.txt')
lines = []
ok_n = 0
for name, status, err in results:
    lines.append(f'{status:5} {name:25} {err}')
    if status == 'OK':
        ok_n += 1
lines.append(f'--- {ok_n}/{len(results)} OK ---')
out.write_text('\n'.join(lines), encoding='utf-8')
print(f'WROTE {out} ({ok_n}/{len(results)} OK)')