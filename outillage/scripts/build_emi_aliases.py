#!/usr/bin/env python3
"""Génère les alias de recherche EMI sans accents.

EMI cherche avec toLowerCase() puis contains(), sans normalisation Unicode :
« ragout » ne trouve jamais « Ragoût ». Mais EmiSearch$CompiledQuery ajoute
AliasQuery sans condition et l'unit à NameQuery par un OU logique, donc un alias
sans accents rend l'objet trouvable sans toucher au nom affiché.

Nos propres noms d'objets s'écrivent sans accents (voir CLAUDE.md), donc les alias ne
couvrent que le français embarqué par les mods, que le pack ne recouvre pas : « Ragoût de
morue » de Farmer's Delight, « Boîte de pêche » d'Aquaculture, et 2 900 autres.

Refined Storage, lui, n'a pas d'équivalent : son NameGridFilter compare le seul nom
affiché et le mod n'a aucun système d'alias. C'est ce qui a fait renoncer aux noms
accentués — voir fr-workspace/DECISION-ACCENTS.md.

Écrit kubejs/assets/emi/aliases/society_fr.json et complète
kubejs/assets/emi/lang/fr_fr.json sans toucher aux clés d'interface d'EMI.

    python3 fr-workspace/scripts/build_emi_aliases.py             # régénère
    python3 fr-workspace/scripts/build_emi_aliases.py --verifier  # contrôle seul
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
import zipfile
from collections import OrderedDict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
PACK = RACINE / "society-sunlit-valley"
JARS = RACINE / "fr-workspace" / "jars"
ALIAS = PACK / "kubejs/assets/emi/aliases/society_fr.json"
LANG = PACK / "kubejs/assets/emi/lang/fr_fr.json"

ACCENT = re.compile(r"[àâäéèêëîïôöùûüÿçÀÂÄÉÈÊËÎÏÔÖÙÛÜŸÇœŒæÆ]")
NOM = re.compile(r"^(item|block)\.([^.]+)\.([^.]+)$")  # les entités ne sont pas des piles

# Ce qui porte un nom sans être un objet ramassable : l'alias serait inerte.
# Une pile inconnue se résout en EmiStack.EMPTY côté EMI, donc sans dommage, mais
# autant ne pas en écrire des milliers.
PAS_UN_OBJET = re.compile(
    r"(^|_)(wall_banner|wall_sign|wall_torch|wall_head|wall_fan|wall_skull)$"
    r"|^potted_|_stem$|^attached_|_cauldron$"
)
PREFIXE = "alias.societyfr."


def sans_accents(texte: str) -> str:
    texte = (texte.replace("œ", "oe").replace("Œ", "Oe")
                  .replace("æ", "ae").replace("Æ", "Ae"))
    return "".join(c for c in unicodedata.normalize("NFD", texte)
                   if unicodedata.category(c) != "Mn")


def lire_jars() -> tuple[dict[str, str], set[str]]:
    """Le français embarqué des mods. La clé de langue vaut preuve d'existence :
    un mod qui nomme un objet le déclare."""
    noms: dict[str, str] = {}
    modeles: set[str] = set()
    for jar in sorted(JARS.glob("*.jar")):
        try:
            z = zipfile.ZipFile(jar)
        except (zipfile.BadZipFile, OSError):
            continue
        for entree in z.namelist():
            if entree.endswith("/lang/fr_fr.json"):
                try:
                    d = json.loads(z.read(entree))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                for k, v in d.items():
                    if isinstance(v, str):
                        noms.setdefault(k, v)
            m = re.match(r"assets/([^/]+)/models/item/(.+)\.json$", entree)
            if m:
                modeles.add(f"{m.group(1)}:{m.group(2)}")
    return noms, modeles


def verifier() -> int:
    """Contrôle sans rien écrire : tout nom accentué doit avoir son alias.

    Remplace l'ancien contrôle « pas d'accents sur les noms », devenu faux depuis que la
    politique est levée. Le risque aujourd'hui n'est plus qu'un accent se glisse dans un
    nom, c'est qu'un nom accentué sorte de la recherche d'EMI faute d'alias.
    """
    noms: dict[str, str] = {}
    for f in sorted(PACK.glob("kubejs/assets/*/lang/fr_fr.json")):
        for k, v in json.loads(f.read_text(encoding="utf-8")).items():
            if isinstance(v, str) and v:
                noms[k] = v
    try:
        alias = json.loads(ALIAS.read_text(encoding="utf-8"))["aliases"]
        langue = json.loads(LANG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, KeyError) as e:
        print(f"  fichier d'alias illisible : {e}")
        return 1

    piles = {a["stacks"].removeprefix("item:") for a in alias}
    orphelins = [a["text"] for a in alias if a["text"] not in langue]
    manquants = []
    for cle, valeur in noms.items():
        m = NOM.match(cle)
        if not m or not ACCENT.search(valeur) or PAS_UN_OBJET.search(m.group(3)):
            continue
        if f"{m.group(2)}:{m.group(3)}" not in piles:
            manquants.append((cle, valeur))

    accentues = sum(1 for k, v in noms.items() if NOM.match(k) and ACCENT.search(v))
    print(f"  {accentues} noms accentués · {len(alias)} alias · {len(langue)} clés de langue")
    print(f"  noms accentués sans alias : {len(manquants)}")
    for cle, valeur in manquants[:10]:
        print(f"      {cle}\t{valeur}")
    if len(manquants) > 10:
        print(f"      … et {len(manquants) - 10} autres")
    print(f"  alias sans texte : {len(orphelins)}")
    if manquants or orphelins:
        print("  → relancer sans --verifier pour régénérer")
    return 1 if (manquants or orphelins) else 0


def main() -> None:
    if "--verifier" in sys.argv:
        raise SystemExit(verifier())
    mods, modeles = lire_jars()
    for f in PACK.glob("kubejs/assets/*/models/item/*.json"):
        modeles.add(f"{f.parents[2].name}:{f.stem}")

    pack: dict[str, str] = {}
    for f in sorted(PACK.glob("kubejs/assets/*/lang/fr_fr.json")):
        for k, v in json.loads(f.read_text(encoding="utf-8")).items():
            if isinstance(v, str) and v:
                pack[k] = v

    # le pack l'emporte sur le mod ; on ne garde que ce qui s'affiche accentué
    effectif = {**mods, **pack}
    alias, langue, vus = [], {}, set()
    ecartes = {"pas un objet ramassable": 0, "doublon": 0}
    for cle, valeur in sorted(effectif.items()):
        m = NOM.match(cle)
        if not m or not valeur or not ACCENT.search(valeur):
            continue
        sans = sans_accents(valeur)
        if sans == valeur:
            continue
        pile = f"{m.group(2)}:{m.group(3)}"
        if pile in vus:
            ecartes["doublon"] += 1
            continue
        if PAS_UN_OBJET.search(m.group(3)):
            ecartes["pas un objet ramassable"] += 1
            continue
        vus.add(pile)
        k = f"{PREFIXE}{m.group(2)}.{m.group(3)}"
        alias.append({"stacks": f"item:{pile}", "text": k})
        langue[k] = sans

    # les alias d'EMI lui-même sont parfois accentués, donc inutilisables
    ancien = json.loads(LANG.read_text(encoding="utf-8")) if LANG.exists() else {}
    interface = {k: v for k, v in ancien.items() if not k.startswith(PREFIXE)}
    for k, v in interface.items():
        if k.startswith("alias.emi.") and ACCENT.search(v):
            neuf = f"{PREFIXE}sans-accent.{k.rsplit('.', 1)[-1]}"
            for e in json.loads(
                zipfile.ZipFile(next(JARS.glob("emi-*.jar")))
                .read("assets/emi/aliases/emi.json")
            )["aliases"]:
                textes = e["text"] if isinstance(e["text"], list) else [e["text"]]
                if k in textes:
                    piles = e["stacks"] if isinstance(e["stacks"], list) else [e["stacks"]]
                    for p in piles:
                        alias.append({"stacks": p, "text": neuf})
                    langue[neuf] = sans_accents(v)

    ALIAS.parent.mkdir(parents=True, exist_ok=True)
    ALIAS.write_text(json.dumps({"aliases": alias}, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")
    fusion = OrderedDict(sorted({**interface, **langue}.items()))
    LANG.write_text(json.dumps(fusion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"  {len(alias)} alias écrits · {len(interface)} clés d'interface d'EMI préservées")
    print(f"  écartés : {ecartes}")


if __name__ == "__main__":
    main()
