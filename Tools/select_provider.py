"""Enqueue a provider switch; no browser or model commands execute here."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from Core.config import load
from Bridge.provider_switch import enqueue
from Adapters.registry import PROVIDERS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True, choices=list("ABCDEFGHIJ"))
    ap.add_argument("--provider", required=True, choices=list(PROVIDERS))
    ap.add_argument("--expected", required=True, choices=list(PROVIDERS))
    args = ap.parse_args()
    try:
        cfg = load()
        print(json.dumps(enqueue(cfg, args.channel, args.provider, args.expected)))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
