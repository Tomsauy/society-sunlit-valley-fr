"""Contrôle terminologie : un terme imposé (termes_imposes.json) est employé partout où l'anglais
emploie le terme source, champs des livres compris. Bloquant sur un nom d'objet, signalé sur un texte, où
une reformulation peut être voulue. Une forme imposée écrite avec sa majuscule (STYLE §7 : « Maîtrise du
minage ») la garde.

Un rendu interdit (« interdits ») resté dans un texte où l'anglais emploie le terme, dans la portée de l'entrée, est
bloquant, nom ou texte : c'est un ancien rendu que le terme imposé remplace. Il se compare comme la forme imposée, aux
pluriels, accents et casse près ; ses mots qui ne figurent qu'à l'intérieur d'une forme imposée (« clé » dans « mot
clé ») ne comptent pas. Son objet, « anglais ≠ interdit », le distingue du constat de forme absente. Règle en
attente (regles.json : terminologie_interdits), activée une fois les anciens rendus relevés corrigés."""
from __future__ import annotations

import re

from ..corpus import affichee
from ..modele import BLOQUANT, SIGNALE, Constat
from ..texte import contient_mots, jetons, mots

NOM = "terminologie"


def verifier(corpus, registre, config, options) -> list:
    avec_interdits = config.regle("terminologie_interdits", options)
    termes = []
    for t in config.termes_imposes:
        formes = t["francais"] if isinstance(t["francais"], list) else [t["francais"]]
        termes.append((t, formes, [mots(f) for f in formes], re.compile(rf"\b(?:{t['anglais']})\b", re.I),
                       re.compile(t["cles"]) if t.get("cles") else None,
                       [(i, mots(i)) for i in t.get("interdits", [])] if avec_interdits else []))
    constats = []
    for cle, fr, en, est_nom in _textes(corpus, registre):
        mots_fr = mots(fr)
        for terme, formes, formes_mots, anglais, filtre, interdits in termes:
            portee = terme.get("portee", "tout")
            if (portee == "noms" and not est_nom) or (portee == "textes" and est_nom):
                continue
            if filtre and not filtre.search(cle):
                continue
            if not anglais.search(en):
                continue
            for interdit, interdit_mots in interdits:
                if _interdit_present(mots_fr, interdit_mots, formes_mots):
                    constats.append(Constat(NOM, cle, BLOQUANT, actuel=fr, attendu=formes[0],
                                            objet=f"{terme['anglais']} ≠ {interdit}", preuve=terme.get("motif", ""),
                                            detail=f"« {interdit} » est un rendu interdit de « {terme['anglais']} », "
                                                   f"qui se traduit « {' / '.join(formes)} »"))
            statut = BLOQUANT if est_nom else SIGNALE
            if not any(contient_mots(mots_fr, f) for f in formes_mots):
                constats.append(Constat(NOM, cle, statut, actuel=fr, attendu=formes[0],
                                        objet=terme["anglais"], preuve=terme.get("motif", ""),
                                        detail=f"« {terme['anglais']} » se traduit « {' / '.join(formes)} »"))
                continue
            perdue = _majuscule_perdue(fr, formes)
            if perdue:
                constats.append(Constat(NOM, cle, statut, actuel=fr, attendu=perdue, objet=terme["anglais"],
                                        preuve=terme.get("motif", ""),
                                        detail=f"« {terme['anglais']} » s'écrit « {perdue} », avec sa majuscule"))
    return constats


def _textes(corpus, registre):
    """(clé, français, anglais, est un nom) du français effectif hors vanilla, puis des champs de livres."""
    for cle, fr in sorted(corpus.fr.items()):
        if fr and affichee(cle) and corpus.origine_fr.get(cle) != "vanilla":
            en = corpus.anglais(cle)
            if en:
                yield cle, fr, en, cle in registre.noms
    for champ in corpus.livres:
        if champ.fr and champ.en:
            yield champ.cle, champ.fr, champ.en, False


def _interdit_present(mots_fr: tuple, interdit: tuple, formes_mots) -> bool:
    """L'interdit figure-t-il dans le texte hors des occurrences d'une forme imposée qui le contiennent ?"""
    n = len(interdit)
    if not n:
        return False
    couverts = set()
    for forme in formes_mots:
        m = len(forme)
        if m and contient_mots(forme, interdit):
            for i in range(len(mots_fr) - m + 1):
                if mots_fr[i:i + m] == forme:
                    couverts.update(range(i, i + m))
    return any(mots_fr[i:i + n] == interdit and not couverts.issuperset(range(i, i + n))
               for i in range(len(mots_fr) - n + 1))


def _majuscule_perdue(fr: str, formes) -> str:
    """La forme imposée à majuscule (« Maîtrise du minage ») que le texte n'écrit qu'en minuscule ; sinon ""."""
    suite = jetons(fr)
    for forme in formes:
        if not forme[:1].isupper():
            continue
        cible = mots(forme)
        n = len(cible)
        ecrits = [suite[i][1] for i in range(len(suite) - n + 1) if tuple(m for m, _, _ in suite[i:i + n]) == cible]
        if ecrits and not any(e[:1].isupper() for e in ecrits):
            return forme
    return ""
