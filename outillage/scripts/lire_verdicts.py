#!/usr/bin/env python3
"""Lit les verdicts téléchargés d'un échantillon (spec 2 §9) : complet ou non, et les refus.

    python3 fr-workspace/scripts/lire_verdicts.py fr-workspace/lots/1a-01/.verdicts \
        --page fr-workspace/lots/1a-01/page.json --sortie fr-workspace/lots/1a-01/verdicts.json

Code de retour : 0 si l'échantillon est complet, 1 sinon.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from corrections.echantillon import lire_verdicts  # noqa: E402


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Lit les verdicts téléchargés d'un échantillon (spec 2 §9).")
    p.add_argument("dossier", type=Path, help="le out_dir de l'outil ArtifactData (collection verdicts)")
    p.add_argument("--page", type=Path, required=True, help="le page.json du sous-lot")
    p.add_argument("--sortie", type=Path, required=True)
    a = p.parse_args(argv)
    page = json.loads(a.page.read_text(encoding="utf-8"))
    r = lire_verdicts(a.dossier, page)
    a.sortie.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{r['lot']} : échantillon {'complet' if r['complet'] else 'incomplet'} "
          f"({len(r['verdicts'])}/{len(page['echantillon'])}), {len(r['refus'])} refus")
    for x in r["refus"]:
        print(f"  refus n° {x['n']}, {x['cle']} : {x['commentaire'] or '(sans commentaire)'}")
    return 0 if r["complet"] else 1


if __name__ == "__main__":
    sys.exit(main())
