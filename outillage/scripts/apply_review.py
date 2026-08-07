#!/usr/bin/env python3
"""Applique les corrections de relecture (lang + patchouli via pointeurs).
Usage : apply_review.py <review-out-*.json ...>"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "society-sunlit-valley"

def set_pointer(obj, pointer: str, value: str) -> None:
    parts = pointer.split("/")
    for p in parts[:-1]:
        obj = obj[int(p)] if isinstance(obj, list) else obj[p]
    last = parts[-1]
    if isinstance(obj, list):
        obj[int(last)] = value
    else:
        obj[last] = value

def main() -> None:
    per_file = {}
    for rf in sys.argv[1:]:
        for c in json.loads(Path(rf).read_text())["corrections"]:
            per_file.setdefault(c["file"], []).append(c)
    total = 0
    for target, cs in sorted(per_file.items()):
        fp = REPO / target
        if not fp.exists():
            print("ABSENT:", target)
            continue
        doc = json.loads(fp.read_text())
        for c in cs:
            try:
                if target.startswith("patchouli_books"):
                    set_pointer(doc, c["key"], c["fr"])
                else:
                    if c["key"] not in doc:
                        print("clé absente:", target, c["key"])
                        continue
                    doc[c["key"]] = c["fr"]
                total += 1
            except Exception as e:
                print("échec:", target, c["key"], e)
        indent = 4 if target.startswith("patchouli_books") else 2
        sort = not target.startswith("patchouli_books")
        fp.write_text(json.dumps(doc, ensure_ascii=False, indent=indent, sort_keys=sort) + "\n")
    print(f"{total} corrections appliquées dans {len(per_file)} fichiers")

if __name__ == "__main__":
    main()
