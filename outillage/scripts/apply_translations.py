#!/usr/bin/env python3
"""Applique les sorties d'agents aux fichiers cibles du repo, après validation."""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate_translation import validate

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "society-sunlit-valley"
WS = ROOT / "fr-workspace"

def accent_prefixes() -> tuple:
    txt = (WS / "DECISION-ACCENTS.md").read_text()
    return ("item.", "block.", "entity.") if '["item.", "block.", "entity."]' in txt else ()

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
    gl = json.loads((WS / "glossaire.json").read_text())
    keep = set(gl["keep_english_terms"])
    inv_p = WS / "invariants.json"
    if inv_p.exists():
        keep |= set(json.loads(inv_p.read_text()))
    pfx = accent_prefixes()
    all_errors = {}
    applied = 0
    for batch_path in sys.argv[1:]:
        b = json.loads(Path(batch_path).read_text())
        out_p = ROOT / b["out"]
        if not out_p.exists():
            all_errors[batch_path] = [("no_output", b["out"])]
            continue
        tr = json.loads(out_p.read_text())["translations"]
        errs = [e for e in validate(b["en"], tr, pfx)
                if not (e[0] == "untranslated" and b["en"][e[1]] in keep)]
        if errs:
            all_errors[batch_path] = errs
            continue
        target = REPO / b["target"]
        if b["kind"] == "patchouli":
            src = REPO / b["target"].replace("/fr_fr/", "/en_us/")
            doc = json.loads(src.read_text())
            for ptr, val in tr.items():
                set_pointer(doc, ptr, val)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(doc, ensure_ascii=False, indent=4) + "\n")
        else:
            cur = json.loads(target.read_text()) if target.exists() else {}
            cur.update(tr)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(cur, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        applied += 1
        print("appliqué:", b["target"], f"({len(tr)} clés)")
    print(f"{applied} lot(s) appliqué(s), {len(all_errors)} en erreur", file=sys.stderr)
    if all_errors:
        print(json.dumps({k: v[:20] for k, v in all_errors.items()}, ensure_ascii=False, indent=1))
        sys.exit(1)

if __name__ == "__main__":
    main()
