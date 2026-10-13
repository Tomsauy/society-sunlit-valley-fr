#!/usr/bin/env python3
"""Fixe une entrée du glossaire dans provenance.json, qui fait foi, et régénère GLOSSAIRE.md.

    python3 fr-workspace/scripts/glossaire.py --en "Crab Trap" --fr "Casier à crabes" --raison "pas de nasse"
    python3 fr-workspace/scripts/glossaire.py --en "Jar" --fr "Pot" --sens "bloc décoratif" --raison "nom du mod"
    python3 fr-workspace/scripts/glossaire.py --md      # régénère seulement GLOSSAIRE.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from corrections.glossaire import ecrire_md, fixer  # noqa: E402

ESPACE = SCRIPTS.parent


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Fixe une entrée du glossaire (provenance.json) et régénère GLOSSAIRE.md.")
    p.add_argument("--en")
    p.add_argument("--fr")
    p.add_argument("--raison")
    p.add_argument("--sens", default="", help="le sens visé, quand l'anglais en a plusieurs")
    p.add_argument("--garde-anglais", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--md", action="store_true", help="régénère seulement GLOSSAIRE.md")
    p.add_argument("--espace", type=Path, default=ESPACE)
    a = p.parse_args(argv)
    if a.md:
        print(f"GLOSSAIRE.md : {ecrire_md(a.espace)} entrées")
        return 0
    if not (a.en and a.fr and a.raison):
        p.error("--en, --fr et --raison sont requis (ou --md)")
    print(fixer(a.espace, a.en, a.fr, a.raison, sens=a.sens, garde_anglais=a.garde_anglais))
    return 0


if __name__ == "__main__":
    sys.exit(main())
