"""Contrôle familles : chaque nom d'une famille dérivée est égal au rendu de son gabarit."""
from __future__ import annotations

from ..modele import BLOQUANT, Constat
from ..regles_derivees import Familles

NOM = "familles"


def verifier(corpus, registre, config, options) -> list:
    familles = Familles(corpus, config)
    constats = []
    for cle in sorted(familles.membres):
        actuel = corpus.fr.get(cle)
        if not actuel:
            continue  # absente du français : la couverture le signale, le générateur la produit
        famille = familles.membres[cle][0]["nom"]
        attendu = familles.attendu(cle)
        if attendu is None:
            constats.append(Constat(NOM, cle, BLOQUANT, actuel=actuel,
                                    detail=f"famille {famille} : {familles.problemes[cle]}"))
        elif actuel != attendu:
            constats.append(Constat(NOM, cle, BLOQUANT, actuel=actuel, attendu=attendu,
                                    detail=f"famille {famille}"))
    return constats
