"""Offline tests; fake CDP, stub parser, no live website validation."""
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from Adapters.perplexity import Perplexity
from Adapters.registry import choices, provider


class FakeCDP:
    def __init__(self):
        self.s = dict(url="https://www.perplexity.ai/search/test", input=True,
                      draft="", busy=False, supported=True, answers=["answer"])
        self.calls = []

    def eval_expr(self, expr):
        return True if "el.focus()" in expr else dict(self.s)

    def call(self, method, params):
        self.calls.append((method, params))
        if method == "Input.insertText":
            self.s["draft"] = params["text"]
        if method == "Input.dispatchKeyEvent" and params["type"] == "keyUp":
            self.s["draft"] = ""


class Tests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.a = Perplexity(clock=lambda: self.now, sleep=lambda _: None)
        self.c = FakeCDP()
        parser = lambda text: [types.SimpleNamespace(id="GGAA0001")]
        p = patch.dict(sys.modules, {"Bridge.exec": types.SimpleNamespace(parse_blocks=parser)})
        p.start()
        self.addCleanup(p.stop)

    def test_registry(self):
        self.assertEqual(len(choices()), 4)
        self.assertTrue(provider(" Perplexity ")["experimental"])
        with self.assertRaises(ValueError):
            provider("typo")

    def test_wrong_host(self):
        self.c.s["url"] = "https://www.perplexity.ai.attacker.invalid/"
        with self.assertRaises(RuntimeError):
            self.a.snapshot(self.c)

    def test_stability(self):
        self.assertEqual(self.a.collect_blocks(self.c), [])
        self.now = 4
        self.assertEqual(len(self.a.collect_blocks(self.c)), 1)
        self.c.s["answers"] = ["changed"]
        self.assertEqual(self.a.collect_blocks(self.c), [])

    def test_fail_closed(self):
        for key, value in [("busy", True), ("input", False), ("supported", False)]:
            c = FakeCDP()
            c.s[key] = value
            self.assertEqual(self.a.collect_blocks(c), [])

    def test_draft_preserved(self):
        self.c.s["draft"] = "operator typing"
        self.assertFalse(self.a.send_text(self.c, "report"))
        self.assertEqual(self.c.calls, [])

    def test_single_submit(self):
        self.assertTrue(self.a.send_text(self.c, "report"))
        self.assertEqual([m for m, p in self.c.calls],
                         ["Input.insertText", "Input.dispatchKeyEvent", "Input.dispatchKeyEvent"])

    def test_assistant_verification(self):
        self.c.s["draft"] = "marker"
        self.assertEqual(self.a.verify_prompt_hits(self.c, ["marker"]), 0)
        self.c.s["answers"] = ["marker"]
        self.assertEqual(self.a.verify_prompt_hits(self.c, ["marker"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
