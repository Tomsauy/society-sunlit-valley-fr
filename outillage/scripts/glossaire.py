#!/usr/bin/env python3
"""Fixe une entrée du glossaire, dans provenance.json et GLOSSAIRE.md à la fois (spec 2 §6).

    python3 fr-workspace/scripts/glossaire.py --en "Crab Trap" --fr "Casier à crabes" --raison "fiche du 30/09 : crabes"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from corrections.glossaire import fixer  # noqa: E402

ESPACE = SCRIPTS.parent


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Fixe une entrée du glossaire (provenance.json et GLOSSAIRE.md).")
    p.add_argument("--en", required=True)
    p.add_argument("--fr", required=True)
    p.add_argument("--raison", required=True)
    p.add_argument("--espace", type=Path, default=ESPACE)
    a = p.parse_args(argv)
    print(fixer(a.espace, a.en, a.fr, a.raison))
    return 0


if __name__ == "__main__":
    sys.exit(main())
