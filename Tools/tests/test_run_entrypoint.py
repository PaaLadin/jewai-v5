"""Portable runner contract tests. No live channels or browser are touched."""
import contextlib
import importlib.util
import io
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[2]


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.cfg = MagicMock()
        self.cfg.channel.return_value = types.SimpleNamespace(model="perplexity", cdp_port=9999)
        self.adapter = types.SimpleNamespace(HOST="www.perplexity.ai")
        self.factory = MagicMock(return_value=self.adapter)
        def create(model):
            if model not in ("deepseek", "qwen", "alice", "perplexity"):
                raise ValueError("unsupported adapter: " + model)
            return self.factory(model)
        metadata = {m: {"module": "Adapters." + m, "class": m.title()}
                    for m in ("deepseek", "qwen", "alice", "perplexity")}
        stubs = {
            "Core.config": types.SimpleNamespace(load=MagicMock(return_value=self.cfg)),
            "Bridge.cdp": types.SimpleNamespace(connect=MagicMock(return_value=None)),
            "Bridge.daemon": types.SimpleNamespace(Daemon=MagicMock()),
            "Adapters.registry": types.SimpleNamespace(PROVIDERS=metadata, create=create),
        }
        self.modules = patch.dict(sys.modules, stubs)
        self.modules.start()
        self.addCleanup(self.modules.stop)
        spec = importlib.util.spec_from_file_location("runner_under_test", ROOT / "Bridge" / "run.py")
        self.run = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.run)
        self.run._acquire_single_instance_mutex = MagicMock(return_value=object())

    def invoke(self, *args):
        with patch.object(sys, "argv", ["run.py", *args]):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                return self.run.main()

    def test_provider_dispatch(self):
        for name in ("deepseek", "qwen", "alice", "perplexity"):
            self.assertIs(self.run._adapter_for(name), self.adapter)
            self.factory.assert_called_with(name)

    def test_unknown_provider_rejected(self):
        with self.assertRaises(ValueError):
            self.run._adapter_for("nonsense")

    def test_configured_g_once_dead(self):
        self.assertEqual(self.invoke("--channel", "G", "--once"), 2)
        self.cfg.channel.assert_called_once_with("G")

    def test_lowercase_channel(self):
        self.assertEqual(self.invoke("--channel", "g", "--once"), 2)
        self.cfg.channel.assert_called_once_with("G")

    def test_unknown_channel_rejected_before_mutex(self):
        self.cfg.channel.side_effect = KeyError("unknown channel")
        with self.assertRaises(SystemExit) as caught:
            self.invoke("--channel", "Z", "--once")
        self.assertEqual(caught.exception.code, 2)
        self.run._acquire_single_instance_mutex.assert_not_called()

    def test_help(self):
        with self.assertRaises(SystemExit) as caught:
            self.invoke("--help")
        self.assertEqual(caught.exception.code, 0)

    def test_mutex_conflict(self):
        self.run._acquire_single_instance_mutex.return_value = None
        self.assertEqual(self.invoke("--channel", "G", "--once"), 3)

    def test_once_closes_connection(self):
        cdp = MagicMock()
        self.run.connect.return_value = cdp
        self.run.Daemon.return_value.tick.return_value = types.SimpleNamespace(processed=1, skipped=0, errors=0)
        self.assertEqual(self.invoke("--channel", "G", "--once"), 0)
        cdp.close.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
