"""CSS fixture checks, not a live-browser test. Requires beautifulsoup4 and soupsieve."""
import json
import unittest
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
CFG = json.loads((ROOT / "Adapters/perplexity_selectors.json").read_text(encoding="utf-8"))
HTML = """<main>
<div class="scrollable-container"><div class="max-w-threadContentWidth">
<div data-message-bubble="right"><div data-renderer="lm">User command</div></div>
<div class="prose" data-renderer="lm"><pre>Assistant command</pre></div>
<aside><div class="prose" data-renderer="lm">Source text</div></aside>
<div data-message-bubble="right"><div class="prose" data-renderer="lm">User quote</div></div>
</div></div>
<div class="prose" data-renderer="lm">Outside conversation</div>
<div data-lexical-editor="true" contenteditable="true">draft</div>
</main>"""

class Tests(unittest.TestCase):
    def setUp(self): self.soup = BeautifulSoup(HTML,"html.parser")
    def excluded(self, el):
        import soupsieve
        return any(soupsieve.match(CFG["exclude"], n) for n in [el,*el.parents] if getattr(n,"name",None))
    def test_lexical_without_old_id(self):
        self.assertIsNotNone(self.soup.select_one(CFG["inputs"][0]))
        self.assertIsNone(self.soup.select_one("#ask-input"))
    def test_assistant_only_inside_conversation(self):
        found=[]
        for root in self.soup.select(CFG["container"]):
            found.extend(el for el in root.select(CFG["answer"]) if not self.excluded(el))
        self.assertEqual([el.get_text() for el in found],["Assistant command"])
    def test_no_generic_prose_fallback(self):
        soup=BeautifulSoup('<div class="prose">unknown text</div>',"html.parser")
        self.assertEqual(soup.select(CFG["answer"]),[])
    def test_legacy_textarea(self):
        soup=BeautifulSoup('<textarea id="ask-input"></textarea>',"html.parser")
        self.assertIsNotNone(soup.select_one(CFG["inputs"][-1]))
    def test_readonly_textarea_excluded(self):
        soup=BeautifulSoup('<textarea id="ask-input" readonly></textarea>',"html.parser")
        self.assertIsNone(soup.select_one(CFG["inputs"][-1]))
    def test_snapshot_has_no_unresolved_config_at_runtime(self):
        text=(ROOT/"Adapters/perplexity_dom.js").read_text(encoding="utf-8")
        self.assertEqual(text.count("__JEWAI_SELECTORS__"),1)
        self.assertNotIn("__JEWAI_SELECTORS__",text.replace("__JEWAI_SELECTORS__",json.dumps(CFG)))

if __name__=="__main__": unittest.main(verbosity=2)
