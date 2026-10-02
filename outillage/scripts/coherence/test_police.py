"""Largeur dans la police de Minecraft."""
import unittest

from coherence.police import lignes, px


class TestPolice(unittest.TestCase):

    def test_largeurs(self):
        self.assertEqual(px("Boutiques"), 48)          # le titre qui débordait de SelectorScreen
        self.assertEqual(px("î"), px("i"))
        self.assertEqual(px("§6Or§r"), px("Or"))

    def test_repli_par_mot(self):
        self.assertEqual(lignes("Oeufs de carangue vieillis"), 2)
        self.assertEqual(lignes("Appât pour poisson-chat des cavernes géant"), 3)
        self.assertEqual(lignes("Pomme"), 1)


if __name__ == "__main__":
    unittest.main()
