"""La mesure d'un sous-lot (spec 2 §4, étape 1) : son périmètre vient du vérificateur, jamais de celui qui propose."""
from __future__ import annotations

import json
from pathlib import Path

ANNEXE = Path("docs/specs/2026-09-30-fiche-decisions.json")
# Contrôles dont l'attendu est le texte corrigé en entier (spec 2 §4 : remplacements sûrs). S'y ajoutent les
# conventions dont l'attendu est écrit et les formes interdites du contrôle orthographe.
ATTENDU_COMPLET = frozenset({"accents", "casse", "decisions", "familles"})


def cles_des_questions(depot, questions) -> set:
    """Les clés concernées par ces questions de la fiche (annexe de la spec 2)."""
    annexe = json.loads((Path(depot) / ANNEXE).read_text(encoding="utf-8"))
    par_id = {q["id"]: q for q in annexe["questions"]}
    inconnues = sorted(set(questions) - set(par_id))
    if inconnues:
        raise ValueError(f"question inconnue de l'annexe : {', '.join(inconnues)}")
    return {cle for q in questions for cle in par_id[q].get("cles", [])}


def selectionner(resultat, controles=(), cles=(), bloquants_seulement=False) -> list:
    """Les constats du sous-lot, bloquants, en dette et signalés (ou les bloquants seuls : ceux qu'une règle retirée
    ou activée fait naître) : ceux des contrôles demandés et ceux des clés demandées."""
    controles, cles = set(controles), set(cles)
    tous = list(resultat.bloquants)
    if not bloquants_seulement:
        tous += list(resultat.en_dette) + list(resultat.signales)
    return [c for c in tous if c.controle in controles or c.cle in cles]


def premier_paquet(constats, taille, par_objet) -> list:
    """Les premiers groupes de constats, par objet cité (références) ou par clé, qui tiennent en `taille` ; un
    groupe plus grand que `taille` est coupé (spec 2 §4 : 150 actions au plus par sous-lot)."""
    groupes = {}
    for c in sorted(constats, key=lambda c: (str(c.objet) if par_objet else "", c.cle, c.controle)):
        groupes.setdefault(str(c.objet) if par_objet else c.cle, []).append(c)
    paquet = []
    for groupe in groupes.values():
        if len(paquet) + len(groupe) <= taille:
            paquet += groupe
        elif not paquet:
            return groupe[:taille]
        else:
            break
    return paquet


def squelette(lot_id, nature, criteres, constats, cles_en_plus, dette) -> dict:
    """Le fichier de lot tel que la mesure le laisse : périmètre, constats retenus, actions vides."""
    return {
        "lot": lot_id,
        "nature": nature,
        "mesure": {"criteres": criteres, "dette": len(dette), "constats": len(constats)},
        "perimetre": sorted({c.cle for c in constats} | set(cles_en_plus)),
        "constats": [c.en_dict() for c in constats],
        "actions": [],
    }


def attendus_surs(constats, texte_de, formes_interdites=()) -> tuple:
    """Les corrections que les constats donnent en entier. Une clé à plusieurs constats, dont l'attendu n'est pas
    sûr, ou absente du français (texte_de rend None), est laissée à la main. Rend (actions, clés laissées)."""
    par_cle = {}
    for c in constats:
        par_cle.setdefault(c.cle, []).append(c)
    actions, laissees = [], []
    for cle, liste in sorted(par_cle.items()):
        c = liste[0]
        sur = (c.controle in ATTENDU_COMPLET or (c.controle == "conventions" and c.attendu)
               or (c.controle == "orthographe" and c.objet in formes_interdites))
        actuel = texte_de(cle)
        if len(liste) > 1 or not sur or not c.attendu or actuel is None or c.attendu == actuel:
            laissees.append(cle)
            continue
        actions.append({"type": "correction", "cle": cle, "avant": actuel, "apres": c.attendu,
                        "motif": f"[{c.controle}] {c.detail}".strip()})
    return actions, laissees
