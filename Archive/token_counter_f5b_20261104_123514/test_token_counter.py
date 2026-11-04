"""Isolated tests for token_counter. No live Chrome."""
import importlib.util
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
JEHO = HERE.parent.parent
sys.path.insert(0, str(JEHO))
TROOT = HERE / "_testroot_tc"
PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("OK   " if cond else "FAIL ") + name + (("  " + detail) if detail else ""))


def setup():
    if TROOT.exists():
        shutil.rmtree(TROOT)
    (TROOT / "logs").mkdir(parents=True)
    (TROOT / "Profiles" / "A" / "logs").mkdir(parents=True)
    cfg = {"root": str(TROOT), "bind": "127.0.0.1", "chat_port": 8670,
           "doh_proxy_port": 9899, "letters": ["A"],
           "channels": {"A": {"name": "T", "agent": 19999, "cdp": 19998,
                              "prefix": "AAAA", "extension": "e", "model": "deepseek"}},
           "thresholds": {}, "timeouts": {}, "version": "t"}
    (TROOT / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    return str(TROOT / "config.json")


def load_mod():
    p = HERE / "token_counter.py"
    spec = importlib.util.spec_from_file_location("token_counter", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    cfgp = setup()
    import os
    os.environ["JEWAI_CONFIG"] = cfgp
    m = load_mod()
    from Core.config import load as load_config
    cfg = load_config(cfgp)

    # formula
    check("empty -> 0", m.estimate_tokens("") == 0)
    # 40 latin -> 10, 25 cyr -> 10, total ~20
    check("latin 40", m.estimate_tokens("a" * 40) == 10)
    check("cyr 25", m.estimate_tokens("\u0430" * 25) == 10)
    check("mixed", m.estimate_tokens("a" * 40 + "\u0430" * 25) == 20)

    # levels
    check("level ok 10", m.level_for(10) == "ok")
    check("level yellow 80", m.level_for(80) == "yellow")
    check("level red90 90", m.level_for(90) == "red90")
    check("level red95 95", m.level_for(95) == "red95")
    check("blink red95", m.blink_ms("red95") == 500)
    check("voice red90", m.voice_needed("red90"))
    check("no voice yellow", not m.voice_needed("yellow"))

    # update: small text -> ok
    st = m.update(cfg, "A", text="a" * 40, limit=3600)
    check("small estimate", st["estimate"] == 10, str(st))
    check("small level", st["level"] == "ok")

    # 3000 latin -> 750 tokens -> ~20.8% ok
    st = m.update(cfg, "A", text="a" * 3000, limit=3600)
    check("mid level ok", st["level"] == "ok", str(st))

    # 12000 latin -> 3000 -> 83.3% yellow
    st = m.update(cfg, "A", text="a" * 12000, limit=3600)
    check("yellow", st["level"] == "yellow", str(st))
    check("warned set", st["warned"] is True)

    # 13000 -> 3250 -> 90.3 red90
    st = m.update(cfg, "A", text="a" * 13000, limit=3600)
    check("red90", st["level"] == "red90", str(st))

    # 14000 -> 3500 -> 97.2 red95
    st = m.update(cfg, "A", text="a" * 14000, limit=3600)
    check("red95", st["level"] == "red95", str(st))

    # hysteresis: drop to 2000 latin = 500 tokens = 13.9% -> warned cleared
    st = m.update(cfg, "A", text="a" * 2000, limit=3600)
    check("hysteresis clears warned", st["warned"] is False, str(st))
    check("back to ok", st["level"] == "ok")

    # send count + snowball
    st = m.update(cfg, "A", text="a" * 40, limit=3600, send_delta=3)
    check("sendCount 3", st["sendCount"] == 3, str(st))
    check("snowball = 10*3", st["snowball"] == 30, str(st))

    # reset
    st = m.reset(cfg, "A")
    check("reset estimate 0", st["estimate"] == 0)
    check("reset sendCount 0", st["sendCount"] == 0)
    check("reset level ok", st["level"] == "ok")

    # persistence
    p = m.state_path(cfg, "A")
    check("state file exists", p.exists(), str(p))

    print("")
    print("PASS %d FAIL %d" % (len(PASS), len(FAIL)))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())