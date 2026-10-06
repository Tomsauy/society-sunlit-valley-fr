#!/usr/bin/env python3
"""Mesure le périmètre d'un sous-lot (spec 2 §4, étape 1) et écrit le squelette de son fichier de lot.

    python3 fr-workspace/scripts/mesurer_lot.py --lot 1a-01 --nature decisions --question crabes \
        --sortie fr-workspace/lots/1a-01/lot.json
    python3 fr-workspace/scripts/mesurer_lot.py --lot 3b-01 --nature references --controle references \
        --sortie fr-workspace/lots/3b-01/lot.json
    python3 fr-workspace/scripts/mesurer_lot.py --lot 4b-01 --nature casse --controle casse --regle casse_textes \
        --remplir --sortie fr-workspace/lots/4b-01/lot.json
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import verifier  # noqa: E402
from coherence import config as config_mod  # noqa: E402
from coherence import corpus as corpus_mod  # noqa: E402
from corrections.lot import MAX_ACTIONS, NATURES  # noqa: E402
from corrections.mesure import attendus_surs, cles_des_questions, premier_paquet, selectionner, squelette  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Mesure le périmètre d'un sous-lot (spec 2 §4).")
    p.add_argument("--lot", required=True)
    p.add_argument("--nature", required=True, choices=NATURES)
    p.add_argument("--controle", action="append", default=[], help="les constats de ce contrôle (répétable)")
    p.add_argument("--question", action="append", default=[], help="les clés de cette question de la fiche (répétable)")
    p.add_argument("--cles", type=Path, help="un fichier : une clé par ligne")
    p.add_argument("--taille", type=int, default=MAX_ACTIONS, help="constats retenus au plus")
    p.add_argument("--regle", action="append", default=[], choices=["casse_textes", "nombres", "largeurs_mods", "terminologie_interdits"],
                   help="mesurer avec cette règle en attente activée")
    p.add_argument("--bloquants", action="store_true",
                   help="ne retenir que les constats bloquants : ceux qu'une règle retirée ou activée fait naître")
    p.add_argument("--remplir", action="store_true", help="proposer les corrections dont le constat donne le texte entier")
    p.add_argument("--sortie", type=Path, required=True)
    p.add_argument("--racine", type=Path)
    p.add_argument("--espace", type=Path, default=verifier.ESPACE)
    a = p.parse_args(argv)
    if not (a.controle or a.question or a.cles):
        p.error("au moins un critère : --controle, --question ou --cles")
    espace = a.espace.resolve()
    racine = (a.racine or verifier.racine_par_defaut(espace)).resolve()
    try:
        corpus, config, resultat, _ = verifier.analyser(racine, espace, regles={r: True for r in a.regle})
        cles = cles_des_questions(espace.parent, a.question) if a.question else set()
    except (corpus_mod.CorpusIncomplet, config_mod.ConfigInvalide, ValueError) as e:
        print(f"mesurer_lot : {e}", file=sys.stderr)
        return 2
    if a.cles:
        cles |= {ligne.strip() for ligne in a.cles.read_text(encoding="utf-8").splitlines() if ligne.strip()}
    constats = selectionner(resultat, a.controle, cles, bloquants_seulement=a.bloquants)
    paquet = premier_paquet(constats, a.taille, par_objet=a.nature == "references")
    criteres = {"controles": a.controle, "questions": a.question, "regles": a.regle, "bloquants": a.bloquants,
                "date": datetime.date.today().isoformat()}
    lot = squelette(a.lot, a.nature, criteres, paquet, cles, config.dette)
    if a.remplir:
        texte = lambda cle: (corpus.texte(cle) if cle in corpus.fr or "#" in cle  # noqa: E731
                             or cle == corpus_mod.CLE_JOURNAL else None)
        lot["actions"], laissees = attendus_surs(paquet, texte, {f["forme"] for f in config.formes_interdites})
        print(f"remplies : {len(lot['actions'])} correction(s) ; à la main : {len(laissees)} clé(s)")
    a.sortie.parent.mkdir(parents=True, exist_ok=True)
    a.sortie.write_text(json.dumps(lot, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{a.lot} : {len(paquet)} constat(s) retenu(s) sur {len(constats)}, "
          f"{len(lot['perimetre'])} clé(s) dans le périmètre → {a.sortie}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
