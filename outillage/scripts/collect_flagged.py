#!/usr/bin/env python3
"""Collecte les signalements du validateur pour une liste de lots.
Usage : collect_flagged.py <liste-batches.txt> <sortie.json>"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate_translation import validate

WS = Path(__file__).resolve().parents[1]

def main() -> None:
    keep = set(json.loads((WS / "glossaire.json").read_text())["keep_english_terms"])
    keep |= set(json.loads((WS / "invariants.json").read_text()))
    flagged = []
    for bp in Path(sys.argv[1]).read_text().splitlines():
        b = json.loads(Path(bp).read_text())
        out = WS.parent / b["out"] if not Path(b["out"]).is_absolute() else Path(b["out"])
        if not out.exists():
            flagged.append({"batch": bp, "key": None, "en": None, "code": "no_output"})
            continue
        tr = json.loads(out.read_text())["translations"]
        for code, key in validate(b["en"], tr, ("item.", "block.", "entity.")):
            if code == "untranslated" and b["en"][key] in keep:
                continue
            flagged.append({"batch": bp, "key": key, "en": b["en"].get(key), "code": code})
    Path(sys.argv[2]).write_text(json.dumps(flagged, ensure_ascii=False, indent=1) + "\n")
    from collections import Counter
    print(len(flagged), "signalements :", dict(Counter(f["code"] for f in flagged)))

if __name__ == "__main__":
    main()
