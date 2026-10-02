"""Les contrôles : chaque module expose NOM et verifier(corpus, registre, config, options)."""
from __future__ import annotations

from . import (accents, anglais_residuel, casse, codes, conventions, couverture, decisions, everycomp, familles,
               gabarits, homonymes, largeur, orthographe, references, scripts_patches, terminologie)

MODULES = (accents, anglais_residuel, casse, codes, conventions, couverture, decisions, everycomp, familles,
           gabarits, homonymes, largeur, orthographe, references, scripts_patches, terminologie)
CONTROLES = {module.NOM: module.verifier for module in MODULES}
