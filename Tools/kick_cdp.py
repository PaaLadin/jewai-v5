"""Tools/kick_cdp.py - kick коллеге через CDP напрямую, без bridge_kick2.py.

Причина: bridge_kick2.py на Windows бьёт кириллицу в argv (cp1251).
Здесь текст идёт через json.dumps (ensure_ascii=True), CDP принимает
ASCII-эскейпы, никакой cp1251.

Usage:
  python Tools/kick_cdp.py --port 9222 --text "[C>A] ..."
"""
import argparse, json, sys, time, urllib.request, websocket


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, required=True)
    ap.add_argument('--text', required=True)
    ap.add_argument('--host', default='chat.deepseek.com')
    a = ap.parse_args()

    try:
        ts = json.load(urllib.request.urlopen('http://127.0.0.1:%d/json/list' % a.port, timeout=5))
    except Exception as e:
        print('FAIL: CDP not reachable on %d: %r' % (a.port, e))
        return 2
    chat = next((t for t in ts if t.get('type') == 'page' and a.host in (t.get('url') or '')), None)
    if not chat:
        print('FAIL: no chat on port %d' % a.port)
        return 2

    ws = websocket.create_connection(chat['webSocketDebuggerUrl'], timeout=10)
    _i = [0]
    def call(m, p=None):
        _i[0] += 1; i = _i[0]
        ws.send(json.dumps({'id': i, 'method': m, 'params': p or {}}))
        while True:
            j = json.loads(ws.recv())
            if j.get('id') == i:
                return j
    try:
        call('Runtime.enable')
        ta = call('Runtime.evaluate', {'expression': "(function(){var t=document.querySelector('textarea');return t?t.value:'';})()", 'returnByValue': True})
        ta_v = (ta.get('result') or {}).get('result', {}).get('value') or ''
        if ta_v.strip():
            print('SKIP: textarea busy (len=%d)' % len(ta_v))
            return 3

        fill_js = (
            "(()=>{var t=document.querySelector('textarea');if(!t)return 'NO_TA';t.focus();"
            "var s=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;"
            "s.call(t," + json.dumps(a.text) + ");"
            "if(t._valueTracker)t._valueTracker.setValue('');"
            "t.dispatchEvent(new Event('input',{bubbles:true}));"
            "t.dispatchEvent(new Event('change',{bubbles:true}));"
            "return t.value.length>0?'OK':'EMPTY';})()")
        r = call('Runtime.evaluate', {'expression': fill_js, 'returnByValue': True})
        v = (r.get('result') or {}).get('result', {}).get('value')
        print('fill:', v)
        if v != 'OK':
            return 4
        time.sleep(1.2)
        call('Input.dispatchKeyEvent', {'type':'keyDown','key':'Enter','code':'Enter','windowsVirtualKeyCode':13,'nativeVirtualKeyCode':13})
        time.sleep(0.1)
        call('Input.dispatchKeyEvent', {'type':'keyUp','key':'Enter','code':'Enter','windowsVirtualKeyCode':13,'nativeVirtualKeyCode':13})
        time.sleep(2)
        r = call('Runtime.evaluate', {'expression': "(function(){var t=document.querySelector('textarea');return t?t.value:'';})()", 'returnByValue': True})
        after = (r.get('result') or {}).get('result', {}).get('value') or ''
        print('sent, textarea_after=%d' % len(after))
        return 0 if not after.strip() else 5
    finally:
        ws.close()


if __name__ == '__main__':
    sys.exit(main())