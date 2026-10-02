"""Mêmes codes en anglais et en français."""
import unittest

from coherence.controles import CONTROLES
from coherence.controles.codes import ecart, structure
from coherence.corpus import ChampLivre, Corpus
from coherence.modele import Options


class TestEcart(unittest.TestCase):

    def test_codes_perdus_et_ajoutes(self):
        self.assertEqual(ecart("Hello %s", "Salut"), "perdus : %s")
        self.assertEqual(ecart("§6Or§r", "§6Or§7"), "perdus : §r ; ajoutés : §7")
        self.assertEqual(ecart("Version: ${mc_version} forge", "Version de Minecraft :"),
                         "perdus : ${mc_version}")

    def test_ordre_libre(self):
        self.assertEqual(ecart("%1$s gives %2$s", "%2$s offert par %1$s"), "")

    def test_lien_patchouli(self):
        # Point de vigilance 5 : le chemin du lien fait partie du code.
        self.assertNotEqual(ecart("$(l:a/b)x$(/l)", "$(l:a/c)x$(/l)"), "")
        self.assertEqual(ecart("$(l:a/b)x$(/l)", "$(l:a/b)y$(/l)"), "")


class TestControle(unittest.TestCase):

    def test_cles_livres_journal(self):
        c = Corpus()
        c.en.update({"a.x": "Hi %s", "a.y": "Hi"})
        c.fr.update({"a.x": "Salut", "a.y": "Salut"})
        c.origine_fr.update({"a.x": "projet", "a.y": "projet"})
        c.livres = [ChampLivre("almanac/e.json", "/text", "$(item)Milk$()", "Lait", ())]
        c.journal_en = "## 4.1.5\n---\n- one\n- two\n"
        c.journal_fr = "## 4.1.5\n---\n- un\n"
        constats = {x.cle: x for x in CONTROLES["codes"](c, None, None, Options())}
        self.assertEqual(sorted(constats), ["a.x", "almanac/e.json#/text", "journal"])
        self.assertIn("4 en anglais, 3 en français", constats["journal"].detail)
        self.assertEqual(structure("## T\n^^^\n--- \n- a\ntexte"), ["##", "^^^", "---", "- "])


if __name__ == "__main__":
    unittest.main()
