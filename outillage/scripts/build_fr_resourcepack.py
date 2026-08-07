#!/usr/bin/env python3
"""Génère resourcepacks/Society_FR.zip depuis les overrides kubejs. Relançable."""
import json, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "society-sunlit-valley"

def main() -> None:
    dest = REPO / "resourcepacks" / "Society_FR.zip"
    files = sorted((REPO / "kubejs" / "assets").glob("*/lang/fr_fr.json"))
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("pack.mcmeta", json.dumps(
            {"pack": {"pack_format": 15,
                      "description": "Traduction FR non officielle — Society: Sunlit Valley"}},
            ensure_ascii=False, indent=2))
        for f in files:
            z.write(f, f"assets/{f.parents[1].name}/lang/fr_fr.json")
    print(f"écrit {dest.name}: {len(files)} fichiers lang")

if __name__ == "__main__":
    main()
