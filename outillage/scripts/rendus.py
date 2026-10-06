#!/usr/bin/env python3
"""Relevé des rendus : les termes anglais récurrents traduits de plusieurs façons dans le pack.

Pour chaque n-gramme anglais (1 à 3 mots) présent dans assez de textes, le relevé cherche les n-grammes français
associés (présents surtout dans les textes qui contiennent le terme anglais), puis couvre ces textes de façon gloutonne.
Un terme dont deux rendus concurrents se partagent les textes est signalé, avec un concordancier : c'est la matière
que les relecteurs départagent (une incohérence, ou une différence voulue). Les termes déjà imposés
(coherence/termes_imposes.json) ne sont pas relevés : le contrôle `terminologie` les tient.

Le relevé est une heuristique de tri, pas un contrôle : il signale plus qu'il ne faut, les relecteurs écartent.

    python3 fr-workspace/scripts/rendus.py --sortie fr-workspace/chasse/rendus/releve.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from chasser import Pack  # noqa: E402

CODES = re.compile(r"\$\([^)]*\)|§.|&[0-9a-fk-or]|%(?:\d+\$)?[sd]|\{[^}]*\}|<[^>]*>|\\n|\[[^\]]*\]\([^)]*\)")
MOT = re.compile(r"[A-Za-zÀ-ÿ]+(?:['-][A-Za-zÀ-ÿ]+)*")

VIDES_EN = set("""a an the of to in on at by for from with and or but not no is are be been was were it its this that these
those you your can will may must if then than so as into onto up down out over under all any each every some more most less
very also only just when while where which who what how there here they them their he she his her we our us i me my do does
did done has have had get gets got make makes made use used using one two three four five six first second new other such
both own same per via etc s t""".split())
VIDES_FR = set("""le la les l un une des du de d à au aux en dans sur sous par pour avec et ou mais ne pas plus moins
très aussi seulement quand lorsque où qui que quoi dont ce cet cette ces c se s son sa ses leur leurs il elle ils elles on
tu te t toi ton ta tes vous votre vos nous notre nos je j me m mon ma mes y est sont être été était peut peuvent doit
faire fait font a ont avoir tout tous toute toutes chaque autre autres même mêmes si alors comme ainsi ici là deux trois
un une premier première nouveau nouvelle""".split())


def plier(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def racine_fr(m: str) -> str:
    m = plier(m)
    if len(m) > 3 and m[-1] in "sx" and m[-2] not in "s":
        return m[:-1]
    return m


def racine_en(m: str) -> str:
    m = m.lower()
    if len(m) > 4 and m.endswith("ies"):
        return m[:-3] + "y"
    if len(m) > 3 and m.endswith("s") and m[-2] not in "siu":
        return m[:-1]
    return m


def ngrammes(mots: list, vides: set, n_max: int = 3) -> set:
    vus = set()
    for i in range(len(mots)):
        if mots[i] in vides:
            continue
        for n in range(1, n_max + 1):
            seg = mots[i:i + n]
            if len(seg) < n or seg[-1] in vides:
                continue
            vus.add(" ".join(seg))
    return vus


def mots_de(texte: str, racine, vides: set) -> list:
    mots = [m.lower() for m in MOT.findall(CODES.sub(" ", texte))]
    return [m if m in vides or plier(m) in vides else racine(m) for m in mots]


def releve(pack, df_min: int, couverture_max: float, part_min: float, n_conc: int, imposes: set) -> list:
    textes = [t for t in pack.textes if t.en and t.fr and t.en != t.fr]
    en_ng, fr_ng = {}, {}
    df_en, df_fr = Counter(), Counter()
    for t in textes:
        e = ngrammes(mots_de(t.en, racine_en, VIDES_EN), VIDES_EN)
        f = ngrammes(mots_de(t.fr, racine_fr, VIDES_FR), VIDES_FR)
        en_ng[t.id], fr_ng[t.id] = e, f
        df_en.update(e)
        df_fr.update(f)
    index = defaultdict(list)
    for t in textes:
        for g in en_ng[t.id]:
            if df_en[g] >= df_min:
                index[g].append(t)
    signales = []
    for terme, porteurs in index.items():
        if terme in imposes or len(set(t.espace for t in porteurs)) < 1:
            continue
        n = len(porteurs)
        co = Counter()
        for t in porteurs:
            co.update(fr_ng[t.id])
        # Rendus candidats : fréquents parmi les porteurs, et associés (rares ailleurs).
        cands = {f: c for f, c in co.items() if c >= max(3, part_min * n) and c / df_fr[f] >= 0.5}
        if len(cands) < 2:
            continue
        restants = {t.id for t in porteurs}
        choisis = []
        while restants and len(choisis) < 4:
            meilleur = max(cands, key=lambda f: (sum(1 for i in restants if f in fr_ng[i]), -len(f)), default=None)
            if meilleur is None:
                break
            gain = sum(1 for i in restants if meilleur in fr_ng[i])
            if gain < max(3, part_min * n):
                break
            # Un rendu qui contient le précédent (ou l'inverse) n'est pas concurrent : « mot clé » / « clé ».
            if any(meilleur in c or c in meilleur for c, _ in choisis):
                cands.pop(meilleur)
                continue
            choisis.append((meilleur, gain))
            restants = {i for i in restants if meilleur not in fr_ng[i]}
            cands.pop(meilleur)
        if len(choisis) < 2 or choisis[0][1] / n > couverture_max:
            continue
        exemples = {}
        for f, _ in choisis:
            ex = [t for t in porteurs if f in fr_ng[t.id]]
            ex.sort(key=lambda t: (len(t.en), t.id))
            exemples[f] = [{"id": t.id, "espace": t.espace, "en": t.en[:300], "fr": t.fr[:300]} for t in ex[:n_conc]]
        signales.append({
            "terme": terme, "textes": n, "espaces": len(set(t.espace for t in porteurs)),
            "rendus": [{"fr": f, "textes": g} for f, g in choisis],
            "sans_rendu": len(restants), "exemples": exemples,
        })
    # Un même conflit remonte par plusieurs n-grammes (« tag », « item tag ») : garder le plus court par paire de rendus.
    vus, uniques = set(), []
    for s in sorted(signales, key=lambda s: (len(s["terme"].split()), -s["textes"])):
        cle = tuple(sorted(r["fr"] for r in s["rendus"][:2]))
        if cle in vus:
            continue
        vus.add(cle)
        uniques.append(s)
    uniques.sort(key=lambda s: -min(r["textes"] for r in s["rendus"][:2]))
    return uniques


def registres(pack) -> list:
    """Par espace de noms : textes qui tutoient, textes qui vouvoient. Les espaces qui mélangent les deux."""
    TU = re.compile(r"\b(tu|ton|ta|tes|toi|t'as)\b|\b\w+(?:es|is|ns)-tu\b", re.I)
    VOUS = re.compile(r"\b(vous|votre|vos)\b", re.I)
    par = defaultdict(lambda: {"tu": [], "vous": []})
    for t in pack.textes:
        if TU.search(t.fr):
            par[t.unite]["tu"].append(t.id)
        if VOUS.search(t.fr):
            par[t.unite]["vous"].append(t.id)
    sortie = []
    for u, d in par.items():
        a, b = len(d["tu"]), len(d["vous"])
        if a and b:
            mino = "tu" if a < b else "vous"
            sortie.append({"unite": u, "tu": a, "vous": b, "minoritaires": d[mino][:40], "registre_minoritaire": mino})
    sortie.sort(key=lambda s: -min(s["tu"], s["vous"]))
    return sortie


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--sortie", required=True)
    p.add_argument("--df-min", type=int, default=6, help="textes minimum pour qu'un terme anglais soit relevé")
    p.add_argument("--couverture-max", type=float, default=0.9, help="au-delà, le rendu majoritaire suffit")
    p.add_argument("--part-min", type=float, default=0.08, help="part minimale d'un rendu concurrent")
    p.add_argument("--exemples", type=int, default=6)
    a = p.parse_args(argv)
    pack = Pack()
    imposes = {racine_en(t["anglais"].lower()) for t in json.loads(
        (pack.espace / "coherence" / "termes_imposes.json").read_text(encoding="utf-8"))}
    termes = releve(pack, a.df_min, a.couverture_max, a.part_min, a.exemples, imposes)
    reg = registres(pack)
    sortie = Path(a.sortie)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(json.dumps({"termes": termes, "registres": reg}, ensure_ascii=False, indent=1) + "\n",
                      encoding="utf-8")
    print(f"{len(termes)} terme(s) à rendus multiples, {len(reg)} unité(s) qui mêlent tu et vous → {sortie}")
    for s in termes[:25]:
        print(f"  {s['terme']:<24} {s['textes']:>4}  " + " | ".join(f"{r['fr']} {r['textes']}" for r in s["rendus"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
