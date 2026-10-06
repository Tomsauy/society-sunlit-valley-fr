"""La mesure, le banc des filets (spec 3 §1, §4) et l'avancement (§7)."""
import json
import tempfile
import unittest
from pathlib import Path

from chasse.avancement import etat
from chasse.mesure import choisir_banc, decider, projection, rendement, rendement_pack, resultat


def v(classe):
    return {"classe": classe}


class TestResultat(unittest.TestCase):

    def test_par_zone_et_total(self):
        tirage = [{"id": f"a{i}", "zone": "a"} for i in range(600)] + [{"id": f"b{i}", "zone": "b"} for i in range(400)]
        verdicts = {t["id"]: v("correct") for t in tirage}
        verdicts["a1"], verdicts["b2"] = v("majeur"), v("mineur")
        r = resultat(tirage, verdicts)
        self.assertEqual((r["n"], r["majeurs"], r["mineurs"], r["borne_texte"], r["critere"]), (1000, 1, 1, "0,473 %", True))
        self.assertEqual((r["par_zone"]["a"]["majeurs"], r["par_zone"]["b"]["n"]), (1, 400))

    def test_cles_mortes_hors_mesure(self):
        tirage = [{"id": f"a{i}", "zone": "a"} for i in range(100)]
        verdicts = {t["id"]: v("correct") for t in tirage}
        verdicts["a1"] = v("majeur")
        verdicts["a2"] = {"classe": "correct", "raison": "jamais affiché : mod absent"}
        r = resultat(tirage, verdicts)
        self.assertEqual((r["n"], r["majeurs"], r["corrects"], r["mortes"], r["ids_mortes"]), (99, 1, 98, 1, ["a2"]))
        self.assertEqual((r["par_zone"]["a"]["n"], r["par_zone"]["a"]["mortes"]), (99, 1))
        banc = choisir_banc({**verdicts, **{f"c{i}": v("correct") for i in range(5)}}, "g")
        self.assertNotIn("a2", banc["corrects"])

    def test_verdict_manquant(self):
        with self.assertRaises(ValueError):
            resultat([{"id": "x", "zone": "a"}], {"x": {"classe": "en_attente"}})


class TestBanc(unittest.TestCase):

    def setUp(self):
        self.verdicts = {**{f"d{i}": v("majeur" if i < 4 else "mineur") for i in range(10)},
                         **{f"c{i}": v("correct") for i in range(50)}}
        self.banc = choisir_banc(self.verdicts, "banc-1")

    def test_choix(self):
        self.assertEqual(len(self.banc["defauts"]), 10)
        self.assertEqual(len(self.banc["corrects"]), 10)
        self.assertEqual(self.banc, choisir_banc(self.verdicts, "banc-1"))
        with self.assertRaises(ValueError):
            choisir_banc({"d": v("majeur")}, "g")

    def test_rendement_et_decision(self):
        corrects = self.banc["corrects"]
        f1 = rendement({"d0", "d5"}, self.banc)
        f2 = rendement({"d1", "d2", "d3", "d5", "d6", corrects[0], corrects[1], "hors-banc"}, self.banc)
        reunis = rendement({"d0", "d1", "d2", "d3", "d5", "d6", corrects[0], corrects[1]}, self.banc)
        self.assertEqual((f1["precision"], f1["rappel"], f1["fausses_alertes"]), (1.0, 0.2, 0.0))
        self.assertEqual((f2["signales"], f2["rappel_majeurs"], f2["fausses_alertes"]), (7, 0.75, 0.2))
        d = decider(f1, f2, reunis)
        self.assertEqual(d["F2"][0], "resserrer")      # 20 % de fausses alertes
        self.assertEqual(d["F1"][0], "garder")         # d0, majeur, que F2 manque
        self.assertEqual(decider(rendement(set(), self.banc), f2, f2)["F1"][0], "retirer")
        self.assertEqual(projection(f2, 50000, 0.02), round(0.2 * 49000 + 0.5 * 1000))

    def test_rendement_sur_le_pack(self):
        signalements = [{"id": "a", "filets": ["F1"]}, {"id": "b", "filets": ["F1", "F2"]}, {"id": "c", "filets": ["F2"]}]
        verdicts = {"a": v("majeur"), "b": v("fausse_alerte"), "c": v("mineur")}
        r = rendement_pack(signalements, verdicts)
        self.assertEqual(r["F1"], {"signales": 2, "confirmes": 1, "majeurs": 1, "precision": 0.5})
        self.assertEqual(r["F1 + F2"]["confirmes"], 2)


class TestAvancement(unittest.TestCase):

    def test_etat(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "zones" / "a").mkdir(parents=True)
            (Path(d) / "zones" / "a" / "bilan.json").write_text(json.dumps({"signalements": 4, "majeurs": 1, "mineurs": 2,
                                                                            "corriges": 3, "lots": ["a-01"]}))
            (Path(d) / "zones" / "b").mkdir()
            (Path(d) / "mesure-depart").mkdir()
            (Path(d) / "mesure-depart" / "resultat.json").write_text(json.dumps(
                {"n": 1000, "majeurs": 1, "borne_texte": "0,473 %", "critere": True}))
            zones = [{"id": i, "textes": ["x"] * n} for i, n in (("a", 3), ("b", 2), ("c", 1))]
            e = etat(zones, d)
            self.assertEqual([(z["id"], z["statut"], z["corriges"]) for z in e["zones"]],
                             [("a", "faite", 3), ("b", "en_cours", 0), ("c", "a_faire", 0)])
            self.assertEqual(e["mesures"], {"depart": {"n": 1000, "majeurs": 1, "borne": "0,473 %", "critere": True}})


if __name__ == "__main__":
    unittest.main()
