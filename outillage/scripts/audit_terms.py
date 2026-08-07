#!/usr/bin/env python3
"""Audit de cohérence : un terme anglais tantôt conservé, tantôt traduit.

Cible les NOMS INVENTÉS (absents du dictionnaire anglais) — ceux pour lesquels la
question « garder ou traduire » se pose vraiment. Élimine les faux positifs de
cognats (alpine/alpin, chevron/chevrons) par comparaison de radical.
Écrit fr-workspace/audit-termes.json.
"""
import json, re, sys, unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "society-sunlit-valley"
WS = ROOT / "fr-workspace"
DICT = Path("/usr/share/dict/words")

def fold(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s.replace("œ", "oe").replace("Œ", "Oe").lower()

def kept_in(term: str, fr: str) -> bool:
    """Le terme survit-il dans le FR ? (radical commun de 4+ caractères)"""
    t = fold(term)
    stem = t[:max(4, len(t) - 2)]
    return any(w.startswith(stem) or t.startswith(w[:max(4, len(w) - 2)])
               for w in re.findall(r"[a-z][a-z'-]*", fold(fr)))

def main() -> None:
    english = set()
    if DICT.exists():
        english = {w.strip().lower() for w in DICT.read_text(errors="ignore").splitlines()}
    inv = json.loads((WS / "inventaire.json").read_text())
    en_by_target = defaultdict(dict)
    for u in inv["units"]:
        if u["kind"] != "patchouli":
            en_by_target[u["target"]].update(u["en"])
    pairs = []
    for target, en in en_by_target.items():
        ns = target.split("/")[2]
        fp = REPO / target
        if not fp.exists():
            continue
        fr = json.loads(fp.read_text())
        wit = {}
        for loc in ("ko_kr", "zh_cn"):
            p = REPO / "kubejs" / "assets" / ns / "lang" / f"{loc}.json"
            if p.exists():
                try: wit[loc] = json.loads(p.read_text())
                except Exception: pass
        for k, v in en.items():
            if k in fr and v.strip() and k.startswith(("item.", "block.", "entity.", "fluid.")):
                pairs.append({"ns": ns, "key": k, "en": v, "fr": fr[k],
                              "ko": wit.get("ko_kr", {}).get(k),
                              "zh": wit.get("zh_cn", {}).get(k)})
    terms = defaultdict(lambda: {"kept": [], "translated": []})
    for p in pairs:
        for w in set(re.findall(r"[A-Za-z][A-Za-z'-]{3,}", p["en"])):
            wl = w.lower()
            if wl in english or wl.rstrip("s") in english:
                continue  # mot anglais courant : la question ne se pose pas
            terms[wl]["kept" if kept_in(w, p["fr"]) else "translated"].append(p)
    out = []
    for w, d in terms.items():
        if not (d["kept"] and d["translated"]):
            continue
        out.append({"terme": w, "conserve": len(d["kept"]), "traduit": len(d["translated"]),
                    "ex_conserve": [{"key": x["key"], "en": x["en"], "fr": x["fr"], "ko": x["ko"], "zh": x["zh"]} for x in d["kept"][:4]],
                    "ex_traduit": [{"key": x["key"], "en": x["en"], "fr": x["fr"], "ko": x["ko"], "zh": x["zh"]} for x in d["translated"][:4]]})
    out.sort(key=lambda e: -min(e["conserve"], e["traduit"]))
    (WS / "audit-termes.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"{len(pairs)} noms analysés | {len(terms)} termes inventés | {len(out)} au traitement MIXTE\n")
    for e in out[:int(sys.argv[1]) if len(sys.argv) > 1 else 25]:
        print(f"  « {e['terme']} » — conservé {e['conserve']}× / traduit {e['traduit']}×")
        x = e["ex_conserve"][0]; print(f"      gardé   : {x['en']!r} → {x['fr']!r}")
        x = e["ex_traduit"][0]; print(f"      traduit : {x['en']!r} → {x['fr']!r}")

if __name__ == "__main__":
    main()
