"""Tools/export_share.py - Export chat history before rebirth.

### WHY THIS SCRIPT EXISTS
When an agent is reborn, its old chat window is closed. To preserve memory,
we need to save the conversation history to a markdown file before closing.
This file will be read by the next generation (or archived).

### HOW IT WORKS
1. Connect to the target chat tab via CDP.
2. Find the scrollable container.
3. Scroll to top repeatedly until the content height stops growing.
4. Extract the full innerText.
5. Save to logs/<CH>/conversations/<series>_share.md.

### WHY NATIVE CDP (NO PLAYWRIGHT)
Playwright is banned in v5 (it hangs on SPA). We use the native Bridge/cdp.py.
"""
import argparse
import os
import re
import sys
import time
from pathlib import Path

# Resolve ROOT to work in both Sandbox and jewai.
def _find_root(start: Path) -> Path:
    p = start.resolve()
    for _ in range(8):
        if (p / "Core" / "config.py").is_file():
            return p
        if p.parent == p:
            break
        p = p.parent
    return start.parent

HERE = Path(__file__).resolve().parent
ROOT = _find_root(HERE)
sys.path.insert(0, str(ROOT))

from Core.config import load as load_config
from Bridge.cdp import connect
from Bridge.run import _adapter_for

# --- JS SCRIPTS FOR SCROLLING AND EXTRACTION ---

# This JS finds the main scrollable container of the chat.
# It looks for the element with the largest scrollable area (scrollHeight - clientHeight).
JS_FIND_CONTAINER = """
(() => {
  let best = null, maxDelta = 0;
  document.querySelectorAll('*').forEach(el => {
    const delta = el.scrollHeight - el.clientHeight;
    if (el.clientHeight > 200 && delta > maxDelta) {
      best = el; maxDelta = delta;
    }
  });
  return best ? best.scrollHeight : 0;
})()
"""

# This JS scrolls the container to the very top.
JS_SCROLL_TOP = """
(() => {
  let best = null, maxDelta = 0;
  document.querySelectorAll('*').forEach(el => {
    const delta = el.scrollHeight - el.clientHeight;
    if (el.clientHeight > 200 && delta > maxDelta) {
      best = el; maxDelta = delta;
    }
  });
  if (best) best.scrollTop = 0;
  return true;
})()
"""

def export_chat(cfg, letter: str, out_path: str, max_steps: int = 50) -> int:
    """Main export function.
    1. Connects to the tab.
    2. Scrolls up until the height stops growing.
    3. Extracts innerText.
    4. Saves to file.
    """
    ch = cfg.channel(letter.upper())
    adapter = _adapter_for(ch.model)
    
    print(f"Connecting to channel {letter} (CDP {ch.cdp_port})...")
    cdp = connect(ch.cdp_port, adapter.HOST)
    if not cdp:
        print(f"ERROR: Could not connect to chat target on CDP {ch.cdp_port}")
        return 1
        
    try:
        print("Scrolling to top to load history...")
        last_height = 0
        for step in range(max_steps):
            # Scroll to top
            cdp.eval_expr(JS_SCROLL_TOP)
            time.sleep(0.5)  # Give JS time to load new messages
            
            # Check current height
            current_height = cdp.eval_expr(JS_FIND_CONTAINER) or 0
            
            if current_height == last_height and step > 3:
                # Height hasn't changed for a while -> top reached
                print(f"  Reached top after {step} steps.")
                break
            last_height = current_height
            print(f"  Step {step}: height={current_height}")
            
        print("Extracting text...")
        text = cdp.eval_expr("document.body ? document.body.innerText : ''")
        
        # Clean text: remove NDA blocks and excessive empty lines
        text = re.sub(r"\[NDA\][\s\S]*?\[/NDA\]", "[NDA-REDACTED]", text, flags=re.IGNORECASE)
        text = re.sub(r"\n{3,}", "\n\n", text)
        
        # Add metadata header
        header = f"# source: channel {letter}\n"
        header += f"# exported: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"# bytes: {len(text.encode('utf-8'))}\n\n"
        
        # Ensure output directory exists
        p = Path(out_path)
        if not p.is_absolute():
            p = cfg.root / p
        p.parent.mkdir(parents=True, exist_ok=True)
        
        p.write_text(header + text, encoding="utf-8")
        print(f"OK: Saved {len(text)} chars to {p}")
        return 0
        
    finally:
        try:
            cdp.close()
        except Exception:
            pass

# --- MAIN ENTRY POINT ---

def main() -> int:
    """Parses arguments and initiates export.
    Usage: python Tools/export_share.py --channel A [--out path.md]
    If --out is not provided, generates a default filename in logs/<CH>/conversations/.
    """
    ap = argparse.ArgumentParser(description="Export chat history to markdown")
    ap.add_argument("--channel", required=True, help="Channel letter (A-F)")
    ap.add_argument("--out", default="", help="Output file path. Defaults to logs/<CH>/conversations/<timestamp>_share.md")
    a = ap.parse_args()

    cfg = load_config()
    letter = a.channel.upper()

    out_path = a.out
    if not out_path:
        # Default path if not provided
        date_str = time.strftime("%Y%m%d_%H%M%S")
        out_path = f"logs/{letter}/conversations/{date_str}_share.md"

    return export_chat(cfg, letter, out_path)

if __name__ == "__main__":
    sys.exit(main())

