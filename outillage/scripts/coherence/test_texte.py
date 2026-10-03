"""Le texte ramené à ce qui se compare."""
import unittest

from coherence.modele import BLOQUANT, Constat
from coherence.texte import contient, jetons, mots, racine, sans_codes


class TestSansCodes(unittest.TestCase):

    def test_couleurs_minecraft_et_ftb(self):
        self.assertEqual(mots("&6Pickarang&r et §6Oeufs dorés§7"),
                         ("pickarang", "et", "oeuf", "dore"))

    def test_macros_patchouli_y_compris_les_liens(self):
        texte = "Comme l'$(l:functional_flowers/hopperhock)$(item)entunia$(0)$(/l), le disque"
        self.assertNotIn("hopperhock", mots(texte))
        self.assertIn("entunia", mots(texte))

    def test_gabarits_et_emojis(self):
        self.assertEqual(mots("Prix : %1$s :coin: et %.1f %%"), ("pri", "et"))

    def test_saut_de_ligne_litteral(self):
        self.assertEqual(sans_codes("a\\nb"), "a\nb")

    def test_sauts_patchouli_et_identifiants(self):
        self.assertEqual(sans_codes("$(li)Biome$(br)Fin").split(), ["Biome", "Fin"])
        self.assertIn("\n", sans_codes("$(li)Biome"))
        self.assertEqual(mots("Dimension : minecraft:the_nether"), ("dimension",))
        self.assertIn("botania", mots("#botania:generating_special"))  # une étiquette reste visible


class TestJetons(unittest.TestCase):

    def test_forme_ecrite_et_debut_de_phrase(self):
        self.assertEqual(jetons("All versions. Allows the Vault : Plans"),
                         (("all", "All", True), ("version", "versions", False), ("allow", "Allows", True),
                          ("the", "the", False), ("vault", "Vault", False), ("plan", "Plans", False)))

    def test_aligne_sur_mots(self):
        texte = "&6Oeufs dorés&r : l'$(item)entunia$(0) — Œuf"
        self.assertEqual(tuple(m for m, _, _ in jetons(texte)), mots(texte))


class TestRacine(unittest.TestCase):

    def test_pluriels_reguliers(self):
        for pluriel, singulier in (("bocaux", "bocal"), ("chevaux", "cheval"), ("bureaux", "bureau"),
                                   ("oeufs", "oeuf"), ("prix", "prix"),
                                   # -au, -ail et -aux vers un même radical (mots déjà pliés : étau, émail)
                                   ("tuyaux", "tuyau"), ("noyaux", "noyau"), ("joyaux", "joyau"), ("boyaux", "boyau"),
                                   ("etaux", "etau"), ("coraux", "corail"), ("travaux", "travail"),
                                   ("vitraux", "vitrail"), ("emaux", "email"), ("details", "detail")):
            with self.subTest(pluriel=pluriel):
                self.assertEqual(racine(pluriel), racine(singulier))

    def test_mots_courts_intacts(self):
        self.assertEqual(racine("les"), "les")


class TestContient(unittest.TestCase):

    def test_pluriel_accent_casse_elision(self):
        self.assertTrue(contient("Place tes bacs d'EXPEDITION ici", "Bac d'expédition"))

    def test_nom_absent(self):
        self.assertFalse(contient("un casier à crabes", "Piège à crabes"))

    def test_nom_dans_une_balise(self):
        self.assertTrue(contient("La &6Machine à récompenses&r donne", "Machine à récompenses"))

    def test_nom_vide(self):
        self.assertTrue(contient("n'importe quoi", ""))


class TestConstat(unittest.TestCase):

    def test_en_dict(self):
        c = Constat("codes", "a.b", BLOQUANT, actuel="x")
        self.assertEqual(c.en_dict()["actuel"], "x")
        self.assertEqual(c.en_dict()["objet"], "")


if __name__ == "__main__":
    unittest.main()
