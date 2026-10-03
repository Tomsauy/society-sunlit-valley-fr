"""Rendu des familles dérivées et contrôle familles."""
import unittest
from pathlib import Path

from coherence.config import Config
from coherence.controles import CONTROLES
from coherence.corpus import Corpus
from coherence.modele import Options
from coherence.regles_derivees import Familles, elide, rendre

FAMILLES = {
    "familles": [
        {"nom": "oeufs_vieillis", "motif": "item.society.aged_{id}_roe", "source": ["item.society.{id}_roe"],
         "gabarit": "{Source} vieillis", "anglais": "Aged {source} Roe"},
        {"nom": "oeufs", "motif": "item.society.{id}_roe", "source": ["entity.aquaculture.{id}"],
         "gabarit": "Oeufs de {source}", "anglais": "{source} Roe",
         "cles_source": {"clam": "item.society.clam"},
         "noms_source": {"ancient": {"nom": "poisson ancien", "genre": "m", "nombre": "s"}}},
        {"nom": "fume", "motif": "item.society.smoked_{id}", "source": ["entity.aquaculture.{id}"],
         "gabarit": "{Source} fumé{e}{s}", "anglais": "Smoked {source}"},
    ],
    "accords": {"entity.aquaculture.carp": {"genre": "f", "nombre": "s"}},
}
FR = {
    "entity.aquaculture.carp": "Carpe",
    "entity.aquaculture.eel": "Anguille",
    "entity.aquaculture.pike": "Brochet",
    "item.society.clam": "Palourde",
    "item.society.carp_roe": "Oeufs de carpe",
    "item.society.aged_carp_roe": "Oeufs de carpe vieillis",
    "item.society.smoked_carp": "Carpe fumé",
    "item.society.eel_roe": "Oeufs de anguille",
    "item.society.smoked_eel": "Anguille fumée",
    "item.society.clam_roe": "Oeufs de palourde",
    "item.society.ancient_roe": "Oeufs de poisson ancien",
    "item.society.mystery_roe": "Oeufs mystère",
}


def preparer(familles=FAMILLES, fr=FR):
    corpus = Corpus()
    for cle, v in fr.items():
        corpus.fr[cle], corpus.origine_fr[cle] = v, "projet"
    corpus.en["item.society.pike_roe"] = "Pike Roe"
    return corpus, Config(espace=Path("."), familles=familles)


class TestRendre(unittest.TestCase):

    def test_elision(self):
        self.assertEqual(rendre("Oeufs de {source}", "Anguille"), "Oeufs d'anguille")
        self.assertEqual(rendre("Oeufs de {source}", "Huître"), "Oeufs d'huître")
        self.assertEqual(rendre("Oeufs de {source}", "Hareng"), "Oeufs de hareng")
        self.assertEqual(rendre("Oeufs de {source}", "Yucca"), "Oeufs de yucca")
        self.assertEqual(rendre("Pickles de {source}", "Oignons", nombre="p"), "Pickles d'oignons")
        self.assertFalse(elide(""))

    def test_accord_avec_la_source(self):
        self.assertEqual(rendre("{Source} fumé{e}{s}", "Carangue", "f"), "Carangue fumée")
        self.assertEqual(rendre("{Source} fumé{e}{s}", "brochet", "m"), "Brochet fumé")
        self.assertEqual(rendre("{Source} séché{e}{s}", "Champignons scintillants", "m", "p"),
                         "Champignons scintillants séchés")

    def test_pluriel_de_la_source(self):
        self.assertEqual(rendre("Conserve de {sources}", "Tomate", pluriel="tomates"), "Conserve de tomates")
        self.assertEqual(rendre("Conserve de {sources}", "Abricot", pluriel="Abricots"), "Conserve d'abricots")

    def test_nom_propre(self):
        self.assertEqual(rendre("Oeufs de {source}", "Aegis", propre=True), "Oeufs d'Aegis")
        self.assertEqual(rendre("Appât pour {source}", "Aegis"), "Appât pour aegis")


class TestFamilles(unittest.TestCase):

    def setUp(self):
        self.corpus, self.config = preparer()
        self.familles = Familles(self.corpus, self.config)

    def test_la_plus_specifique_d_abord(self):
        self.assertEqual(self.familles.membres["item.society.aged_carp_roe"][0]["nom"], "oeufs_vieillis")

    def test_rendus(self):
        attendu = self.familles.attendu
        self.assertEqual(attendu("item.society.carp_roe"), "Oeufs de carpe")
        self.assertEqual(attendu("item.society.eel_roe"), "Oeufs d'anguille")
        self.assertEqual(attendu("item.society.clam_roe"), "Oeufs de palourde")
        self.assertEqual(attendu("item.society.ancient_roe"), "Oeufs de poisson ancien")
        self.assertEqual(attendu("item.society.pike_roe"), "Oeufs de brochet")

    def test_chaine_de_proche_en_proche(self):
        self.corpus.fr["item.society.carp_roe"] = "Oeufs de carpes"
        self.assertEqual(Familles(self.corpus, self.config).attendu("item.society.aged_carp_roe"),
                         "Oeufs de carpe vieillis")

    def test_chaine_avec_accord_refusee(self):
        familles = {"familles": [dict(FAMILLES["familles"][0], gabarit="{Source} vieilli{e}{s}"),
                                 FAMILLES["familles"][1]], "accords": {}}
        f = Familles(*preparer(familles))
        self.assertIsNone(f.attendu("item.society.aged_carp_roe"))
        self.assertIn("en chaîne", f.problemes["item.society.aged_carp_roe"])

    def test_controle(self):
        constats = {c.cle: c for c in CONTROLES["familles"](self.corpus, None, self.config, Options())}
        self.assertEqual(sorted(constats), ["item.society.eel_roe", "item.society.mystery_roe",
                                            "item.society.smoked_carp", "item.society.smoked_eel"])
        self.assertEqual(constats["item.society.smoked_carp"].attendu, "Carpe fumée")
        self.assertIn("source inconnue", constats["item.society.mystery_roe"].detail)
        self.assertIn("genre inconnu", constats["item.society.smoked_eel"].detail)


if __name__ == "__main__":
    unittest.main()
