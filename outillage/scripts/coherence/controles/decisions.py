"""Contrôle decisions : chaque clé dont provenance.json fixe une valeur a cette valeur. Une
correction, même de sens, ne peut plus être défaite en silence : changer une clé tracée demande une
nouvelle décision, avec son motif. Les champs de livres se tracent sous leur clé du vérificateur,
« <livre>/<fichier>#/<pointeur> » (almanac/entries/animals/cow.json#/pages/0/text)."""
from __future__ import annotations

from ..corpus import CLE_JOURNAL
from ..modele import BLOQUANT, Constat

NOM = "decisions"


def valeur_decidee(decisions):
    """Le français de la dernière décision qui en fixe un ; None si aucune n'en fixe."""
    for decision in reversed(decisions if isinstance(decisions, list) else []):
        if isinstance(decision, dict) and "fr" in decision:
            return decision["fr"]
    return None


def valeur_actuelle(corpus, cle):
    """Le français d'une clé tracée — clé de langue ou champ de livre — ; None si le jeu ne l'affiche pas : clé
    absente du français, champ que le livre anglais n'a pas. Le journal des modifications se trace sous « journal »,
    la clé que lui donnent le vérificateur et l'applicateur des lots."""
    if cle == CLE_JOURNAL:
        return corpus.journal_fr or None
    if "#" in cle:
        champ = corpus.champ(cle)
        return None if champ is None else champ.fr
    return corpus.fr.get(cle)


def verifier(corpus, registre, config, options) -> list:
    constats = []
    for cle, decisions in sorted(config.provenance.get("cles", {}).items()):
        decidee = valeur_decidee(decisions)
        if decidee is None:
            continue
        actuel = valeur_actuelle(corpus, cle)
        if actuel is None:
            constats.append(Constat(NOM, cle, BLOQUANT, attendu=decidee,
                                    detail="clé tracée absente du français : l'écrire si elle s'affiche en jeu, "
                                           "sinon la déplacer dans cles_mortes_ecartees"))
        elif actuel != decidee:
            constats.append(Constat(NOM, cle, BLOQUANT, actuel=actuel, attendu=decidee,
                                    detail="valeur différente de la décision tracée : restaurer, "
                                           "ou tracer une nouvelle décision avec son motif"))
    return constats
