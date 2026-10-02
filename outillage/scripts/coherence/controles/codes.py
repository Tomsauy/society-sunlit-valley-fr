"""Contrôle codes : mêmes codes en anglais et en français — clés du projet, livres, journal."""
from __future__ import annotations

import re
from collections import Counter

from validate_translation import TOKEN

from ..corpus import CLE_JOURNAL
from ..modele import BLOQUANT, Constat

NOM = "codes"
LIGNE_DE_STRUCTURE = re.compile(r"^(#+|\^\^\^|---|- )")


def ecart(en: str, fr: str) -> str:
    """Les codes perdus et ajoutés, en clair ; vide si les deux textes portent les mêmes."""
    a, b = Counter(TOKEN.findall(en)), Counter(TOKEN.findall(fr))
    if a == b:
        return ""
    morceaux = []
    if a - b:
        morceaux.append("perdus : " + " ".join(sorted((a - b).elements())))
    if b - a:
        morceaux.append("ajoutés : " + " ".join(sorted((b - a).elements())))
    return " ; ".join(morceaux).replace("\n", "\\n")


def structure(journal: str) -> list:
    """Titres, séparateurs et puces du journal, dans l'ordre."""
    return [m.group(1) for m in (LIGNE_DE_STRUCTURE.match(l) for l in journal.splitlines()) if m]


def verifier(corpus, registre, config, options) -> list:
    constats = []
    for cle, fr in corpus.textes_projet():
        en = corpus.anglais(cle)
        d = ecart(en, fr) if en else ""
        if d:
            constats.append(Constat(NOM, cle, BLOQUANT, actuel=fr, attendu=en, detail=d))
    for champ in corpus.livres:
        d = ecart(champ.en, champ.fr) if champ.fr else ""
        if d:
            constats.append(Constat(NOM, champ.cle, BLOQUANT, actuel=champ.fr, attendu=champ.en, detail=d))
    if corpus.journal_en and corpus.journal_fr:
        a, b = structure(corpus.journal_en), structure(corpus.journal_fr)
        if a != b:
            i = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            constats.append(Constat(NOM, CLE_JOURNAL, BLOQUANT,
                                    detail=f"structure différente de l'anglais dès la ligne de structure {i + 1} "
                                           f"({len(a)} en anglais, {len(b)} en français)"))
    return constats
