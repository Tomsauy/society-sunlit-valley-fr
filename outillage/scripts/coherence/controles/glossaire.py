"""Contrôle glossaire : le glossaire de provenance.json dit ce que la traduction dit vraiment.

Un terme du glossaire dont l'anglais est aussi, mot pour mot, l'anglais entier d'un texte du projet doit être le
français d'au moins un de ces textes ; sans quoi le glossaire et la traduction se sont écartés, et le prochain
lot de corrections ramènerait l'ancienne forme. Un même anglais peut porter plusieurs entrées, une par sens (« Jar » :
« Pot » ou « Bocal ») : une seule suffit. Seuls comptent les textes du projet et les champs des livres — le français
de Mojang et celui que les mods embarquent ne sont pas les nôtres. L'anglais se compare à la casse près (« ADD » et
« Add » sont deux termes), le français sans la casse, la ponctuation finale ni le pluriel des mots (une étiquette
`tag.*` nomme un groupe au pluriel : « Graviers » pour « Gravel »).

Deux entrées de même anglais et de même sens qui se contredisent bloquent aussi : le glossaire ne dirait plus rien.

Le glossaire suit aussi les conventions de la traduction : « oe », jamais la ligature (CLAUDE.md)."""
from __future__ import annotations

import re

from ..corpus import affichee
from ..modele import BLOQUANT, Constat

NOM = "glossaire"
LIGATURES = re.compile("[œŒ]")


def verifier(corpus, registre, config, options) -> list:
    textes = _textes(corpus)
    entrees = {}
    for e in config.glossaire():
        entrees.setdefault(e.get("en", "").strip(), []).append(e)
    constats = []
    for en, es in sorted(entrees.items()):
        for e in es:
            if LIGATURES.search(e.get("fr", "")):
                constats.append(Constat(NOM, f"glossaire:{en}", BLOQUANT, actuel=e["fr"], objet=en,
                                        attendu=LIGATURES.sub(lambda m: "oe" if m.group() == "œ" else "Oe", e["fr"]),
                                        detail="le glossaire écrit la ligature ; la traduction écrit « oe »"))
        par_sens = {}
        for e in es:
            par_sens.setdefault(e.get("sens", ""), set()).add(_forme(e.get("fr", "")))
        for sens, formes in sorted(par_sens.items()):
            if len(formes) > 1:
                constats.append(Constat(NOM, f"glossaire:{en}", BLOQUANT, objet=en,
                                        actuel=" / ".join(e.get("fr", "") for e in es if e.get("sens", "") == sens),
                                        detail="deux entrées de même anglais et de même sens se contredisent"
                                               + (f" (sens : {sens})" if sens else "")))
        vus = textes.get(en)
        if not vus or any(_forme(e.get("fr", "")) in {_forme(fr) for _, fr in vus} for e in es):
            continue
        cle, fr = vus[0]
        constats.append(Constat(NOM, cle, BLOQUANT, actuel=fr, attendu=" / ".join(e.get("fr", "") for e in es),
                                objet=en, preuve="provenance.json (glossaire)",
                                detail=f"le glossaire traduit « {en} » autrement que les {len(vus)} texte(s) du jeu "
                                       f"de même anglais : corriger le glossaire, ou ajouter le sens qui manque"))
    return constats


def _textes(corpus) -> dict:
    """Anglais entier (bords nettoyés) → [(clé, français)] des textes du projet et des champs de livres."""
    textes = {}
    for cle, fr in sorted(corpus.fr.items()):
        if fr and affichee(cle) and corpus.origine_fr.get(cle) == "projet":
            en = corpus.anglais(cle)
            if en and en.strip():
                textes.setdefault(en.strip(), []).append((cle, fr))
    for champ in corpus.livres:
        if champ.fr and champ.en and champ.en.strip():
            textes.setdefault(champ.en.strip(), []).append((champ.cle, champ.fr))
    return textes


def _forme(texte: str) -> str:
    """Le français comparé : sans casse, sans ponctuation finale, chaque mot au singulier (s ou x final retiré)."""
    texte = re.sub(r"[\s.!:]+$", "", texte.strip().lower())
    return re.sub(r"(\w{3,}?)[sx]\b", r"\1", texte)
