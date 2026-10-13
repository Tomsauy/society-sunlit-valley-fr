"""Le glossaire confronté à la traduction."""
import unittest
from pathlib import Path

from coherence.config import Config
from coherence.controles import CONTROLES
from coherence.corpus import ChampLivre, Corpus
from coherence.modele import BLOQUANT, Options
from coherence.registre import Registre


def constats(lignes, glossaire, livres=()):
    c = Corpus()
    for cle, (en, fr, origine) in lignes.items():
        c.en[cle], c.fr[cle], c.origine_fr[cle] = en, fr, origine
    c.livres = list(livres)
    config = Config(espace=Path("."), provenance={"cles": {}, "glossaire": glossaire})
    return CONTROLES["glossaire"](c, Registre(c, config), config, Options())


def entree(en, fr, **autres):
    return dict({"en": en, "fr": fr, "garde_anglais": False, "origine": "arbitrage de traduction", "raison": ""}, **autres)


class TestGlossaire(unittest.TestCase):

    def test_un_terme_que_la_traduction_rend_autrement_bloque(self):
        trouves = constats({"block.x.tuff_stairs": ("Tuff Stairs", "Escalier en tuf", "projet")},
                           [entree("Tuff Stairs", "Escalier de tuf")])
        self.assertEqual([(x.cle, x.statut, x.actuel, x.attendu) for x in trouves],
                         [("block.x.tuff_stairs", BLOQUANT, "Escalier en tuf", "Escalier de tuf")])

    def test_conforme_a_la_casse_et_a_la_ponctuation_finale_pres(self):
        self.assertEqual(constats({"a": ("Tuff Stairs", "Escalier en tuf", "projet"),
                                   "b": ("Done.", "Terminé.", "projet")},
                                  [entree("Tuff Stairs", "escalier en tuf"), entree("Done.", "Terminé")]), [])

    def test_un_sens_parmi_plusieurs_suffit(self):
        lignes = {"block.x.jar": ("Jar", "Pot", "projet"), "block.y.jar": ("Jar", "Pot", "projet")}
        self.assertEqual(constats(lignes, [entree("Jar", "Bocal"), entree("Jar", "Pot", sens="bloc décoratif")]), [])

    def test_seul_le_francais_du_projet_compte(self):
        lignes = {"item.minecraft.bundle": ("Bundle", "Sac", "vanilla"), "item.y.jar": ("Jar", "Pot", "jar")}
        self.assertEqual(constats(lignes, [entree("Bundle", "Lot"), entree("Jar", "Bocal")]), [])

    def test_une_etiquette_au_pluriel_est_conforme_et_une_etiquette_perimee_bloque(self):
        lignes = {"tag.item.c.gravel": ("Gravel", "Graviers", "projet"),
                  "tag.item.x.boilers": ("Locometal Boilers", "Chaudières en locométal", "projet")}
        trouves = constats(lignes, [entree("Gravel", "Gravier"), entree("Locometal Boilers", "Chaudières de Locométal")])
        self.assertEqual([x.cle for x in trouves], ["tag.item.x.boilers"])

    def test_deux_entrees_de_meme_sens_qui_se_contredisent_bloquent(self):
        trouves = constats({}, [entree("Jar", "Bocal"), entree("Jar", "Pot"), entree("Jar", "Pot", sens="bloc")])
        self.assertEqual([(x.cle, x.actuel) for x in trouves], [("glossaire:Jar", "Bocal / Pot")])

    def test_l_anglais_se_compare_a_la_casse_pres(self):
        lignes = {"gui.x.add": ("Add", "Ajouter", "projet")}
        self.assertEqual(constats(lignes, [entree("ADD", "ADD", garde_anglais=True), entree("Add", "Ajouter")]), [])

    def test_les_champs_des_livres_comptent(self):
        livre = ChampLivre("fish_finder/entries/fish/eyeball_fish.json", "/name", "Eyeball Fish", "Poisson-oeil")
        trouves = constats({}, [entree("Eyeball Fish", "Poisson-globe")], livres=[livre])
        self.assertEqual([x.cle for x in trouves], [livre.cle])

    def test_la_ligature_est_refusee_dans_le_glossaire(self):
        trouves = constats({}, [entree("Eggs", "Œufs")])
        self.assertEqual([(x.cle, x.attendu) for x in trouves], [("glossaire:Eggs", "Oeufs")])

    def test_un_terme_sans_texte_identique_passe(self):
        self.assertEqual(constats({"a": ("Copper Door", "Porte en cuivre", "projet")}, [entree("Copper", "cuivre")]), [])


if __name__ == "__main__":
    unittest.main()
