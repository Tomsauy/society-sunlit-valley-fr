#!/usr/bin/env python3
"""Tire l'échantillon d'un sous-lot et écrit le document de la page de relecture (spec 2 §9).

    python3 fr-workspace/scripts/echantillonner_lot.py fr-workspace/lots/1a-01/lot.json --titre "Noms d'objets (1)" \
        --resume "…" --dette-avant 2828 --dette-apres 2790 --attend-verdict --sortie fr-workspace/lots/1a-01/page.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import verifier  # noqa: E402
from coherence import corpus as corpus_mod  # noqa: E402
from corrections.echantillon import document  # noqa: E402
from corrections.lot import LotInvalide, charger_lot  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Échantillon d'un sous-lot pour la page de relecture (spec 2 §9).")
    p.add_argument("lot", type=Path)
    p.add_argument("--titre", required=True)
    p.add_argument("--resume", required=True)
    p.add_argument("--dette-avant", type=int, required=True)
    p.add_argument("--dette-apres", type=int, required=True)
    p.add_argument("--attend-verdict", action="store_true", help="premier sous-lot de sa nature : attendre les verdicts")
    p.add_argument("--sortie", type=Path, required=True)
    p.add_argument("--racine", type=Path)
    p.add_argument("--espace", type=Path, default=verifier.ESPACE)
    a = p.parse_args(argv)
    espace = a.espace.resolve()
    racine = (a.racine or verifier.racine_par_defaut(espace)).resolve()
    try:
        lot = charger_lot(a.lot)
        corpus = corpus_mod.charger(racine, espace)
    except (LotInvalide, corpus_mod.CorpusIncomplet) as e:
        print(f"echantillonner_lot : {e}", file=sys.stderr)
        return 2

    def anglais(cle):
        if cle == corpus_mod.CLE_JOURNAL:
            return corpus.journal_en
        champ = corpus.champ(cle) if "#" in cle else None
        return champ.en if champ else corpus.anglais(cle)

    doc = document(lot, a.titre, a.resume, a.dette_avant, a.dette_apres, a.attend_verdict, anglais, corpus.texte)
    a.sortie.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{lot['lot']} : {len(doc['echantillon'])} action(s) tirée(s) sur {doc['actions']} → {a.sortie}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
