#!/usr/bin/env python3
"""Détecte les termes candidats au glossaire : valeurs EN partagées, noms Society, vocab vanilla."""
import json, re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WS = ROOT / "fr-workspace"

def main() -> None:
    inv = json.loads((WS / "inventaire.json").read_text())
    mc_en = json.loads((WS / "references" / "mc_en_us.json").read_text())
    mc_fr = json.loads((WS / "references" / "mc_fr_fr.json").read_text())
    vanilla = {v: mc_fr[k] for k, v in mc_en.items() if k in mc_fr}
    # index valeur EN → occurrences dans les unités à traduire
    occ = defaultdict(lambda: {"namespaces": set(), "keys": [], "count": 0, "witness_ko": None})
    ko_cache = {}
    for u in inv["units"]:
        ko = {}
        w = u["witnesses"].get("ko_kr")
        if w and Path(w).exists() and u["kind"] != "patchouli":
            if w not in ko_cache:
                try:
                    ko_cache[w] = json.loads(Path(w).read_text())
                except Exception:
                    ko_cache[w] = {}
            ko = ko_cache[w]
        for k, v in u["en"].items():
            if len(v) > 60 or not re.search(r"[A-Za-z]", v):
                continue
            e = occ[v]
            e["namespaces"].add(u["namespace"])
            e["count"] += 1
            if len(e["keys"]) < 3:
                e["keys"].append(k)
            if ko and k in ko and not e["witness_ko"]:
                e["witness_ko"] = ko[k]
    # fr des jars (référence) : en_value → {ns: fr_value}
    jar_fr_index = defaultdict(dict)
    for jar_dir in (WS / "extracted").iterdir():
        if not jar_dir.is_dir():
            continue
        for ns_dir in jar_dir.iterdir():
            en_f, fr_f = ns_dir / "en_us.json", ns_dir / "fr_fr.json"
            if en_f.exists() and fr_f.exists():
                en_d, fr_d = json.loads(en_f.read_text()), json.loads(fr_f.read_text())
                for k, v in en_d.items():
                    if k in fr_d and v != fr_d[k] and len(v) <= 60:
                        jar_fr_index[v][ns_dir.name] = fr_d[k]
    cands = []
    for v, e in occ.items():
        multi = len(e["namespaces"]) >= 2
        society_name = "society" in e["namespaces"] and any(
            k.startswith(("item.", "block.")) for k in e["keys"])
        if not (multi or society_name or v in vanilla or v in jar_fr_index):
            continue
        cands.append({"en": v, "occurrences": e["count"],
                      "namespaces": sorted(e["namespaces"]),
                      "vanilla_fr": vanilla.get(v),
                      "jar_fr": jar_fr_index.get(v, {}),
                      "witness_ko": e["witness_ko"],
                      "sample_keys": e["keys"]})
    cands.sort(key=lambda c: -c["occurrences"])
    (WS / "glossaire-candidats.json").write_text(
        json.dumps(cands, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(cands)} candidats")

if __name__ == "__main__":
    main()
