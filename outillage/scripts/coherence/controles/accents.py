"""Contrôle accents : aucun mot du vocabulaire figé écrit sans ses accents.

Le vocabulaire (fr-workspace/accents/vocabulaire.json) associe à chaque mot plié ses formes justes.
Un mot à forme unique accentuée se vérifie partout — sauf les homographes (« mais »/« maïs »,
« taille »/« taillé ») : attestés sans accent dans le français de Mojang ou déclarés dans
homographes.json, ils ne se vérifient que dans les noms d'objets, pour lesquels le vocabulaire a été
établi. Un mot qui porte un accent là où la forme figée n'en a pas est un autre mot (« acheté » /
« achète », « pêché » / « pêche ») ; tout autre écart d'accent est une faute. Les mots à double sens
(séché/sèche) se vérifient contre l'anglais, d'après double_sens.json ; quand l'anglais porte les deux
sens, les deux formes sont justes. Un nom propre de plusieurs mots (« Cozy Cafe ») est exempté là où il
figure en entier : ses mots restent vérifiés ailleurs.
"""
from __future__ import annotations

import re

from compare_accents import plier

from ..corpus import CLE_JOURNAL
from ..modele import BLOQUANT, Constat
from ..registre import CLE_OBJET
from ..texte import meme_casse, sans_codes

NOM = "accents"
MOT = re.compile(r"[^\W\d_]+")


def formes_uniques(config) -> dict:
    """Mot plié -> sa seule forme juste, pour les mots du vocabulaire qui n'en ont qu'une, accentuée."""
    formes = {}
    for pli, entrees in config.vocabulaire.items():
        uniques = {e["forme"] for e in entrees}
        if len(uniques) == 1 and next(iter(uniques)) != pli:
            formes[pli] = next(iter(uniques))
    return formes


def homographes(corpus, config, formes) -> set:
    """Les mots dont la forme sans accent est aussi du français : attestée chez Mojang, ou déclarée."""
    mojang = {m.lower() for cle, fr in corpus.fr.items() if corpus.origine_fr.get(cle) == "vanilla"
              for m in MOT.findall(sans_codes(fr))}
    return {pli for pli in formes if pli in mojang} | set(config.homographes)


def exemptes(config) -> set:
    return {plier(m) for m in config.noms_propres} | {plier(t) for t in config.garder_anglais}


def expressions(config):
    """Les noms propres et termes gardés en anglais de plusieurs mots, en une expression régulière, ou None.
    Pliés d'un bloc, ils ne rencontreraient jamais un mot seul dans `exemptes`."""
    termes = sorted({t for t in list(config.noms_propres) + list(config.garder_anglais) if len(t.split()) > 1},
                    key=len, reverse=True)
    return re.compile(r"(?<!\w)(?:" + "|".join(map(re.escape, termes)) + r")(?!\w)") if termes else None


def _lettres(mot: str) -> list:
    """(lettre de base, lettre écrite) de chaque lettre du mot en minuscules ; une ligature compte pour
    ses lettres de base, sans accent."""
    lettres = []
    for ecrite in mot.lower():
        base = plier(ecrite)
        lettres += [(b, ecrite if len(base) == 1 else b) for b in base]
    return lettres


def accent_fautif(mot: str, juste: str) -> bool:
    """Le mot, de même pli que sa forme juste, s'en écarte-t-il par ses accents (oublié ou erroné) ? Pas
    s'il porte un accent là où elle n'en a pas : c'est alors un autre mot (« acheté » pour « achète »)."""
    if mot.lower() == juste.lower():
        return False
    return not any(ecrite != base and attendue == base
                   for (base, ecrite), (_, attendue) in zip(_lettres(mot), _lettres(juste)))


def verifier(corpus, registre, config, options) -> list:
    formes = formes_uniques(config)
    gardes, a_verifier_dans_les_noms = exemptes(config), homographes(corpus, config, formes)
    masque = expressions(config)
    regles = [(re.compile(rf"\b(?:{r['anglais']})\b", re.I), {plier(j): j for j in r["justes"]})
              for r in config.double_sens]
    constats = []
    for cle, en, fr in _textes(corpus):
        fautes = {}
        texte = masque.sub(" ", sans_codes(fr)) if masque else sans_codes(fr)
        mots, dans_un_nom = MOT.findall(texte), bool(CLE_OBJET.match(cle))
        plis = [plier(mot) for mot in mots]
        for mot, pli in zip(mots, plis):
            juste = formes.get(pli)
            if (juste and pli not in gardes and (dans_un_nom or pli not in a_verifier_dans_les_noms)
                    and accent_fautif(mot, juste)):
                fautes[mot] = meme_casse(mot, juste)
        tranches = {}  # mot plié -> ses formes justes, d'après chaque sens que porte l'anglais
        for anglais, justes in regles:
            if en and anglais.search(en):
                for pli, juste in justes.items():
                    tranches.setdefault(pli, []).append(juste)
        if tranches:
            for mot, pli in zip(mots, plis):
                justes = tranches.get(pli)
                if justes and mot.lower() not in justes:
                    fautes[mot] = meme_casse(mot, justes[0])
        if fautes:
            attendu = fr
            for mot, juste in fautes.items():
                attendu = re.sub(rf"(?<!\w){re.escape(mot)}(?!\w)", juste, attendu)
            constats.append(Constat(NOM, cle, BLOQUANT, actuel=fr, attendu=attendu,
                                    detail=", ".join(f"« {m} » → « {j} »" for m, j in fautes.items())))
    return constats


def _textes(corpus):
    for cle, fr in corpus.textes_projet():
        yield cle, corpus.anglais(cle), fr
    for champ in corpus.livres:
        yield champ.cle, champ.en, champ.fr
    yield CLE_JOURNAL, corpus.journal_en, corpus.journal_fr
