#!/usr/bin/env python3
"""Découpe l'inventaire en lots de traduction ≤200 clés avec contexte."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WS = ROOT / "fr-workspace"
CHUNK = 200

def relevant_glossary(chunk: dict, entries: list) -> list:
    """Entrées du glossaire dont le terme EN apparaît dans les valeurs du lot."""
    text = " \n ".join(chunk.values()).lower()
    out = []
    for e in entries:
        t = e["en"].lower()
        if len(t) >= 3 and t in text:
            out.append({"en": e["en"], "fr": e["fr"], "keep_english": e.get("keep_english", False)})
    return out

def main() -> None:
    kinds = None
    if "--kinds" in sys.argv:
        kinds = set(sys.argv[sys.argv.index("--kinds") + 1].split(","))
    inv = json.loads((WS / "inventaire.json").read_text())
    glossary = json.loads((WS / "glossaire.json").read_text())["entries"]
    (WS / "batches").mkdir(exist_ok=True)
    made = []
    for u in inv["units"]:
        if kinds and u["kind"] not in kinds:
            continue
        items = sorted(u["en"].items())
        ctx = dict(items[:30])
        ko = {}
        w = u["witnesses"].get("ko_kr")
        if w and Path(w).exists() and u["kind"] != "patchouli":
            try:
                ko = json.loads(Path(w).read_text())
            except Exception:
                ko = {}
        slug = re.sub(r"[^a-z0-9]+", "_", u["id"].lower())
        for n, i in enumerate(range(0, len(items), CHUNK)):
            chunk = dict(items[i:i + CHUNK])
            batch = {"unit_id": u["id"], "kind": u["kind"], "namespace": u["namespace"],
                     "target": u["target"], "en": chunk, "context_sample": ctx,
                     "jar_fr_partial": u["jar_fr_partial"],
                     "witness_ko": {k: ko[k] for k in chunk if k in ko},
                     "glossary": relevant_glossary(chunk, glossary),
                     "out": f"fr-workspace/out/{slug}-{n:03d}.json"}
            p = WS / "batches" / f"tr-{u['kind']}-{slug}-{n:03d}.json"
            p.write_text(json.dumps(batch, ensure_ascii=False, indent=1) + "\n")
            made.append(str(p.relative_to(ROOT)))
    print(json.dumps(made, indent=1))

if __name__ == "__main__":
    main()
