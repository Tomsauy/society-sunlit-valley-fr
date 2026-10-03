"""Accents : vocabulaire figé et mots à double sens."""
import unittest
from pathlib import Path

from coherence.config import Config
from coherence.controles import CONTROLES
from coherence.corpus import Corpus
from coherence.modele import Options
from coherence.texte import meme_casse

VOCABULAIRE = {
    "cle": [{"forme": "clé", "sens": "key"}],
    "ecran": [{"forme": "écran", "sens": "screen"}],
    "a": [{"forme": "a", "sens": "has"}, {"forme": "à", "sens": "to"}],
    "ether": [{"forme": "éther", "sens": "ether"}],
    "seche": [{"forme": "séché", "sens": "dried"}, {"forme": "sèche", "sens": "dry"}],
    "mais": [{"forme": "maïs", "sens": "corn"}],
    "ameliore": [{"forme": "amélioré", "sens": "improved"}],
    "achete": [{"forme": "achète", "sens": "purchase"}],
    "peche": [{"forme": "pêche", "sens": "fishing"}],
    "seches": [{"forme": "sèches", "sens": "dry"}],
    "cafe": [{"forme": "café", "sens": "coffee"}],
}
DOUBLE_SENS = [{"anglais": "dried", "justes": ["séché", "séchée", "séchés", "séchées"], "motif": "participe"},
               {"anglais": "dry", "justes": ["sec", "sèche", "secs", "sèches"], "motif": "adjectif"}]


def constats(textes, homographes=None):
    c = Corpus()
    for cle, (en, fr) in textes.items():
        c.en[cle], c.fr[cle], c.origine_fr[cle] = en, fr, "projet"
    c.fr["gui.minecraft.exemple"], c.origine_fr["gui.minecraft.exemple"] = "Oui mais non", "vanilla"
    config = Config(espace=Path("."), vocabulaire=VOCABULAIRE, double_sens=DOUBLE_SENS,
                    noms_propres={"Ether": "nom inventé par le mod", "Cozy Cafe": "nom du mod"},
                    homographes=homographes or {})
    return {x.cle: x for x in CONTROLES["accents"](c, None, config, Options())}


class TestAccents(unittest.TestCase):

    def test_mot_sans_accent(self):
        c = constats({"item.x.cle": ("Red Key", "Cle rouge"), "gui.x.ecran": ("Screen", "ECRAN principal")})
        self.assertEqual(c["item.x.cle"].attendu, "Clé rouge")
        self.assertEqual(c["gui.x.ecran"].attendu, "ÉCRAN principal")

    def test_formes_justes_et_ambigues(self):
        c = constats({"a.b": ("x", "CLÉ à molette"), "a.c": ("x", "Il a une clé"), "a.d": ("x", "L'Ether pur")})
        self.assertEqual(c, {})

    def test_double_sens(self):
        c = constats({"item.society.dried_shimmering_mushrooms": ("Dried Shimmering Mushrooms",
                                                                   "Champignons scintillants sèches")})
        self.assertEqual(c["item.society.dried_shimmering_mushrooms"].attendu, "Champignons scintillants séchés")

    def test_homographes_verifies_dans_les_noms_seulement(self):
        c = constats({"tooltip.x.mais": ("x", "C'est bien mais cher"), "item.x.corn": ("Corn", "Epi de mais"),
                      "tooltip.x.am": ("x", "Il améliore ton outil"), "item.x.can": ("Can", "Arrosoir ameliore")},
                     homographes={"ameliore": "verbe améliorer : « il améliore »"})
        self.assertEqual(sorted(c), ["item.x.can", "item.x.corn"])
        self.assertEqual(c["item.x.corn"].attendu, "Epi de maïs")  # « mais » attesté chez Mojang

    def test_un_accent_de_plus_n_est_pas_un_oubli(self):
        # « acheté », « pêché », « séchés » portent un accent que la forme figée n'a pas : c'est un autre mot
        c = constats({"gui.x.achat": ("Bought", "Il a été acheté"), "gui.x.prise": ("Caught", "Poisson pêché"),
                      "item.x.dried": ("Dried Mushrooms", "Champignons séchés"),
                      "gui.x.oubli": ("Fishing Rod", "Canne a peche")})
        self.assertEqual(sorted(c), ["gui.x.oubli"])
        self.assertEqual(c["gui.x.oubli"].attendu, "Canne a pêche")

    def test_un_autre_accent_reste_une_faute(self):
        # « péche » ne porte aucun accent là où « pêche » n'en a pas : c'est l'accent fautif, pas un autre mot
        c = constats({"gui.x.faute": ("Fishing Rod", "Canne a péche")})
        self.assertEqual(c["gui.x.faute"].attendu, "Canne a pêche")

    def test_double_sens_quand_l_anglais_porte_les_deux(self):
        # l'anglais dit dry et dried : « sec » et « séché » y sont justes l'un et l'autre
        c = constats({"journal.x": ("Added Dry Totem. Fixed dried tea.", "Totem sec, thé séché"),
                      "gui.x.seul": ("Fixed dried tea.", "Thé sèche")})
        self.assertEqual(sorted(c), ["gui.x.seul"])
        self.assertEqual(c["gui.x.seul"].attendu, "Thé séché")

    def test_nom_propre_de_plusieurs_mots(self):
        # « Cozy Cafe » est exempté là où il figure en entier ; « cafe » seul reste vérifié, noms compris
        c = constats({"itemGroup.x": ("Cozy Cafe", "Cozy Cafe"),
                      "journal.y": ("Added Cozy Cafe", "Ajout de Cozy Cafe, un mini-jeu de cafe"),
                      "item.x.cup": ("Coffee Cup", "Tasse de cafe")})
        self.assertEqual(sorted(c), ["item.x.cup", "journal.y"])
        self.assertEqual(c["journal.y"].attendu, "Ajout de Cozy Cafe, un mini-jeu de café")

    def test_meme_casse(self):
        self.assertEqual([meme_casse("ECRAN", "écran"), meme_casse("Cle", "clé"), meme_casse("cle", "clé")],
                         ["ÉCRAN", "Clé", "clé"])


if __name__ == "__main__":
    unittest.main()
