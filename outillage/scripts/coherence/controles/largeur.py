"""Contrôle largeur : un nom vendu en boutique tient en deux lignes de 102 px ; un libellé de
largeurs.json tient sous sa limite. Mesure dans la police du jeu (coherence/police.py)."""
from __future__ import annotations

from ..modele import BLOQUANT, SIGNALE, Constat
from ..police import lignes, px

NOM = "largeur"


def verifier(corpus, registre, config, options) -> list:
    constats = []
    for ident in sorted(corpus.vendus):
        ns, _, chemin = ident.partition(":")
        cle = next((c for c in (f"item.{ns}.{chemin}", f"block.{ns}.{chemin}") if corpus.fr.get(c)), None)
        if cle and lignes(corpus.fr[cle]) > 2:
            statut = BLOQUANT if corpus.origine_fr.get(cle) == "projet" else SIGNALE
            constats.append(Constat(NOM, cle, statut, actuel=corpus.fr[cle],
                                    detail=f"{lignes(corpus.fr[cle])} lignes dans la boîte de 102 px de la boutique, "
                                           "deux au plus"))
    for entree in config.largeurs:
        fr = corpus.fr.get(entree["cle"], "")
        if px(fr) > entree["limite"]:
            constats.append(Constat(NOM, entree["cle"], BLOQUANT, actuel=fr, preuve=entree.get("motif", ""),
                                    detail=f"{px(fr)} px pour {entree['limite']} au plus"))
    return constats
