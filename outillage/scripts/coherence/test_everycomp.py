"""Every Compat : essences activées et gabarits block_type."""
import unittest

from coherence.controles import CONTROLES
from coherence.corpus import Corpus
from coherence.modele import Options


class TestEverycomp(unittest.TestCase):

    def test_constats(self):
        c = Corpus(essences=["wood_type.atmospheric.rosewood", "leaves_type.autumnity.maple"])
        c.fr.update({"leaves_type.autumnity.maple": "érable", "block_type.everycomp.bench": "Banc en %s"})
        c.en.update({"block_type.everycomp.cupboard": "%s Cupboard", "block_type.everycomp.bench": "%s Bench"})
        constats = sorted(x.cle for x in CONTROLES["everycomp"](c, None, None, Options()))
        self.assertEqual(constats, ["block_type.everycomp.cupboard", "wood_type.atmospheric.rosewood"])

    def test_registre_sans_nom_d_essence(self):
        # everycomp-entries.toml liste aussi les gâteaux d'Amendments ([types.cake.…]) : leur nom se
        # lit sous la clé fixe « cake », jamais sous cake.<mod>.<gâteau>.
        c = Corpus(essences=["cake.veggiesdelight.carrot_cake", "leaves_type.meadow.pine"])
        constats = [x.cle for x in CONTROLES["everycomp"](c, None, None, Options())]
        self.assertEqual(constats, ["leaves_type.meadow.pine"])


if __name__ == "__main__":
    unittest.main()
