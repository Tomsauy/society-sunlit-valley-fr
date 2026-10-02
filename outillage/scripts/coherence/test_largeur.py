"""Noms vendus en boutique et libellés contraints."""
import unittest
from pathlib import Path

from coherence.config import Config
from coherence.controles import CONTROLES
from coherence.corpus import Corpus
from coherence.modele import BLOQUANT, SIGNALE, Options

LONG = "Appât pour poisson-chat des cavernes géant"


class TestLargeur(unittest.TestCase):

    def test_constats(self):
        c = Corpus(vendus={"society:long", "jar:long", "society:court", "society:bloc"})
        valeurs = {"item.society.long": (LONG, "projet"), "item.jar.long": (LONG, "jar"),
                   "item.society.court": ("Pomme", "projet"), "block.society.bloc": (LONG, "projet"),
                   "gui.x.titre": ("Boutiques", "projet"), "gui.x.autre": ("Achats", "projet")}
        for cle, (fr, origine) in valeurs.items():
            c.fr[cle], c.origine_fr[cle] = fr, origine
        config = Config(espace=Path("."), largeurs=[{"cle": "gui.x.titre", "limite": 46, "motif": "SelectorScreen"},
                                                   {"cle": "gui.x.autre", "limite": 46, "motif": "SelectorScreen"}])
        constats = {x.cle: x.statut for x in CONTROLES["largeur"](c, None, config, Options())}
        self.assertEqual(constats, {"item.society.long": BLOQUANT, "item.jar.long": SIGNALE,
                                    "block.society.bloc": BLOQUANT, "gui.x.titre": BLOQUANT})


if __name__ == "__main__":
    unittest.main()
