"""Couverture : pas d'anglais sans français, pas de français vide, témoins, doublons."""
import unittest
from pathlib import Path

from coherence.config import Config
from coherence.controles import CONTROLES
from coherence.corpus import ChampLivre, Corpus
from coherence.modele import BLOQUANT, SIGNALE, Options


class TestCouverture(unittest.TestCase):

    def setUp(self):
        c = Corpus()
        c.en.update({"a.manque": "Hello", "a.vide": "Hi", "item.society.cle": "", "block.minecraft.x": "X",
                     "block_type.everycomp.cupboard": "%s Cupboard", "ftbquests.chapter.a.quest1.title": "Q"})
        c.origine_en.update({"a.manque": "jar", "a.vide": "projet", "item.society.cle": "projet",
                             "block.minecraft.x": "vanilla", "block_type.everycomp.cupboard": "jar",
                             "ftbquests.chapter.a.quest1.title": "projet"})
        c.reconstitue["item.society.cle"] = "Red Key"
        c.fr.update({"a.vide": " ", "ftbquests.chapter.a.quest1.title": "Q"})
        c.temoins = {("society", "a.temoin"): {"ko_kr": "x"}, ("entityculling", "a.retire"): {"zh_cn": "y"},
                     ("ftbquestlocalizer", "ftbquests.chapter.a.quest2.description3"): {"ko_kr": "z"}}
        c.projet = {("a", "k.double"): "Un", ("b", "k.double"): "Deux"}
        c.livres = [ChampLivre("almanac/e.json", "/text", "Milk", "", ())]
        self.corpus = c
        self.config = Config(espace=Path("."), mods_retires={"entityculling": "mod retiré du pack en 4.0"})

    def test_blanc_sans_temoin(self):
        """Spec 2 §7 : un texte vide dont l'anglais est vide et qui n'a aucune traduction témoin n'est plus présumé
        voulu ; avec des témoins vides, il reste une ligne blanche voulue."""
        c = Corpus()
        c.en.update({"tooltip.x.seul": "", "tooltip.x.temoins_vides": ""})
        c.origine_en.update({"tooltip.x.seul": "projet", "tooltip.x.temoins_vides": "projet"})
        c.fr.update({"tooltip.x.seul": "", "tooltip.x.temoins_vides": " "})
        c.temoins = {("x", "tooltip.x.temoins_vides"): {"ko_kr": "", "zh_cn": " "}}
        constats = CONTROLES["couverture"](c, None, self.config, Options())
        self.assertEqual([(x.cle, x.statut) for x in constats], [("tooltip.x.seul", BLOQUANT)])
        self.assertIn("sans anglais ni traduction témoin", constats[0].detail)

    def test_constats(self):
        constats = {(c.cle, c.statut): c for c in CONTROLES["couverture"](self.corpus, None, self.config, Options())}
        self.assertEqual(sorted(constats), [
            ("a.manque", BLOQUANT), ("a.temoin", BLOQUANT), ("a.vide", BLOQUANT),
            ("almanac/e.json#/text", BLOQUANT), ("item.society.cle", BLOQUANT), ("k.double", SIGNALE)])
        self.assertEqual(constats[("item.society.cle", BLOQUANT)].attendu, "Red Key")
        self.assertIn("vide", constats[("a.vide", BLOQUANT)].detail)

    def test_objet_sans_anglais(self):
        """Piège n° 2 de CLAUDE.md : un nouvel objet dont l'anglais est vide (KubeJS le nomme d'après son identifiant),
        sans anglais reconstitué, sans témoins traduits et sans français, est relevé ; un blanc voulu ne l'est pas."""
        c = Corpus()
        c.en.update({"item.society.nouveau_roe": "", "item.society.reconstitue_roe": "", "item.x.blanc": " ",
                     "tooltip.x.ligne": ""})
        c.origine_en.update({"item.society.nouveau_roe": "projet", "item.society.reconstitue_roe": "projet",
                             "item.x.blanc": "projet", "tooltip.x.ligne": "jar"})
        c.reconstitue["item.society.reconstitue_roe"] = "Reconstituted Roe"
        c.fr.update({"item.x.blanc": " ", "tooltip.x.ligne": "", "item.x.temoin_traduit": ""})
        c.temoins = {("x", "item.x.blanc"): {"ko_kr": " "}, ("x", "tooltip.x.ligne"): {"ko_kr": ""},
                     ("x", "item.x.temoin_traduit"): {"zh_cn": "번역"}, ("x", "item.x.temoin_seul"): {"ko_kr": "열쇠"}}
        constats = CONTROLES["couverture"](c, None, self.config, Options())
        sans_anglais = sorted(x.cle for x in constats if "sans anglais" in x.detail)
        self.assertEqual(sans_anglais, ["item.society.nouveau_roe", "item.x.temoin_traduit"])
        self.assertTrue(all(x.statut == BLOQUANT for x in constats if "sans anglais" in x.detail))
        # une clé des témoins absente du français n'a qu'un constat, celui des témoins
        (seul,) = [x.detail for x in constats if x.cle == "item.x.temoin_seul"]
        self.assertTrue(seul.startswith("présente dans les témoins (ko_kr)"), seul)
        self.assertIn("anglais sans français", [x.detail for x in constats if x.cle == "item.society.reconstitue_roe"])

    def test_surcharge_vanilla_videe(self):
        c = Corpus()
        c.en["item.minecraft.cod"] = "Raw Cod"
        c.origine_en["item.minecraft.cod"] = "vanilla"
        c.fr["item.minecraft.cod"] = ""
        c.origine_fr["item.minecraft.cod"] = "projet"
        constats = CONTROLES["couverture"](c, None, self.config, Options())
        self.assertEqual([(x.cle, x.statut) for x in constats], [("item.minecraft.cod", BLOQUANT)])


if __name__ == "__main__":
    unittest.main()
