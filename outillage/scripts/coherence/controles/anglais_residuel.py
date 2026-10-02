"""Contrôle anglais_residuel : l'anglais laissé tel quel.

- dans un nom d'objet, un mot de l'anglais recopié (« Noir Sharestone », « Foul Berries ») ;
- dans un texte, le texte entier resté en anglais, sauf décision « garder l'anglais » tracée ;
- partout, une étiquette brute affichée (« #botania:generating_special »).

Un mot est tenu pour français s'il figure dans le français de Mojang, dans un français dont
l'anglais ne le contient pas (un traducteur l'a choisi), dans le vocabulaire des accents ou dans le
glossaire ; un chiffre romain (« XXXVIII ») n'est d'aucune langue. Sont exemptés : KEEP-ENGLISH,
noms_propres.json, les termes que le glossaire garde en anglais et les noms des PNJ. Un mot seul l'est
partout ; un nom de plusieurs mots (« Villagers Fright »), là seulement où il figure en entier.
"""
from __future__ import annotations

import re

from ..corpus import affichee
from ..modele import BLOQUANT, Constat
from ..registre import CLE_OBJET
from ..texte import mots, sans_codes

NOM = "anglais_residuel"
ETIQUETTE = re.compile(r"#[a-z0-9_.-]+:[a-z0-9_/.-]+")
# Un nombre romain bien formé, en minuscules (mots() plie la casse).
ROMAIN = re.compile(r"m{0,4}(?:cm|cd|d?c{0,3})(?:xc|xl|l?x{0,3})(?:ix|iv|v?i{0,3})")


def _textes(corpus):
    """(clé, français, anglais, origine) du français effectif et des livres."""
    for cle, fr in sorted(corpus.fr.items()):
        if fr and affichee(cle):
            yield cle, fr, corpus.anglais(cle), corpus.origine_fr.get(cle, "")
    for champ in corpus.livres:
        if champ.fr:
            yield champ.cle, champ.fr, champ.en, "livre"


def lexique(corpus, config) -> set:
    """Les mots tenus pour français."""
    francais = set()
    for _, fr, en, origine in _textes(corpus):
        francais.update(mots(fr) if origine == "vanilla" else set(mots(fr)) - set(mots(en)))
    francais.update(m for pli in config.vocabulaire for m in mots(pli))
    francais.update(m for e in config.glossaire() if not e.get("garde_anglais") for m in mots(e.get("fr", "")))
    return francais


def exemptes(config, registre) -> tuple:
    """Les termes anglais gardés à dessein (KEEP-ENGLISH, noms propres, glossaire, noms des PNJ) : les mots
    seuls, exemptés partout, et les noms de plusieurs mots en une expression régulière, ou None. Ceux-là
    ne s'exemptent que là où ils figurent en entier : « Villagers Fright » n'exempte pas « Villager »."""
    termes = config.termes_gardes() + (registre.noms_de_pnj() if registre is not None else [])
    seuls, expressions = set(), set()
    for terme in termes:
        trouves = mots(terme)
        if len(trouves) == 1:
            seuls.add(trouves[0])
        elif trouves:
            expressions.add(terme.strip())
    if not expressions:
        return seuls, None
    ordre = sorted(expressions, key=len, reverse=True)
    return seuls, re.compile(r"(?<!\w)(?:" + "|".join(map(re.escape, ordre)) + r")(?!\w)")


def gardees(config) -> set:
    """Les clés dont une décision tracée garde l'anglais."""
    return {cle for cle, decisions in config.provenance.get("cles", {}).items()
            if any(isinstance(d, dict) and d.get("decision") == "garde_anglais" for d in decisions)}


def verifier(corpus, registre, config, options) -> list:
    francais, a_garder = lexique(corpus, config), gardees(config)
    exempts, expressions = exemptes(config, registre)

    def etranger(mot: str) -> bool:
        return (len(mot) >= 4 and mot.isalpha() and mot not in francais and mot not in exempts
                and not ROMAIN.fullmatch(mot))

    constats = []
    for cle, fr, en, origine in _textes(corpus):
        if origine == "vanilla":
            continue
        details = []
        visibles = expressions.sub(" ", fr) if expressions else fr
        if CLE_OBJET.match(cle):
            restes = sorted(m for m in set(mots(visibles)) & set(mots(en)) if etranger(m))
            if restes:
                details.append("mots anglais recopiés : " + ", ".join(restes))
        elif fr.strip() == en.strip() and cle not in a_garder and any(etranger(m) for m in mots(visibles)):
            details.append("texte resté en anglais")
        etiquettes = ETIQUETTE.findall(sans_codes(fr))
        if etiquettes:
            details.append("étiquette brute affichée : " + ", ".join(etiquettes))
        if details:
            constats.append(Constat(NOM, cle, BLOQUANT, actuel=fr, detail=" ; ".join(details)))
    return constats
