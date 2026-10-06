"""Contrôle nombres (spec 3 §5) : les nombres de l'anglais se retrouvent dans le français, dans le même ordre."""
import unittest
from pathlib import Path

from coherence.config import Config
from coherence.controles import CONTROLES
from coherence.controles.nombres import ecart, nombres_en, nombres_fr
from coherence.corpus import ChampLivre, Corpus
from coherence.modele import Options


class TestExtraction(unittest.TestCase):

    def test_codes_et_identifiants_ne_comptent_pas(self):
        # Point d'attention 3 : les chiffres des codes, des identifiants et des références ne sont pas des nombres.
        self.assertEqual(nombres_en("%1$s gives %2$s §6Gold§r &6x&r {0} $(l:a/b2)x$(/l) minecraft:stone_2"), [])
        self.assertEqual(nombres_en("Use {ftbquests.chapter.a1.quest2B.title}"), [])
        self.assertEqual(nombres_en("%d%% faster"), [])

    def test_separateurs(self):
        self.assertEqual(nombres_en("1,000 coins, 1.50 s, 2.0 m, v1.20.1"), ["1000", "1.5", "2", "1.20.1"])
        self.assertEqual(nombres_fr("1 000 pièces, 1,5 s, 65.536 objets, 1 000"), ["1000", "1.5", "65536", "1000"])

    def test_en_lettres(self):
        self.assertEqual(nombres_fr("Soigne trois coeurs, de zéro au cinquième"), ["3", "0", "5"])

    def test_ecart(self):
        self.assertEqual(ecart("Heals 3 hearts", "Soigne trois coeurs"), "")
        self.assertEqual(ecart("Craft x3 items", "Fabrique x3 objets"), "")
        self.assertEqual(ecart("1st place", "1re place"), "")
        self.assertEqual(ecart("Lasts 20 seconds", "Dure 10 secondes"), "nombres perdus : 20")
        self.assertEqual(ecart("Between 2 and 5", "Entre 5 et 2"), "ordre différent : 2 5 en anglais, 5 2 en français")
        self.assertEqual(ecart("Between 2 and 5", "Entre 2 et 5 (soit 3 de plus)"), "")  # un nombre en plus : permis
        self.assertEqual(ecart("Recycle 1,000,000 mB", "Recycle 1,000,000 mB"), "séparateur anglais : 1,000,000")

    def test_faux_positifs_de_la_premiere_mesure(self):
        # un, une, seul, second, double, triple valent leur chiffre
        self.assertEqual(ecart("by 1 day", "d'un jour"), "")
        self.assertEqual(ecart("at least 1 time", "au moins une fois"), "")
        self.assertEqual(ecart("a value of 1 lets", "permet à un seul joueur"), "")
        self.assertEqual(ecart("the 2nd Slot", "du second emplacement"), "")
        self.assertEqual(ecart("Preserves Jars 3x the value", "Les bocaux triplent la valeur"), "")
        self.assertEqual(ecart("Doubles 2x", "Les bocaux doublent la valeur"), "")
        # une liste de nombres à virgules s'écrit pareil des deux côtés
        self.assertEqual(ecart("levels 1,3,4 and 1,3", "niveaux 1,3,4 et 1,3"), "")
        self.assertEqual(nombres_fr("1,3,4"), ["1,3,4"])
        self.assertEqual(nombres_fr("1,5"), ["1.5"])
        # l'infobulle $(t:…) est affichée : ses nombres comptent des deux côtés
        self.assertEqual(nombres_en("a $(t:11x11x11)pool$()"), ["11", "11", "11"])
        self.assertEqual(ecart("a $(t:11x11x11)pool$()", "un $(t:un bassin)bassin$()"), "nombres perdus : 11 11 11")
        self.assertEqual(ecart("a $(t:11x11x11)pool$()", "un $(t:11x11x11)bassin$()"), "")
        # un balisage non affiché est ignoré des deux côtés
        self.assertEqual(ecart("<remove_size>0.025</remove_size>Exporting", "<remove_size>0.2</remove_size>Exportation"), "")


class TestControle(unittest.TestCase):

    def preparer(self, active):
        c = Corpus()
        c.en.update({"a.x": "Lasts 20 seconds", "a.y": "Heals 3 hearts", "a.z": "Lasts 5 s", "a.v": "Stone 2"})
        c.fr.update({"a.x": "Dure 10 secondes", "a.y": "Soigne trois coeurs", "a.z": "Dure 4 s", "a.v": "Roche"})
        c.origine_fr.update({"a.x": "projet", "a.y": "projet", "a.z": "jar", "a.v": "vanilla"})
        c.livres = [ChampLivre("almanac/e.json", "/text", "Plant 4 seeds", "Plante des graines", ())]
        return c, Config(espace=Path("."), regles={"casse_textes": True, "pourcentages": "espace", "nombres": active})

    def test_regle_en_attente(self):
        corpus, config = self.preparer(False)
        self.assertEqual(CONTROLES["nombres"](corpus, None, config, Options()), [])
        self.assertEqual(len(CONTROLES["nombres"](corpus, None, config, Options(toutes_regles=True))), 3)

    def test_projet_jar_livres_jamais_mojang(self):
        corpus, config = self.preparer(True)
        constats = CONTROLES["nombres"](corpus, None, config, Options())
        self.assertEqual(sorted(c.cle for c in constats), ["a.x", "a.z", "almanac/e.json#/text"])
        self.assertTrue(all(c.statut == "bloquant" for c in constats))


if __name__ == "__main__":
    unittest.main()
