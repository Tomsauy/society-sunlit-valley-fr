"""Termes imposés."""
import unittest
from pathlib import Path

from coherence.config import Config
from coherence.controles import CONTROLES
from coherence.corpus import ChampLivre, Corpus
from coherence.modele import BLOQUANT, SIGNALE, Options
from coherence.registre import Registre

TERMES = [
    {"anglais": "crimson", "francais": "carmin", "motif": "STYLE §7"},
    {"anglais": "ash", "francais": "frêne", "cles": r"\.ash_", "motif": "essence Ash"},
    {"anglais": "polished", "francais": ["poli", "polie", "polis", "polies"], "motif": "vanilla"},
]
LIGNES = {
    "block.x.crimson_planks": ("Crimson Planks", "Planches cramoisies"),
    "block.x.crimson_slab": ("Crimson Slab", "Dalle carmin"),
    "tooltip.x.crimson": ("Found in Crimson Forests", "Se trouve dans les forêts cramoisies"),
    "block.x.ash_door": ("Ash Door", "Porte en cendre"),
    "item.x.ash": ("Ash", "Cendre"),
    "block.x.polished_andesite": ("Polished Andesite", "Andésite polie"),
}


class TestTerminologie(unittest.TestCase):

    def test_constats(self):
        c = Corpus()
        for cle, (en, fr) in LIGNES.items():
            c.en[cle], c.fr[cle], c.origine_fr[cle] = en, fr, "projet"
        config = Config(espace=Path("."), termes_imposes=TERMES)
        constats = {x.cle: x for x in CONTROLES["terminologie"](c, Registre(c, config), config, Options())}
        self.assertEqual({k: v.statut for k, v in constats.items()},
                         {"block.x.crimson_planks": BLOQUANT, "tooltip.x.crimson": SIGNALE, "block.x.ash_door": BLOQUANT})
        self.assertEqual(constats["block.x.ash_door"].attendu, "frêne")

    def test_champs_de_livres(self):
        """Le terme est imposé partout, livres compris : un champ de livre est un texte, donc signalé."""
        c = Corpus()
        c.livres = [ChampLivre("almanac/entries/trees/darkcherry.json", "/name", "Crimson Tree", "Arbre cramoisi"),
                    ChampLivre("almanac/entries/trees/crimson.json", "/name", "Crimson Tree", "Arbre carmin")]
        config = Config(espace=Path("."), termes_imposes=TERMES)
        constats = CONTROLES["terminologie"](c, Registre(c, config), config, Options())
        self.assertEqual([(x.cle, x.statut) for x in constats], [(c.livres[0].cle, SIGNALE)])

    def test_portee(self):
        """M7 : « portee » limite un terme aux noms d'objets (« noms ») ou aux textes (« textes ») ; « tout » par défaut."""
        c = Corpus()
        for cle, (en, fr) in {"block.x.ash_log": ("Ash Log", "Bûche de cendre"),
                              "tooltip.x.ash": ("Burn it to ash", "Brûle-le en cendre")}.items():
            c.en[cle], c.fr[cle], c.origine_fr[cle] = en, fr, "projet"
        attendus = {"noms": ["block.x.ash_log"], "textes": ["tooltip.x.ash"], "tout": ["block.x.ash_log", "tooltip.x.ash"]}
        for portee, cles in attendus.items():
            with self.subTest(portee=portee):
                config = Config(espace=Path("."), termes_imposes=[{"anglais": "ash", "francais": "frêne", "portee": portee,
                                                                   "motif": "essai"}])
                constats = CONTROLES["terminologie"](c, Registre(c, config), config, Options())
                self.assertEqual(sorted(x.cle for x in constats), cles)

    def test_forme_a_majuscule(self):
        """Une forme imposée écrite avec sa majuscule (STYLE §7 : « Maîtrise du minage ») la garde partout."""
        termes = [{"anglais": "mining mastery", "francais": "Maîtrise du minage", "motif": "STYLE §7"}]
        c = Corpus()
        for cle, (en, fr) in {"jei.x.mining": ("Requires Mining Mastery", "Nécessite la maîtrise du minage"),
                              "quest.x.mining": ("Unlock Mining Mastery", "Débloque la Maîtrise du minage"),
                              "quest.x.debut": ("Mining Mastery unlocks it", "Maîtrise du minage requise")}.items():
            c.en[cle], c.fr[cle], c.origine_fr[cle] = en, fr, "projet"
        config = Config(espace=Path("."), termes_imposes=termes)
        constats = CONTROLES["terminologie"](c, Registre(c, config), config, Options())
        self.assertEqual([x.cle for x in constats], ["jei.x.mining"])
        self.assertIn("majuscule", constats[0].detail)


if __name__ == "__main__":
    unittest.main()
