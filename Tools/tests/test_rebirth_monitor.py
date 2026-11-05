"""Isolated tests for rebirth_monitor logic. No live Chrome."""
import importlib.util
import json
import os
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
JEHO = HERE.parent.parent
sys.path.insert(0, str(JEHO))

TROOT = HERE / "_testroot"
PASS = []
FAIL = []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("OK   " if cond else "FAIL ") + name + (("  " + detail) if detail else ""))


def setup():
    if TROOT.exists():
        shutil.rmtree(TROOT)
    (TROOT / "logs" / "rebirth").mkdir(parents=True)
    (TROOT / "logs" / "A").mkdir(parents=True)
    (TROOT / "emergency").mkdir(parents=True)
    cfg = {
        "root": str(TROOT), "bind": "127.0.0.1", "chat_port": 8670,
        "doh_proxy_port": 9899, "letters": ["A"],
        "channels": {"A": {"name": "T", "agent": 19999, "cdp": 19998,
                           "prefix": "AAAA", "extension": "e", "model": "deepseek"}},
        "thresholds": {"rebirth_cmds": 850}, "timeouts": {}, "version": "t",
    }
    (TROOT / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    from Rebirth.table import default_table_template
    tab = default_table_template()
    tab["channels"]["A"]["current_series"] = "14A"
    tab["channels"]["A"]["range"] = ["AAAA0000", "AAAA0999"]
    tab["channels"]["A"]["next_series"] = "15A"
    tab["channels"]["A"]["next_range"] = ["AAAB0000", "AAAB0999"]
    (TROOT / "logs" / "rebirth" / "series_table.json").write_text(
        json.dumps(tab, ensure_ascii=False), encoding="utf-8")
    return str(TROOT / "config.json")


def load_monitor_module():
    p = HERE.parent / "rebirth_monitor.py"
    spec = importlib.util.spec_from_file_location("rebirth_monitor", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    cfgp = setup()
    os.environ["JEWAI_CONFIG"] = cfgp
    mmod = load_monitor_module()
    from Core.config import load as load_config
    cfg = load_config(cfgp)
    mon = mmod.Monitor(cfg, dry_run=True)
    check("config root", str(cfg.root) == str(TROOT))
    check("table loaded", mon.table.get("A")["current_series"] == "14A")
    check("last_id_of dead", mon.last_id_of("A") is None)

    mon.last_id_of = lambda L: "AAAA0600"
    r = mon.check_channel("A")
    check("cmds 600 -> info", r.get("status") == "reminded" and r.get("level") == "info", str(r))
    check("reminder logged", mon.reminder_fired("A", "info"))
    r2 = mon.check_channel("A")
    check("info once/series", r2.get("status") == "ok", str(r2))

    mon2 = mmod.Monitor(cfg, dry_run=True)
    mon2.last_id_of = lambda L: "AAAA0900"
    r3 = mon2.check_channel("A")
    check("cmds 900 -> critical", r3.get("status") == "reminded" and r3.get("level") == "critical", str(r3))

    ns = "15A"
    (TROOT / "logs" / "A" / "TODO.md").write_text("next 15A\n", encoding="utf-8")
    (TROOT / "logs" / "A" / "HANDOVER.md").write_text("no marker here\n", encoding="utf-8")
    (TROOT / "emergency" / "PROMPT_15A.md").write_text("15A\n", encoding="utf-8")
    (TROOT / "SESSION_STATE.md").write_text("x\n", encoding="utf-8")
    info = mon2.table.get("A")
    missing = mon2.verify_artifacts("A", info, 0)
    check("missing marker detected", any("HANDOVER" in x for x in missing), str(missing))
    check("present files not flagged", not any("TODO" in x for x in missing), str(missing))

    old = time.time() - 9999
    os.utime(TROOT / "logs" / "A" / "TODO.md", (old, old))
    missing2 = mon2.verify_artifacts("A", info, time.time() - 100)
    check("stale detected", any("TODO" in x and "stale" in x for x in missing2), str(missing2))

    pf = TROOT / "logs" / "rebirth" / "pending_A.json"
    pf.write_text(json.dumps({"ch": "A", "ts": time.time() - mmod.ESCALATE_AFTER - 10,
                              "escalated": 0}), encoding="utf-8")
    mon2.dry = False
    mon2.check_pending()
    j = json.loads(pf.read_text(encoding="utf-8"))
    check("pending escalated", j.get("escalated") == 1, str(j))

    (TROOT / "logs" / "A" / "HANDOVER.md").write_text("15A ok\n", encoding="utf-8")
    os.utime(TROOT / "logs" / "A" / "TODO.md", None)
    os.utime(TROOT / "logs" / "A" / "HANDOVER.md", None)
    os.utime(TROOT / "emergency" / "PROMPT_15A.md", None)
    os.utime(TROOT / "SESSION_STATE.md", None)
    pf.write_text(json.dumps({"ch": "A", "ts": time.time() - 5, "escalated": 0}),
                  encoding="utf-8")
    mon2.check_pending()
    check("pending verified removed", not pf.exists())

    print("")
    print("PASS %d FAIL %d" % (len(PASS), len(FAIL)))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())