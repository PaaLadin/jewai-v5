"""Offline provider tests: temporary files, fake browser; no live channels."""
import sys, tempfile, types, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from Bridge import provider_switch as sw

class Config:
    def __init__(self,root): self.root=Path(root)
    def path(self,*p): return self.root.joinpath(*p)
    def channel_path(self,ch,*p): return self.path("Profiles",ch,*p)
    def channel(self,ch):
        d=sw.read(self.path("config.json"))["channels"][ch]
        return types.SimpleNamespace(model=d["model"],cdp_port=d["cdp"])

class Tests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.c=Config(t.name)
        sw.write(self.c.path("config.json"),{"channels":{
            "A":{"model":"deepseek","cdp":9122},"G":{"model":"qwen","cdp":9128}}})
        sw.write(self.c.channel_path("A","config","config.json"),{"model":"deepseek"})
        p=patch.object(sw,"_open_target",return_value="new-target")
        self.target=p.start(); self.addCleanup(p.stop)
    def queue(self): return sw.enqueue(self.c,"A","perplexity","deepseek")
    def state(self): return sw.read(sw.paths(self.c,"A")[1])
    def test_validation(self):
        for model,expected in [("bad","deepseek"),("perplexity","alice")]:
            with self.assertRaises(ValueError): sw.enqueue(self.c,"A",model,expected)
        self.assertEqual(sw.enqueue(self.c,"A","deepseek","deepseek")["phase"],"unchanged")
        self.target.assert_not_called()
    def test_queue(self):
        self.queue(); self.assertEqual(self.c.channel("A").model,"deepseek")
        with self.assertRaises(ValueError): self.queue()
    def test_apply(self):
        base=self.c.channel_path("A","logs")
        sw.write(base/"ledger_A.json",{"watermark":"AAAA0042"})
        (base/"outbox_A.jsonl").write_text("report")
        (base/"kick_buffer.jsonl").write_text("kick")
        r=self.queue(); sw.consume(self.c,"A")
        self.assertEqual(self.c.channel("A").model,"perplexity")
        self.assertEqual(self.c.channel("G").model,"qwen")
        self.assertEqual(sw.read(base/"ledger_A.json")["watermark"],"AAAA0042")
        for name,text in [("outbox_A.jsonl","report"),("kick_buffer.jsonl","kick")]:
            self.assertEqual((base/"provider_archive"/r["nonce"]/name).read_text(),text)
            self.assertFalse((base/name).exists())
        self.assertTrue(sw.read(base/"paused.json")["paused"])
        self.assertEqual(self.state()["target"],"new-target")
    def test_browser_failure(self):
        self.target.side_effect=RuntimeError("CDP down")
        self.queue(); sw.consume(self.c,"A")
        self.assertEqual(self.c.channel("A").model,"deepseek")
        self.assertEqual(self.state()["phase"],"error")
    def test_rollback(self):
        self.queue(); original=sw.write
        def fail(path,data):
            if Path(path)==self.c.path("config.json") and data["channels"]["A"]["model"]=="perplexity":
                raise OSError("disk failure")
            return original(path,data)
        with patch.object(sw,"write",side_effect=fail): sw.consume(self.c,"A")
        self.assertEqual(self.c.channel("A").model,"deepseek")
        self.assertEqual(sw.read(self.c.channel_path("A","config","config.json"))["model"],"deepseek")
        self.assertTrue(sw.read(self.c.channel_path("A","logs","paused.json"))["paused"])
    def activation(self,ok):
        self.queue(); sw.consume(self.c,"A"); sent=[]
        d=types.SimpleNamespace(ch=types.SimpleNamespace(prefix="AAAA"),
            ledger=types.SimpleNamespace(watermark="AAAA0042"),_next_id=lambda _:"AAAA0043",
            _render_activation=lambda:"Start AAAA0001",
            adapter=types.SimpleNamespace(send_text=lambda c,t:sent.append(t) or ok))
        cdp=types.SimpleNamespace(eval_expr=lambda _:True)
        for _ in range(2): self.assertEqual(sw.initialize(self.c,"A",d,cdp),ok)
        self.assertEqual(len(sent),1); self.assertIn("AAAA0043",sent[0])
        return self.state()
    def test_activation(self): self.assertEqual(self.activation(True)["phase"],"ready")
    def test_no_ambiguous_retry(self): self.assertEqual(self.activation(False)["phase"],"confirmation_required")
    def test_prefix(self):
        a=types.SimpleNamespace(collect_blocks=lambda *a,**kw:[types.SimpleNamespace(id=x) for x in ["AAAA0001","GGAA0001"]])
        self.assertEqual([b.id for b in sw.PrefixAdapter(a,"AAAA").collect_blocks(None)],["AAAA0001"])

if __name__=="__main__": unittest.main(verbosity=2)
