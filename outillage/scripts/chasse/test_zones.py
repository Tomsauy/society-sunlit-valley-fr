"""Zones de la chasse et couverture exacte (spec 3 §4, phase 2)."""
import unittest

from chasse.textes import Texte
from chasse.zones import blocs, completer, construire, liens_de_familles, verifier_couverture


def texte(i, unite):
    return Texte(i, "en", "fr", "projet", unite.split("/")[0], unite)


class TestZones(unittest.TestCase):

    def test_couverture_exacte(self):
        # Point d'attention 2 : un texte dans deux zones, dans aucune, ou inconnu est nommé.
        zones = [{"id": "a", "blocs": ["a"], "textes": ["t1", "t2"], "indivisible": False},
                 {"id": "b", "blocs": ["b"], "textes": ["t2", "t9"], "indivisible": False},
                 {"id": "b", "blocs": ["c"], "textes": [], "indivisible": False}]
        p = verifier_couverture(zones, ["t1", "t2", "t3"])
        self.assertEqual(p, ["zone b : identifiant en double", "t2 : dans les zones a et b", "zone b : vide",
                             "t9 : dans la zone b, absent de l'inventaire", "t3 : dans aucune zone"])

    def test_trop_grande(self):
        zones = [{"id": "a", "blocs": ["a", "b"], "textes": [f"t{i}" for i in range(12)], "indivisible": False}]
        ids = [f"t{i}" for i in range(12)]
        self.assertEqual(verifier_couverture(zones, ids, plafond=5, tolerance=0),
                         ["zone a : 12 textes, plus que 5, sans bloc indivisible"])
        self.assertEqual(verifier_couverture(zones, ids, plafond=5, tolerance=7), [])
        zones[0]["indivisible"] = True
        self.assertEqual(verifier_couverture(zones, ids, plafond=5, tolerance=0), [])

    def test_familles_non_coupees(self):
        # Unité trop grande : coupée en sous-unités, sauf là où une famille lie deux de ses morceaux.
        textes = ([texte(f"item.big.n{i}", "big") for i in range(4)]
                  + [texte(f"big.page.p{i}", "big") for i in range(3)] + [texte("big.gui.g", "big")])
        b = blocs(textes, plafond=5)
        self.assertEqual(sorted(b), ["big/big.gui", "big/big.page", "big/noms"])
        b = blocs(textes, liens=[("item.big.n0", "big.gui.g")], plafond=5)
        self.assertEqual(sorted(b), ["big/big.gui", "big/big.page"])
        self.assertEqual(len(b["big/big.gui"]), 5)

    def test_construire(self):
        textes = ([texte(f"gros.page.p{i}", "gros") for i in range(4)] + [texte(f"gros.gui.g{i}", "gros") for i in range(3)]
                  + [texte(f"k.a{i}", "a") for i in range(3)] + [texte(f"k.b{i}", "b") for i in range(3)] + [texte("k.c", "c")]
                  + [texte("ftbquests.chapter.w.q", "quetes:w"), texte("journal#1", "journal")])
        zones = construire(textes, [], {"cuisine": ["a", "b"]}, plafond=5, gros=6, tolerance=1)
        self.assertEqual([(z["id"], z["blocs"], len(z["textes"])) for z in zones], [
            ("cuisine-1", ["a"], 3), ("cuisine-2", ["b"], 3), ("divers", ["c"], 1),
            ("gros-1", ["gros/gros.page"], 4), ("gros-2", ["gros/gros.gui"], 3),
            ("livres", ["journal"], 1), ("quetes", ["quetes:w"], 1)])
        self.assertEqual(verifier_couverture(zones, [t.id for t in textes], plafond=5, tolerance=1), [])
        self.assertEqual(zones, construire(textes, [], {"cuisine": ["a", "b"]}, plafond=5, gros=6, tolerance=1))

    def test_completer(self):
        zones = [{"id": "a", "theme": "cuisine", "blocs": ["a"], "textes": ["k.a0", "k.vieux"], "indivisible": False}]
        textes = [texte("k.a0", "a"), texte("k.a1", "a"), texte("k.z", "zz")]
        nouvelles, rapport = completer(zones, textes, [], {"cuisine": ["a"]})
        self.assertEqual(verifier_couverture(nouvelles, ["k.a0", "k.a1", "k.z"]), [])
        self.assertEqual(rapport, {"ajoutes": {"k.a1": "a", "k.z": "divers"}, "retires": ["k.vieux"]})

    def test_liens_de_familles(self):
        class F:
            membres = {"item.s.aged_carp_roe": ({"nom": "vieillis"}, "carp"),
                       "item.s.aged_eel_roe": ({"nom": "vieillis"}, "eel"), "item.s.carp_roe": ({"nom": "oeufs"}, "carp")}
        self.assertEqual(liens_de_familles(F()), [("item.s.aged_carp_roe", "item.s.aged_eel_roe")])


if __name__ == "__main__":
    unittest.main()
