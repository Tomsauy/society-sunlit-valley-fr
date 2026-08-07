#!/usr/bin/env python3
"""Détecte les chaînes EN identiques traduites différemment ; applique les arbitrages.
Les variantes qui ne diffèrent que par les accents (politique accents) sont ignorées."""
import json, sys, unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "society-sunlit-valley"
WS = ROOT / "fr-workspace"

def fold(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s.replace("œ", "oe").replace("Œ", "Oe").lower()

def collect():
    """en_value → {fr_value → [(source, clé)]}. Sources : fichiers produits + fr des jars."""
    index = defaultdict(lambda: defaultdict(list))
    inv = json.loads((WS / "inventaire.json").read_text())
    en_by_target = defaultdict(dict)
    for u in inv["units"]:
        if u["kind"] != "patchouli":
            en_by_target[u["target"]].update(u["en"])
    for target, en in en_by_target.items():
        fp = REPO / target
        if not fp.exists():
            continue
        fr = json.loads(fp.read_text())
        for k, v in en.items():
            if k in fr and 0 < len(v) <= 60:
                index[v][fr[k]].append([target, k])
    for jar_dir in (WS / "extracted").iterdir():
        if not jar_dir.is_dir():
            continue
        for ns_dir in jar_dir.iterdir():
            en_f, fr_f = ns_dir / "en_us.json", ns_dir / "fr_fr.json"
            if not (en_f.exists() and fr_f.exists()):
                continue
            en_d, fr_d = json.loads(en_f.read_text()), json.loads(fr_f.read_text())
            # en jeu, l'override kubejs masque le jar : on lit ce que le joueur voit
            kub = REPO / "kubejs" / "assets" / ns_dir.name / "lang" / "fr_fr.json"
            kub_d = json.loads(kub.read_text()) if kub.exists() else {}
            for k, v in en_d.items():
                if k in fr_d and 0 < len(v) <= 60:
                    index[v][kub_d.get(k, fr_d[k])].append([f"jar:{ns_dir.name}", k])
    return index

def detect():
    div = []
    for en, variants in collect().items():
        if len(variants) < 2:
            continue
        if len({fold(fr) for fr in variants}) < 2:  # ne diffèrent que par les accents
            continue
        div.append({"en": en, "variants": {fr: locs for fr, locs in variants.items()}})
    div.sort(key=lambda d: -sum(len(l) for l in d["variants"].values()))
    (WS / "divergences.json").write_text(json.dumps(div, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(div)} divergences")

def apply_choices(choices_path: str):
    """choices: [{"en", "chosen_fr", "keep_distinct"}] — applique chosen_fr partout dans les
    fichiers PRODUITS ; pour les sources jar:<ns>, ajoute un override ciblé kubejs.
    Respecte la politique accents : clés-noms à 3 segments → version sans accents."""
    choices = json.loads(Path(choices_path).read_text())
    div = {d["en"]: d for d in json.loads((WS / "divergences.json").read_text())}
    def accent_free(s):
        s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
        return s.replace("œ", "oe").replace("Œ", "Oe")
    edits = defaultdict(dict)
    for c in choices:
        if c.get("keep_distinct") or c["en"] not in div:
            continue
        for fr, locs in div[c["en"]]["variants"].items():
            if fr == c["chosen_fr"]:
                continue
            for src, key in locs:
                target = f"kubejs/assets/{src[4:]}/lang/fr_fr.json" if src.startswith("jar:") else src
                val = c["chosen_fr"]
                if key.startswith(("item.", "block.", "entity.")) and key.count(".") == 2:
                    val = accent_free(val)
                edits[target][key] = val
    for target, kv in edits.items():
        fp = REPO / target
        cur = json.loads(fp.read_text()) if fp.exists() else {}
        cur.update(kv)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(json.dumps(cur, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        print("réconcilié:", target, len(kv), "clés")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        apply_choices(sys.argv[2])
    else:
        detect()
