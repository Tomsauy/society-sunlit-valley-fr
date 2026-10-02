"""Scripts de l'amont patchés."""
import unittest
from pathlib import Path

from coherence.config import Config
from coherence.controles import CONTROLES
from coherence.corpus import Corpus
from coherence.modele import Options


class TestScriptsPatches(unittest.TestCase):

    def test_constats(self):
        c = Corpus(scripts_amont={"a.js": "1" * 40, "b.js": "2" * 40})
        config = Config(espace=Path("."), scripts_patches={
            "a.js": {"base": "1" * 40, "motif": "m"}, "b.js": {"base": "3" * 40, "motif": "m"},
            "c.js": {"base": "4" * 40, "motif": "m"}})
        constats = {x.cle: x.detail for x in CONTROLES["scripts_patches"](c, None, config, Options())}
        self.assertEqual(sorted(constats), ["b.js", "c.js"])
        self.assertIn("refusionner", constats["b.js"])
        self.assertIn("introuvable", constats["c.js"])

    def test_amont_illisible(self):
        """M3 : git a échoué (scripts_amont vaut None) — chaque script patché le dit, au lieu de passer pour retiré."""
        config = Config(espace=Path("."), scripts_patches={"a.js": {"base": "1" * 40, "motif": "m"}})
        (c,) = CONTROLES["scripts_patches"](Corpus(scripts_amont=None), None, config, Options())
        self.assertEqual(c.cle, "a.js")
        self.assertIn("amont illisible", c.detail)


if __name__ == "__main__":
    unittest.main()
