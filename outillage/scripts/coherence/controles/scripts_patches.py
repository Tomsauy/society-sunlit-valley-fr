"""Contrôle scripts_patches : un script de l'amont que nous patchons n'a pas changé dans l'amont
depuis le patch. Sinon, refusionner traduction-fr avant de distribuer, puis mettre à jour la base."""
from __future__ import annotations

from ..modele import BLOQUANT, Constat

NOM = "scripts_patches"


def verifier(corpus, registre, config, options) -> list:
    constats = []
    for chemin, entree in sorted(config.scripts_patches.items()):
        if corpus.scripts_amont is None:
            constats.append(Constat(NOM, chemin, BLOQUANT, preuve="origin/master",
                                    detail="amont illisible : git a échoué (hors d'un clone, ou sans origin/master) ; "
                                           "impossible de vérifier la base du patch"))
            continue
        amont = corpus.scripts_amont.get(chemin)
        if amont is None:
            constats.append(Constat(NOM, chemin, BLOQUANT, preuve="origin/master",
                                    detail="script introuvable dans l'amont : retiré ou renommé ; revoir le patch"))
        elif amont != entree["base"]:
            constats.append(Constat(NOM, chemin, BLOQUANT, actuel=amont, attendu=entree["base"], preuve="origin/master",
                                    detail=f"l'amont a modifié ce script depuis le patch (base {entree['base'][:9]}, "
                                           f"amont {amont[:9]}) : refusionner traduction-fr, puis mettre à jour la base"))
    return constats
