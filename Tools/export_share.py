"""Tools/export_share.py - экспорт share-страницы DeepSeek через CDP.

Contract (BUG-006, аналог DeepSeek sandbox/export_share.py БЕЗ Playwright):
- Принимает --url (share), --out (md-файл), --port (CDP), --wait, --step, --max_steps.
- Изолированный browser context: Target.createBrowserContext -> Target.createTarget.
  Cookies не передаются, share отдаётся публично, UI рабочего Chrome не трогается.
- Scroll-loop: ищем самый большой скроллируемый контейнер, читаем innerText постранично,
  дедуп по строкам, скроллим на --step до упора/предела шагов.
- NDA: блоки [NDA]...[/NDA] вырезаются в [NDA-REDACTED].
- Header: source, final_url, title, exported, bytes.

Usage:
  python Tools/export_share.py --url <share_url> --out <path.md> --port 9223
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from Bridge.cdp import CDP, CDPError  # noqa: E402


def _browser_ws(port: int) -> str:
    url = "http://127.0.0.1:%d/json/version" % port
    with urllib.request.urlopen(url, timeout=5.0) as r:
        j = json.loads(r.read().decode("utf-8", "replace"))
    return j.get("webSocketDebuggerUrl") or ""


def _attach_page(port: int, target_id: str) -> CDP:
    """Подключиться к target по его webSocketDebuggerUrl из /json/list."""
    url = "http://127.0.0.1:%d/json/list" % port
    with urllib.request.urlopen(url, timeout=5.0) as r:
        targets = json.loads(r.read().decode("utf-8", "replace"))
    for t in targets:
        if t.get("id") == target_id:
            return CDP(t["webSocketDebuggerUrl"], timeout=60.0)
    raise CDPError("target not found in /json/list: %s" % target_id)


_JS_SNAP = "() => document.body ? document.body.innerText : ''"

_JS_TOP = """() => {
  let best=null, bd=0;
  document.querySelectorAll('*').forEach(el => {
    const d = el.scrollHeight - el.clientHeight;
    if (el.clientHeight > 200 && d > bd) { best = el; bd = d; }
  });
  return best ? best.scrollTop : 0;
}"""

_JS_SCROLL_BY = """(n) => {
  let best=null, bd=0;
  document.querySelectorAll('*').forEach(el => {
    const d = el.scrollHeight - el.clientHeight;
    if (el.clientHeight > 200 && d > bd) { best = el; bd = d; }
  });
  if (best) best.scrollTop += n;
  return best ? best.scrollTop : 0;
}"""

_JS_SCROLL_TOP = """() => {
  let best=null, bd=0;
  document.querySelectorAll('*').forEach(el => {
    const d = el.scrollHeight - el.clientHeight;
    if (el.clientHeight > 200 && d > bd) { best = el; bd = d; }
  });
  if (best) best.scrollTop = 0;
  return true;
}"""


def _eval_fn(cdp: CDP, fn_src: str, arg=None):
    """Вызвать arrow-функцию (с необязательным одним аргументом)."""
    if arg is None:
        expr = "(%s)()" % fn_src
    else:
        expr = "(%s)(%s)" % (fn_src, json.dumps(arg))
    return cdp.eval_expr(expr)


def export_share(port: int, share_url: str, out_path: Path,
                 wait: float = 10.0, step: int = 600, max_steps: int = 300) -> dict:
    bws = _browser_ws(port)
    if not bws:
        raise CDPError("no browser websocket on port %d" % port)

    b = CDP(bws, timeout=60.0)
    ctx_id = ""
    tgt_id = ""
    text = ""
    final_url = ""
    title = ""
    try:
        r = b.call("Target.createBrowserContext", {"disposeOnDetach": False})
        ctx_id = (r.get("result") or {}).get("browserContextId") or ""
        if not ctx_id:
            raise CDPError("createBrowserContext returned no id: %r" % r)
        r = b.call("Target.createTarget", {"url": "about:blank", "browserContextId": ctx_id})
        tgt_id = (r.get("result") or {}).get("targetId") or ""
        if not tgt_id:
            raise CDPError("createTarget returned no id: %r" % r)
    finally:
        b.close()

    pg = _attach_page(port, tgt_id)
    try:
        pg.call("Page.enable", {})
        pg.call("Runtime.enable", {})
        pg.call("Page.navigate", {"url": share_url})
        time.sleep(wait)

        try:
            final_url = pg.eval_expr("location.href") or ""
            title = pg.eval_expr("document.title") or ""
        except Exception:
            pass

        seen: set[str] = set()
        ordered: list[str] = []

        def snap() -> None:
            txt = pg.eval_expr(_JS_SNAP) or ""
            for line in txt.split("\n"):
                k = line.strip()
                if not k or k in seen:
                    continue
                seen.add(k)
                ordered.append(line)

        try:
            _eval_fn(pg, _JS_SCROLL_TOP)
        except Exception:
            pass
        time.sleep(1)
        last = -1
        for i in range(max_steps):
            snap()
            try:
                t = _eval_fn(pg, _JS_TOP)
            except Exception:
                t = None
            if t == last and i > 5:
                break
            last = t
            try:
                _eval_fn(pg, _JS_SCROLL_BY, step)
            except Exception:
                pass
            time.sleep(0.4)
        snap()
        text = "\n".join(ordered)
    finally:
        pg.close()
        try:
            b2 = CDP(bws, timeout=30.0)
            try:
                if tgt_id:
                    b2.call("Target.closeTarget", {"targetId": tgt_id})
                if ctx_id:
                    b2.call("Target.disposeBrowserContext", {"browserContextId": ctx_id})
            finally:
                b2.close()
        except Exception:
            pass

    text, n_nda = re.subn(r"\[NDA\][\s\S]*?\[/NDA\]", "[NDA-REDACTED]", text,
                          flags=re.IGNORECASE)
    if n_nda:
        print("NDA blocks redacted: %d" % n_nda)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    header = ("# source: %s\n# final_url: %s\n# title: %s\n# exported: %s\n# bytes: %d\n\n"
              % (share_url, final_url, title,
                 time.strftime("%Y-%m-%d %H:%M:%S"), len(text)))
    out_path.write_text(header + text, encoding="utf-8")
    return {"ok": True, "chars": len(text), "final_url": final_url,
            "bytes": out_path.stat().st_size, "nda": n_nda}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--port", type=int, default=9223)
    ap.add_argument("--wait", type=float, default=10.0)
    ap.add_argument("--step", type=int, default=600)
    ap.add_argument("--max_steps", type=int, default=300)
    a = ap.parse_args()
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    try:
        r = export_share(a.port, a.url, Path(a.out), a.wait, a.step, a.max_steps)
    except Exception as e:
        print("FAIL: %s: %s" % (type(e).__name__, e))
        return 2
    print("OK chars=%d final=%s bytes=%d" % (r["chars"], r["final_url"], r["bytes"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())