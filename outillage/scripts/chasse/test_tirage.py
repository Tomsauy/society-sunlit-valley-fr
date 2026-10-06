"""Tirage stratifié (spec 3 §4) et borne de Clopper-Pearson (spec 3 §1)."""
import unittest

from chasse.stats import borne_haute, critere_tenu, en_pourcent
from chasse.tirage import quotas, tirer


def zone(nom, n):
    return {"id": nom, "textes": [f"{nom}.{i:04d}" for i in range(n)]}


class TestQuotas(unittest.TestCase):

    def test_minimum_puis_proportionnel(self):
        q = quotas({"a": 1000, "b": 100, "c": 10}, 100)
        self.assertEqual(sum(q.values()), 100)
        self.assertTrue(all(v >= 5 for v in q.values()))
        self.assertGreater(q["a"], q["b"])

    def test_zone_minuscule(self):
        # Point d'attention 1 : une zone de 2 textes en donne 2, jamais 5, et le compte total tient.
        q = quotas({"a": 1000, "petite": 2, "vide_ou_presque": 1}, 50)
        self.assertEqual((q["petite"], q["vide_ou_presque"], sum(q.values())), (2, 1, 50))

    def test_trop_ou_trop_peu(self):
        with self.assertRaises(ValueError):
            quotas({"a": 10}, 11)
        with self.assertRaises(ValueError):
            quotas({z: 100 for z in "abcdef"}, 20)  # 6 zones × 5 = 30 > 20

    def test_toute_la_zone(self):
        self.assertEqual(quotas({"a": 3, "b": 3}, 6), {"a": 3, "b": 3})


class TestTirer(unittest.TestCase):

    def test_reproductible_et_sans_doublon(self):
        zones = [zone("a", 500), zone("b", 40), zone("c", 3)]
        t1, t2 = tirer(zones, 100, "graine-1"), tirer(zones, 100, "graine-1")
        self.assertEqual(t1, t2)
        self.assertEqual(len({x["id"] for x in t1}), 100)
        self.assertNotEqual(t1, tirer(zones, 100, "graine-2"))
        self.assertEqual(sum(1 for x in t1 if x["zone"] == "c"), 3)
        self.assertTrue(all(x["id"].startswith(x["zone"] + ".") for x in t1))


class TestBorne(unittest.TestCase):

    def test_table_de_la_spec(self):
        # Spec 3 §1 : 1 000 textes, 1 défaut → 0,47 % ; 2 → 0,63 % ; 2 000 textes, 4 → 0,46 % ; 5 → 0,53 %.
        self.assertEqual(en_pourcent(borne_haute(1, 1000)), "0,473 %")
        self.assertEqual(en_pourcent(borne_haute(2, 1000)), "0,628 %")
        self.assertEqual(en_pourcent(borne_haute(2, 1500)), "0,419 %")
        self.assertEqual(en_pourcent(borne_haute(3, 1500)), "0,516 %")
        self.assertEqual(en_pourcent(borne_haute(4, 2000)), "0,457 %")
        self.assertEqual(en_pourcent(borne_haute(5, 2000)), "0,525 %")
        self.assertTrue(critere_tenu(4, 2000))
        self.assertFalse(critere_tenu(5, 2000))

    def test_bords(self):
        # Point d'attention 5 : à k = 0, la borne vaut 1 - 0,05^(1/n) ; jamais 0.
        self.assertAlmostEqual(borne_haute(0, 1000), 1 - 0.05 ** (1 / 1000), places=9)
        self.assertAlmostEqual(borne_haute(0, 2000), 1 - 0.05 ** (1 / 2000), places=9)
        self.assertEqual(borne_haute(10, 10), 1.0)
        for k, n in ((-1, 10), (11, 10), (0, 0)):
            with self.assertRaises(ValueError):
                borne_haute(k, n)


if __name__ == "__main__":
    unittest.main()
