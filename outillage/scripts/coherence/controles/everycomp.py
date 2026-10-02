"""Contrôle everycomp : chaque essence de bois ou de feuilles activée (wood_type, leaves_type) a son nom français,
chaque gabarit block_type aussi ; les autres registres que le toml active n'ont pas de nom traduit.

Vérifié dans le bytecode de Moonlight : faute de clé wood_type/leaves_type française, le nom
anglais de l'essence est injecté dans le gabarit français (« Placard en Rosewood »).
"""
from __future__ import annotations

from ..modele import BLOQUANT, Constat

NOM = "everycomp"
# Seules les essences de bois et de feuilles ont un nom traduit (wood_type.<mod>.<essence>). Le toml
# liste aussi les autres registres de Moonlight, comme les gâteaux d'Amendments, lus sous la clé
# fixe « cake » (bytecode de CakeRegistry$CakeType).
ESSENCES_NOMMEES = ("wood_type.", "leaves_type.")


def verifier(corpus, registre, config, options) -> list:
    constats = []
    for essence in corpus.essences:
        if essence.startswith(ESSENCES_NOMMEES) and not corpus.fr.get(essence):
            constats.append(Constat(NOM, essence, BLOQUANT, preuve="config/everycomp-entries.toml",
                                    detail="essence activée sans nom français : ses blocs s'afficheraient avec l'anglais"))
    for cle in sorted(corpus.en):
        if cle.startswith("block_type.") and corpus.anglais(cle) and not corpus.fr.get(cle):
            constats.append(Constat(NOM, cle, BLOQUANT, attendu=corpus.anglais(cle),
                                    detail="gabarit Every Compat sans français"))
    return constats
