#!/usr/bin/env python3
"""Applique les règles des familles dérivées (fr-workspace/coherence/familles.json).

    python3 fr-workspace/scripts/generer_derives.py                  # diff ; rien n'est écrit
    python3 fr-workspace/scripts/generer_derives.py --appliquer      # fr_fr.json et provenance.json
    python3 fr-workspace/scripts/generer_derives.py --famille oeufs --appliquer
    python3 fr-workspace/scripts/generer_derives.py --proposer       # sources et accords devinés

Refuse d'écrire un nom sans genre de source, ou un nom vendu en boutique qui dépasserait deux
lignes de 102 px. Ne défait rien de ce qu'un humain a fixé (spec §7 et §9) : une clé couverte par
une exception `familles` est laissée (écart déclaré) ; une clé dont la dernière décision tracée
n'est pas une règle et fixe une autre valeur que le rendu, ou que la dette tient « en attente de
décision », est refusée. `--forcer` passe outre, explicitement. Code de retour 1 s'il y a un refus,
même quand le reste a été écrit.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ESPACE = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from coherence import config as config_mod  # noqa: E402
from coherence import corpus as corpus_mod  # noqa: E402
from coherence import rapport  # noqa: E402
from coherence.controles.decisions import valeur_decidee  # noqa: E402
from coherence.controles.familles import NOM as FAMILLES  # noqa: E402
from coherence.modele import BLOQUANT, Constat  # noqa: E402
from coherence.police import lignes  # noqa: E402
from coherence.registre import CLE_OBJET, Registre  # noqa: E402
from coherence.regles_derivees import Familles, rendre  # noqa: E402
from coherence.texte import mots  # noqa: E402
from verifier import racine_par_defaut  # noqa: E402

COMBINAISONS = (("m", "s"), ("f", "s"), ("m", "p"), ("f", "p"))


def propositions(corpus, config, familles=None, forcer=False):
    """(écritures [(clé, actuel, attendu, famille)], refus [(clé, raison)], laissées [(clé, motif)]).

    Laissées : les clés qu'une exception `familles` couvre, comme le vérificateur l'applique (écart déclaré).
    Refusées, en plus des noms impossibles à rendre : une clé dont la dernière décision tracée n'est pas une
    règle et fixe une autre valeur que le rendu, une clé que la dette tient en attente de décision. `forcer`
    lève ces trois gardes."""
    f = Familles(corpus, config)
    ecritures, refus, laissees = [], [], []
    candidates = []
    for cle in sorted(f.membres):
        famille = f.membres[cle][0]["nom"]
        if familles and famille not in familles:
            continue
        attendu, actuel = f.attendu(cle), corpus.fr.get(cle, "")
        if attendu is None:
            refus.append((cle, f.problemes[cle]))
            continue
        if attendu == actuel:
            continue
        m = CLE_OBJET.match(cle)
        if m and f"{m.group(2)}:{m.group(3)}" in corpus.vendus and lignes(attendu) > 2:
            refus.append((cle, f"« {attendu} » dépasse deux lignes de 102 px en boutique"))
            continue
        candidates.append((cle, actuel, attendu, famille))
    ecarts = {} if forcer else _ecarts_declares(config, [cle for cle, *_ in candidates])
    en_attente = {} if forcer else _en_attente(config)
    cles_tracees = config.provenance.get("cles", {})
    for cle, actuel, attendu, famille in candidates:
        if cle in ecarts:
            laissees.append((cle, ecarts[cle]))
            continue
        raison = None if forcer else _decision_contraire(cles_tracees.get(cle), attendu)
        if raison is None and cle in en_attente:
            raison = (f"en attente de décision (dette : {', '.join(sorted(en_attente[cle]))}) : la fiche de "
                      "décisions tranche, puis --forcer")
        if raison:
            refus.append((cle, raison))
            continue
        ecritures.append((cle, actuel, attendu, famille))
    return ecritures, sorted(refus), laissees


def _ecarts_declares(config, cles) -> dict:
    """Clé -> motif de l'exception `familles` qui la couvre, selon la règle du rapport du vérificateur."""
    constats = [Constat(FAMILLES, cle, BLOQUANT) for cle in cles]
    resultat = rapport.appliquer(constats, config.exceptions, [], lambda cle: "", [FAMILLES])
    return {c.cle: exc["motif"] for c, exc in resultat.couverts}


def _en_attente(config) -> dict:
    """Clé -> contrôles dont la dette tient la clé en attente de décision."""
    attente = {}
    for entree in config.dette:
        if entree.get("en_attente_de_decision"):
            attente.setdefault(entree.get("cle"), set()).add(entree.get("controle", ""))
    return attente


def _decision_contraire(decisions, attendu):
    """La raison du refus quand la dernière décision tracée n'est pas une règle et fixe une autre valeur que le
    rendu (ou n'en fixe aucune, comme « garder l'anglais ») ; None sinon."""
    decisions = [d for d in decisions or [] if isinstance(d, dict)]
    if not decisions or decisions[-1].get("type") == "regle":
        return None
    decidee = valeur_decidee(decisions)
    if decidee == attendu:
        return None
    fixee = f"fixe « {decidee} »" if decidee is not None else "ne fixe aucune valeur"
    return (f"décision tracée ({decisions[-1].get('type', '?')}) : elle {fixee}, la règle rendrait « {attendu} » "
            "— trancher par une nouvelle décision, puis --forcer")


def proposer(corpus, config, registre) -> dict:
    """Sources introuvables : les objets dont l'anglais correspond. Genres et pluriels manquants :
    devinés d'après les noms actuels. Tout se relit avant d'entrer dans familles.json."""
    f = Familles(corpus, config)
    connus = config.familles.get("accords", {})
    sources, votes, pluriels = {}, {}, {}
    for cle, (famille, ident) in sorted(f.membres.items()):
        nom, accord = f.source(cle)
        if nom is None:
            modeles = [m.format(id=ident) for m in famille.get("source", [])]
            # une famille en chaîne se répare à la source de sa source : rien à proposer ici
            if "anglais" in famille and not any(m in f.membres for m in modeles):
                motif = re.compile("^" + re.escape(famille["anglais"]).replace(re.escape("{source}"), "(?P<s>.+)")
                                   + "$", re.I)
                m = motif.match(corpus.anglais(cle))
                if m:
                    candidats = [n.cle for n in registre.homographes.get(mots(m.group("s")), [])]
                    sources.setdefault(famille["nom"], {})[ident] = candidats
            continue
        gabarit, actuel = famille["gabarit"], corpus.fr.get(cle)
        if not actuel or accord.get("chaine") or "cle" not in accord:
            continue
        deja = connus.get(accord["cle"], {})
        if ("{e}" in gabarit or "{s}" in gabarit) and "genre" not in deja:
            possibles = {(g, n) for g, n in COMBINAISONS if rendre(gabarit, nom, g, n) == actuel}
            votes.setdefault(accord["cle"], []).append((cle, possibles))
        if "{sources}" in gabarit and "pluriel" not in deja:
            motif = (re.escape(gabarit).replace(re.escape("de {sources}"), "d(?:e |')(?P<pl>.+)")
                     .replace(re.escape("{sources}"), "(?P<pl>.+)"))
            m = re.fullmatch(motif, actuel, re.I)
            if m:
                pluriels.setdefault(accord["cle"], set()).add(m.group("pl"))
    accords = {}
    for cle_source, liste in sorted(votes.items()):
        communs = set.intersection(*(p for _, p in liste))
        entree = accords.setdefault(cle_source, {})
        entree["depuis"] = [c for c, _ in liste]
        genres = {g for g, _ in communs}
        if len(genres) == 1:
            genre = genres.pop()
            entree.update(genre=genre, nombre="s" if (genre, "s") in communs else "p")
        else:
            entree["a_saisir"] = "les noms actuels se contredisent" if not communs else "genre indécidable"
    for cle_source, formes in sorted(pluriels.items()):
        entree = accords.setdefault(cle_source, {})
        if len(formes) == 1:
            entree["pluriel"] = formes.pop()
        else:
            entree["a_saisir_pluriel"] = "pluriels divergents : " + ", ".join(sorted(formes))
    return {"sources": sources, "accords": accords}


def ecrire_francais(corpus, racine: Path, ecritures) -> None:
    """Écrit chaque valeur dans tous les fr_fr.json qui définissent la clé, sinon dans celui du namespace."""
    fichiers_de = {}
    for ns, cle in corpus.projet:
        fichiers_de.setdefault(cle, []).append(ns)
    par_namespace = {}
    for cle, _, attendu, _ in ecritures:
        for ns in sorted(fichiers_de.get(cle) or [cle.split(".")[1]]):
            par_namespace.setdefault(ns, {})[cle] = attendu
    for ns, valeurs in sorted(par_namespace.items()):
        chemin = racine / "kubejs" / "assets" / ns / "lang" / "fr_fr.json"
        donnees = corpus_mod.lire_json(chemin)
        donnees.update(valeurs)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(json.dumps(donnees, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def tracer(espace: Path, ecritures) -> None:
    chemin = espace / "provenance.json"
    provenance = json.loads(chemin.read_text(encoding="utf-8"))
    date = datetime.date.today().isoformat()
    for cle, actuel, attendu, famille in ecritures:
        provenance["cles"].setdefault(cle, []).append(
            {"type": "regle", "famille": famille, "fr": attendu, "avant": actuel, "date": date,
             "raison": f"rendu de la famille {famille} (familles.json)"})
    chemin.write_text(json.dumps(provenance, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def action_de(cle, actuel, attendu, famille, corpus) -> dict:
    """Une écriture du générateur en action de correction pour l'applicateur (spec 2 §4 et §8)."""
    action = {"type": "correction", "cle": cle, "avant": actuel if cle in corpus.fr else None, "apres": attendu,
              "motif": f"rendu de la famille {famille} (familles.json)"}
    if cle not in corpus.fr:
        action["espace"] = cle.split(".")[1]
    return action


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Applique les règles des familles dérivées.")
    p.add_argument("--racine", type=Path)
    p.add_argument("--espace", type=Path, default=ESPACE)
    p.add_argument("--famille", action="append", help="cette famille seulement (répétable)")
    p.add_argument("--actions-dans", type=Path, metavar="LOT",
                   help="ajouter les écritures, en actions de correction, au fichier de lot LOT (spec 2 §4)")
    p.add_argument("--appliquer", action="store_true", help="écrire les fr_fr.json et provenance.json")
    p.add_argument("--forcer", action="store_true",
                   help="écrire aussi les écarts déclarés, les décisions tracées contraires et les clés en attente")
    p.add_argument("--proposer", action="store_true", help="sources et accords devinés, en JSON, à relire")
    a = p.parse_args(argv)
    espace = a.espace.resolve()
    racine = (a.racine or racine_par_defaut(espace)).resolve()
    try:
        config = config_mod.charger_config(espace)
        corpus = corpus_mod.charger(racine, espace)
    except (corpus_mod.CorpusIncomplet, config_mod.ConfigInvalide) as e:
        print(f"generer_derives : {e}", file=sys.stderr)
        return 2
    if a.proposer:
        print(json.dumps(proposer(corpus, config, Registre(corpus, config)), ensure_ascii=False, indent=1))
        return 0
    ecritures, refus, laissees = propositions(corpus, config, set(a.famille or ()), forcer=a.forcer)
    for cle, actuel, attendu, famille in ecritures:
        print(f"[{famille}] {cle}\n  - {actuel or '(absente)'}\n  + {attendu}")
    for cle, motif in laissees:
        print(f"LAISSÉE {cle} : écart déclaré, laissé ({motif})")
    for cle, raison in refus:
        print(f"REFUS {cle} : {raison}")
    print(f"{len(ecritures)} à écrire, {len(laissees)} laissée(s), {len(refus)} refus")
    if a.actions_dans:
        from corrections.lot import charger_lot
        lot = charger_lot(a.actions_dans)
        perimetre = set(lot["perimetre"])
        ajoutees = [action_de(cle, actuel, attendu, famille, corpus)
                    for cle, actuel, attendu, famille in ecritures if cle in perimetre]
        lot["actions"] += ajoutees
        a.actions_dans.write_text(json.dumps(lot, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{len(ajoutees)} action(s) ajoutée(s) à {a.actions_dans} ; {len(ecritures) - len(ajoutees)} hors périmètre")
        return 0
    if a.appliquer and ecritures:
        ecrire_francais(corpus, racine, ecritures)
        tracer(espace, ecritures)
        print("écrit dans les fr_fr.json, tracé dans provenance.json")
    return 1 if refus else 0


if __name__ == "__main__":
    sys.exit(main())
