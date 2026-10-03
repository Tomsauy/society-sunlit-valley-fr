"""Largeur du texte dans la police de Minecraft, en pixels, espacement d'un pixel compris."""
from __future__ import annotations

import re
import unicodedata

LARGEURS = {" ": 4, "f": 5, "i": 2, "k": 5, "l": 3, "t": 4, "I": 4, "'": 3, ".": 2, ",": 2, ":": 2,
            "!": 2, ";": 2, "|": 2}
FORMATAGE = re.compile(r"§.")


def px(texte: str) -> int:
    """Largeur d'un texte ; une lettre accentuée a la largeur de la lettre nue ; §x ne compte pas."""
    return sum(LARGEURS.get(unicodedata.normalize("NFD", c)[0], 6) for c in FORMATAGE.sub("", texte))


def lignes(texte: str, largeur: int = 102) -> int:
    """Nombre de lignes après repli par mot dans une boîte de `largeur` pixels (boutique : 102)."""
    n, courante = 1, 0
    for mot in FORMATAGE.sub("", texte).split(" "):
        l = px(mot)
        if courante == 0:
            courante = l
        elif courante + 4 + l <= largeur:
            courante += 4 + l
        else:
            n, courante = n + 1, l
    return n
