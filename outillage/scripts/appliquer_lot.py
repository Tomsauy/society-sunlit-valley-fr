#!/usr/bin/env python3
"""Contrôle puis applique un lot de corrections (spec 2 §8).

    python3 fr-workspace/scripts/appliquer_lot.py fr-workspace/lots/1a-01/lot.json              # contrôle
    python3 fr-workspace/scripts/appliquer_lot.py fr-workspace/lots/1a-01/lot.json --appliquer  # écrit

Code de retour : 0 si le lot passe (et, avec --appliquer, s'il est écrit), 1 s'il a des refus (rien n'est
écrit), 2 si le lot, le corpus ou les données sont illisibles.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from coherence import config as config_mod  # noqa: E402
from coherence import corpus as corpus_mod  # noqa: E402
from corrections.applicateur import ecrire, planifier  # noqa: E402
from corrections.lot import LotInvalide, charger_lot  # noqa: E402
from verifier import ESPACE, racine_par_defaut  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Contrôle puis applique un lot de corrections (spec 2 §8).")
    p.add_argument("lot", type=Path)
    p.add_argument("--appliquer", action="store_true", help="écrire le lot s'il passe")
    p.add_argument("--racine", type=Path, help="arbre du pack (défaut : celui du vérificateur)")
    p.add_argument("--espace", type=Path, default=ESPACE, help="espace de travail (défaut : celui du script)")
    a = p.parse_args(argv)
    espace = a.espace.resolve()
    racine = (a.racine or racine_par_defaut(espace)).resolve()
    try:
        lot = charger_lot(a.lot)
        corpus = corpus_mod.charger(racine, espace)
        config = config_mod.charger_config(espace)
    except (LotInvalide, corpus_mod.CorpusIncomplet, config_mod.ConfigInvalide) as e:
        print(f"appliquer_lot : {e}", file=sys.stderr)
        return 2
    plan = planifier(lot, corpus, config, racine, espace)
    print(plan.bilan())
    for i, raison in plan.refus:
        print(f"  refus, action {i} : {raison}")
    if plan.refus:
        print("rien n'est écrit : corriger le lot, puis relancer")
        return 1
    if a.appliquer:
        ecrire(plan, racine, espace)
        print("écrit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
