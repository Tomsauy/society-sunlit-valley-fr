"""Registre des noms et homonymes."""
import unittest
from pathlib import Path

from coherence import rapport
from coherence.config import Config
from coherence.controles import CONTROLES
from coherence.corpus import ChampLivre, Corpus
from coherence.modele import BLOQUANT, Options
from coherence.registre import Nom, Registre


def corpus_de(noms: dict) -> Corpus:
    """{cle: (anglais, français)} -> Corpus minimal, tout d'origine projet."""
    c = Corpus()
    for cle, (en, fr) in noms.items():
        c.en[cle], c.fr[cle], c.origine_fr[cle] = en, fr, "projet"
    return c


class TestRegistre(unittest.TestCase):

    def setUp(self):
        self.config = Config(espace=Path("."), mots_generiques={"Chute": "mot courant anglais",
                                                                "The End": "expression courante : at the end"})
        self.corpus = corpus_de({
            "block.a.crab_trap": ("Crab Trap", "Piège à crabes"),
            "item.b.crab_trap": ("Crab Trap", "Casier à crabes"),
            "item.c.crab_traps": ("Crab Traps", "piege a crabes"),
            "block.create.chute": ("Chute", "Descente"),
            "item.x.bin": ("Bin", "Bac"),
            "item.x.stone": ("Stone", "Roche"),
            "society.skills.fishing.luck": ("+0.25 Luck", "Chance +0,25"),
            "dialog.npc.banker.name": ("Caroline", "Caroline"),
            "tooltip.society.bac": ("Place your bins", "Place tes bacs"),
            "wood_type.x.cherry": ("Cherry", "Cerisier"),
            "block.x.falling": ("Falling %s", "%s qui tombe"),
            "biome.minecraft.the_end": ("The End", "L'End"),
        })
        self.registre = Registre(self.corpus, self.config)

    def test_identifiant(self):
        self.assertEqual(Nom("item.society.bac", "", "", "").identifiant, "society:bac")
        self.assertEqual(Nom("dialog.npc.banker.name", "", "", "").identifiant, "")

    def test_noms_de_pnj(self):
        self.assertEqual(self.registre.noms_de_pnj(), ["Caroline"])

    def test_perimetre(self):
        self.assertIn("dialog.npc.banker.name", self.registre.noms)
        self.assertNotIn("tooltip.society.bac", self.registre.noms)

    def test_citable(self):
        noms = self.registre.noms
        self.assertTrue(self.registre.citable(noms["block.a.crab_trap"]))
        self.assertTrue(self.registre.citable(noms["item.x.stone"]))
        self.assertFalse(self.registre.citable(noms["block.create.chute"]))
        self.assertFalse(self.registre.citable(noms["item.x.bin"]))
        self.assertFalse(self.registre.citable(noms["society.skills.fishing.luck"]))
        self.assertFalse(self.registre.citable(noms["wood_type.x.cherry"]))       # un matériau, pas un objet cité
        self.assertFalse(self.registre.citable(noms["block.x.falling"]))          # un gabarit
        self.assertFalse(self.registre.citable(noms["biome.minecraft.the_end"]))  # expression générique déclarée

    def test_anglais_reconstitue(self):
        self.corpus.en["item.society.cle_rouge"] = ""
        self.corpus.fr["item.society.cle_rouge"] = "Clé rouge"
        self.corpus.reconstitue["item.society.cle_rouge"] = "Red Key"
        self.assertEqual(Registre(self.corpus, self.config).noms["item.society.cle_rouge"].en, "Red Key")

    def test_groupes_homonymes(self):
        (groupe,) = self.registre.groupes_homonymes()
        self.assertEqual([n.cle for n in groupe], ["block.a.crab_trap", "item.b.crab_trap", "item.c.crab_traps"])

    def test_controle_homonymes(self):
        (c,) = CONTROLES["homonymes"](self.corpus, self.registre, self.config, Options())
        self.assertEqual((c.cle, c.statut), ("block.a.crab_trap", BLOQUANT))
        self.assertIn("Casier à crabes", c.actuel)
        self.assertIn("item.c.crab_traps = piege a crabes", c.preuve)
        # I3 : l'objet du constat est le groupe entier, clés triées
        self.assertEqual(c.objet, ("block.a.crab_trap", "item.b.crab_trap", "item.c.crab_traps"))

    def test_exception_d_un_groupe(self):
        """I3 : l'exception d'un groupe porte ses clés ; un nouveau membre (un troisième bloc « Crab Trap ») n'est pas
        couvert par la distinction déclarée pour les deux premiers, et l'exception devient orpheline."""
        exc = {"controle": "homonymes", "cle": "block.a.crab_trap", "motif": "deux objets distincts",
               "objet": ["block.a.crab_trap", "item.b.crab_trap", "item.c.crab_traps"], "date": "2026-09-29"}
        lancer = lambda corpus: rapport.appliquer(
            CONTROLES["homonymes"](corpus, Registre(corpus, self.config), self.config, Options()), [exc], [],
            corpus.texte, ["homonymes"])
        r = lancer(self.corpus)
        self.assertEqual((len(r.couverts), r.bloquants, r.orphelines), (1, [], []))
        self.corpus.en["block.d.crab_trap"], self.corpus.fr["block.d.crab_trap"] = "Crab Trap", "Nasse"
        self.corpus.origine_fr["block.d.crab_trap"] = "projet"
        r = lancer(self.corpus)
        self.assertEqual((len(r.couverts), len(r.bloquants), r.orphelines), (0, 1, [exc]))

    def test_intitules_de_fiches(self):
        """Un même intitulé des fiches de livres garde sa traduction la plus fréquente : « Sapling Price » se
        traduit « Prix de la pousse » dans deux fiches, « Prix des pousses » s'en écarte."""
        c = Corpus()
        c.livres = [ChampLivre(f"almanac/entries/trees/{nom}.json", "/pages/0/text",
                               "$(l)Stats$()$(li)Sapling Price: :coin: 16$(li)Size: 1x1", fr)
                    for nom, fr in (("oak", "$(l)Stats$()$(li)Prix de la pousse : :coin: 16$(li)Taille : 1x1"),
                                    ("birch", "$(l)Stats$()$(li)Prix de la pousse : :coin: 16$(li)Taille : 1x1"),
                                    ("dark", "$(l)Stats$()$(li)Prix des pousses : :coin: 16$(li)Taille : 1x1"))]
        constats = CONTROLES["homonymes"](c, Registre(c, self.config), self.config, Options())
        self.assertEqual([(x.cle, x.attendu) for x in constats],
                         [("almanac/entries/trees/dark.json#/pages/0/text", "Prix de la pousse")])


if __name__ == "__main__":
    unittest.main()
