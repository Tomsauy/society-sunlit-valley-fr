"""Le fichier de lot : ce que l'applicateur accepte de lire (spec 2 §8)."""
import unittest

from corrections.lot import MAX_ACTIONS, LotInvalide, valider_lot


def lot(*actions, **champs):
    return {"lot": "1a-01", "nature": "decisions", "perimetre": ["a"], "actions": list(actions), **champs}


CORRECTION = {"type": "correction", "cle": "a", "avant": "x", "apres": "y", "motif": "m"}


class TestLot(unittest.TestCase):

    def test_lot_valide(self):
        valider_lot(lot(CORRECTION,
                        {"type": "correction", "cle": "b", "avant": None, "apres": "y", "motif": "m", "espace": "everycomp"},
                        {"type": "exception", "controle": "casse", "cle": "a", "objet": ["k1", "k2"], "motif": "m"},
                        {"type": "retrait", "controle": "casse", "cle": "a", "motif": "m"},
                        {"type": "mot_generique", "mot": "Cherry", "motif": "m"},
                        {"type": "trace", "cle": "a", "fr": "x", "motif": "m", "question": "longwings-descriptions"},
                        {"type": "renvoi", "controle": "references", "cle": "a", "motif": "m"}))

    def test_nature_chasse(self):
        valider_lot(lot(CORRECTION, nature="chasse"))

    def test_refus(self):
        cas = {
            "sans identifiant": lot(CORRECTION, lot=""),
            "nature inconnue": lot(CORRECTION, nature="divers"),
            "type inconnu": lot(dict(CORRECTION, type="suppression")),
            "sans motif": lot(dict(CORRECTION, motif=" ")),
            "correction sans avant": lot({k: v for k, v in CORRECTION.items() if k != "avant"}),
            "clé absente sans espace": lot(dict(CORRECTION, avant=None)),
            "exception sans contrôle": lot({"type": "exception", "cle": "a", "motif": "m"}),
            "question vide": lot(dict(CORRECTION, question="")),
            "trop d'actions": lot(*[dict(CORRECTION, cle=f"k{i}") for i in range(MAX_ACTIONS + 1)]),
            "variante non départagée": lot(dict(CORRECTION, variante="z"), nature="chasse"),
        }
        for nom, donnees in cas.items():
            with self.subTest(nom), self.assertRaises(LotInvalide):
                valider_lot(donnees)


if __name__ == "__main__":
    unittest.main()
