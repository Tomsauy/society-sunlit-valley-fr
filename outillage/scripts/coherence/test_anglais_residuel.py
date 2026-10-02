"""Anglais recopié tel quel, textes restés en anglais, étiquettes brutes."""
import unittest
from pathlib import Path

from coherence.config import Config
from coherence.controles import CONTROLES
from coherence.corpus import Corpus
from coherence.modele import Options

LIGNES = {
    "block.minecraft.cookie": ("Cookie", "Cookie", "vanilla"),
    "block.waystones.black_sharestone": ("Black Sharestone", "Noir Sharestone", "jar"),
    "item.autumnity.foul_berries": ("Foul Berries", "Foul Berries", "projet"),
    "item.x.cookie_jar": ("Cookie Jar", "Pot à cookie", "projet"),
    "item.x.tunnel_kit": ("Tunnel Kit", "Kit de tunnel", "projet"),
    "item.x.bin": ("Red Bin", "Bin rouge", "projet"),
    "painting.x.backyard": ("Backyard", "Backyard", "projet"),
    "controllable.key.split": ("Split Stack", "Split Stack", "jar"),
    "config.x.garde": ("Draw Distance", "Draw Distance", "projet"),
    "ftbquests.a.task": ("Any #botania:generating_special", "N'importe quelle #botania:generating_special", "projet"),
}


def constats(lignes=None, **config):
    c = Corpus()
    for cle, (en, fr, origine) in {**LIGNES, **(lignes or {})}.items():
        c.en[cle], c.fr[cle], c.origine_fr[cle] = en, fr, origine
    provenance = {"cles": {"config.x.garde": [{"type": "arbitrage_identique", "decision": "garde_anglais"}]},
                  "glossaire": config.pop("glossaire", [])}
    configuration = Config(espace=Path("."), garder_anglais={"Backyard"}, provenance=provenance,
                           vocabulaire={"kit": [{"forme": "kit", "sens": "kit"}],
                                        "tunnel": [{"forme": "tunnel", "sens": "tunnel"}]}, **config)
    return {x.cle: x for x in CONTROLES["anglais_residuel"](c, None, configuration, Options())}


class TestAnglaisResiduel(unittest.TestCase):

    def test_constats(self):
        c = constats()
        self.assertEqual(sorted(c), ["block.waystones.black_sharestone", "controllable.key.split",
                                     "ftbquests.a.task", "item.autumnity.foul_berries"])
        self.assertIn("sharestone", c["block.waystones.black_sharestone"].detail)
        self.assertIn("resté en anglais", c["controllable.key.split"].detail)
        self.assertIn("#botania:generating_special", c["ftbquests.a.task"].detail)

    def test_exemptions(self):
        c = constats(noms_propres={"Sharestone": "nom inventé du mod"},
                     glossaire=[{"en": "Foul Berries", "fr": "Foul Berries", "garde_anglais": True}])
        self.assertEqual(sorted(c), ["controllable.key.split", "ftbquests.a.task"])

    def test_un_chiffre_romain_n_est_pas_de_l_anglais(self):
        c = constats(lignes={"enchantment.level.38": ("XXXVIII", "XXXVIII", "projet"),
                             "botania.roman13": ("XIII", "XIII", "jar"),
                             "item.x.salsa": ("Mild Salsa", "Salsa Mild", "jar")})
        self.assertNotIn("enchantment.level.38", c)
        self.assertNotIn("botania.roman13", c)
        self.assertIn("mild", c["item.x.salsa"].detail)  # des lettres romaines ne font pas un nombre

    def test_nom_propre_de_plusieurs_mots(self):
        c = constats(lignes={"block.x.villagers_fright": ("A Bottle of 'Villagers Fright'",
                                                          "Bouteille de 'Villagers Fright'", "jar"),
                             "item.x.villager_hat": ("Villager Hat", "Chapeau Villager", "jar")},
                     noms_propres={"Villagers Fright": "cuvée de Vinery"})
        self.assertNotIn("block.x.villagers_fright", c)                   # le nom figure en entier
        self.assertIn("villager", c["item.x.villager_hat"].detail)        # « Villager » seul n'est pas exempté


if __name__ == "__main__":
    unittest.main()
