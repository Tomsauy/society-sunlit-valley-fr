#!/usr/bin/env python3
"""Classe les différences entre deux états de la traduction.

Usage : python3 compare_accents.py <ref_a> <ref_b>

Une différence qui ne tient qu'aux accents est le chantier lui-même ; une
différence de fond est une correction faite depuis, qu'il faut reporter.

C'est ce contrôle qui manquait au chantier d'août, où les erreurs se
découvraient une à une. Il replie les accents comme le mod Accent Fold, de
sorte que les deux raisonnements coïncident.

Quatre choses peuvent différer, et le code de sortie les distingue :

  0  rien, ou des accents seuls — le chantier et rien d'autre.

  2  des clés sont apparues ou ont disparu. Ce n'est pas forcément une faute :
     une montée de version retire les clés mortes, et le chantier lui-même a
     retiré 2 939 alias EMI à dessein. Échouer là-dessus serait crier au loup à
     chaque version. Mais ce n'est pas non plus un succès : une version
     antérieure de ce script se contentait d'en imprimer le NOMBRE, et c'est
     ainsi qu'une clé morte ressuscitée par un revert
     (item.society.overflow_token.description.warn) s'est cachée au milieu des
     2 939 retraits voulus. Elles sont donc listées une à une, et le code 2
     oblige l'appelant à en accuser réception plutôt qu'à lire « tout va bien ».

  1  une différence de fond, ou un fichier illisible. Le fond est ce que le
     chantier ne doit jamais changer. Un fichier illisible, lui, n'est jamais un
     état légitime de la traduction : c'est le contrôle qui ne sait plus ce
     qu'il compare, et l'ancienne version le rangeait dans le même compteur que
     les clés absentes, puis sautait le fichier ENTIER en silence.
"""
import json
import subprocess
import sys
import unicodedata
from itertools import groupby
from pathlib import Path

PACK = Path(__file__).resolve().parents[2] / "society-sunlit-valley"
# Les ligatures que la normalisation Unicode ne décompose pas. Table et ordre
# d'application doivent rester identiques à Accents.java dans le dépôt du mod
# (github.com/Tomsauy/accent-fold), faute de quoi ce contrôle classerait au « fond »
# des différences qui ne tiennent qu'aux accents.
LIGATURES = (("œ", "oe"), ("Œ", "OE"), ("æ", "ae"), ("Æ", "AE"),
             ("ø", "o"), ("Ø", "O"), ("ß", "ss"), ("ẞ", "ss"),
             ("đ", "d"), ("Đ", "D"), ("ð", "d"), ("Ð", "D"),
             ("ł", "l"), ("Ł", "L"))
# Java replie \p{M}, c'est-à-dire Mn + Mc + Me. Le module re n'a pas ces classes ;
# les énumérer par catégorie est exact, là où un intervalle de bloc Unicode laisserait
# passer les marques hors du bloc combinant de base.
MARQUES = {"Mn", "Mc", "Me"}


class FichierIllisible(Exception):
    """Un fichier existe dans la référence mais son JSON ne se lit pas."""

    def __init__(self, ref, chemin, raison):
        super().__init__(f"{chemin} ({ref}) : {raison}")
        self.ref, self.chemin, self.raison = ref, chemin, raison


def plier(texte):
    """Le texte sous sa forme de comparaison : minuscules, sans accents.

    Mêmes étapes, dans le même ordre, qu'Accents.normalize côté mod : décomposer,
    ôter les marques, recomposer, PUIS remplacer les ligatures. Les remplacer avant
    laisserait « Ǽ » ressortir en « æ » là où la fonction rend « ae ».
    """
    decompose = unicodedata.normalize("NFD", texte)
    sans_marques = "".join(c for c in decompose
                           if unicodedata.category(c) not in MARQUES)
    recompose = unicodedata.normalize("NFC", sans_marques)
    for avant, apres in LIGATURES:
        recompose = recompose.replace(avant, apres)
    return recompose.lower()


def _git(*args):
    r = subprocess.run(["git", "-C", str(PACK), *args],
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def _traduits(ref):
    """Tout ce qui est traduit : les fichiers de langue et les livres."""
    sortie = _git("ls-tree", "-r", "--name-only", ref) or ""
    return [l for l in sortie.split("\n")
            if l.endswith("/lang/fr_fr.json")
            or (l.startswith("patchouli_books/") and "/fr_fr/" in l)]


def _aplatir(objet, prefixe=""):
    """Toutes les chaînes d'un JSON, avec leur chemin.

    Les livres Patchouli imbriquent leurs textes : un parcours récursif est
    nécessaire, là où un fichier de langue est plat.
    """
    plat = {}
    if isinstance(objet, dict):
        for cle, valeur in objet.items():
            plat.update(_aplatir(valeur, f"{prefixe}.{cle}" if prefixe else cle))
    elif isinstance(objet, list):
        for i, valeur in enumerate(objet):
            plat.update(_aplatir(valeur, f"{prefixe}[{i}]"))
    elif isinstance(objet, str):
        plat[prefixe] = objet
    return plat


def _charger(ref, chemin):
    """Le contenu aplati du fichier, ou None s'il n'existe pas dans cette réf.

    Absent et illisible sont deux choses différentes, que l'ancienne version
    confondait en un même None : un fichier qu'une référence ne contient pas est
    un ajout ou une suppression ordinaire, dont les clés se listent ; un fichier
    présent mais au JSON cassé est une panne, et lève.
    """
    brut = _git("show", f"{ref}:{chemin}")
    if brut is None:
        return None
    try:
        return _aplatir(json.loads(brut))
    except json.JSONDecodeError as e:
        raise FichierIllisible(ref, chemin, e) from e


def comparer(ref_a, ref_b):
    """Classe chaque différence entre deux états.

    Rend `accents` (un compte : ces différences SONT le chantier), et trois
    listes — `fond`, `apparues`, `disparues` — plus `illisibles`. Les clés de
    présence se listent, elles aussi : c'est en les comptant qu'on cesse de les
    voir.
    """
    accents = 0
    fond, apparues, disparues, illisibles = [], [], [], []
    for chemin in sorted(set(_traduits(ref_a)) | set(_traduits(ref_b))):
        charges, casse = [], False
        for ref in (ref_a, ref_b):
            try:
                charges.append(_charger(ref, chemin))
            except FichierIllisible as e:
                illisibles.append(e)
                casse = True
        # Un fichier illisible d'un côté rend toute comparaison de ses clés
        # mensongère : on ne verse pas ses clés dans `disparues`, on le signale.
        if casse:
            continue
        a, b = charges[0] or {}, charges[1] or {}
        for cle in sorted(set(a) | set(b)):
            va, vb = a.get(cle), b.get(cle)
            if vb is None:
                disparues.append((chemin, cle, va))
            elif va is None:
                apparues.append((chemin, cle, vb))
            elif va == vb:
                continue
            elif plier(va) == plier(vb):
                accents += 1
            else:
                fond.append((chemin, cle, va, vb))
    return {"accents": accents, "fond": fond, "apparues": apparues,
            "disparues": disparues, "illisibles": illisibles}


def _lister(titre, entrees):
    """Les clés une à une, groupées par fichier, jamais tronquées.

    Le compte par fichier donne l'échelle d'un coup d'oeil — 2 939 alias EMI se
    sautent vite — mais chaque clé reste écrite : c'est la seule forme où celle
    qu'on n'attendait pas ne peut pas se fondre dans la masse.
    """
    if not entrees:
        return
    print(f"\n      {titre} ({len(entrees)}) :")
    for chemin, lot in groupby(entrees, key=lambda e: e[0]):
        lot = list(lot)
        print(f"\n        {chemin} ({len(lot)})")
        for _, cle, valeur in lot:
            print(f"          {cle} : {valeur[:80]}")


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    ref_a, ref_b = sys.argv[1], sys.argv[2]
    r = comparer(ref_a, ref_b)
    print(f"  {ref_a} → {ref_b}")
    lignes = [("différant par les accents seuls", r["accents"]),
              ("différant sur le fond", len(r["fond"])),
              (f"apparues (absentes de {ref_a})", len(r["apparues"])),
              (f"disparues (absentes de {ref_b})", len(r["disparues"]))]
    largeur = max(len(etiquette) for etiquette, _ in lignes)
    for etiquette, combien in lignes:
        print(f"      {etiquette:<{largeur}} : {combien}")

    if r["illisibles"]:
        print(f"\n      FICHIERS ILLISIBLES — la comparaison est incomplète, "
              f"leurs clés n'ont PAS été comparées ({len(r['illisibles'])}) :")
        for e in r["illisibles"]:
            print(f"          {e}")

    for chemin, cle, va, vb in r["fond"]:
        print(f"\n      {chemin}")
        print(f"          {cle}")
        print(f"          {ref_a} : {va[:100]}")
        print(f"          {ref_b} : {vb[:100]}")

    _lister("apparues", r["apparues"])
    _lister("disparues", r["disparues"])

    if r["fond"] or r["illisibles"]:
        sys.exit(1)
    sys.exit(2 if r["apparues"] or r["disparues"] else 0)


if __name__ == "__main__":
    main()
