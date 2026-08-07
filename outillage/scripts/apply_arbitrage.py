#!/usr/bin/env python3
"""Applique un arbitrage d'identiques : corrections dans les out + légitimes en invariants.
Usage : apply_arbitrage.py <arbitrage.json> <flagged.json>"""
import json, sys
from pathlib import Path

WS = Path(__file__).resolve().parents[1]

def main() -> None:
    arb = json.loads(Path(sys.argv[1]).read_text())
    flagged = {f["key"]: f for f in json.loads(Path(sys.argv[2]).read_text())}
    for a in [x for x in arb if not x.get("keep")]:
        print("correction:", a["key"], ":", a["en"], "→", a["fr"])
        b = json.loads(Path(flagged[a["key"]]["batch"]).read_text())
        out = WS.parent / b["out"]
        d = json.loads(out.read_text())
        d["translations"][a["key"]] = a["fr"]
        out.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    p = WS / "invariants.json"
    inv = set(json.loads(p.read_text()))
    before = len(inv)
    inv |= {a["en"] for a in arb if a.get("keep") and a.get("en")}
    p.write_text(json.dumps(sorted(inv), ensure_ascii=False, indent=1) + "\n")
    print(f"invariants: {before} → {len(inv)}")

if __name__ == "__main__":
    main()
