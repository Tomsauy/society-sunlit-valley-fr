"""L'échantillon d'un sous-lot pour la page de relecture, et la lecture des verdicts (spec 2 §9)."""
import json
import tempfile
import unittest
from pathlib import Path

from corrections.echantillon import document, echantillonner, lire_verdicts


class TestEchantillon(unittest.TestCase):

    def test_tirage_reproductible(self):
        actions = [{"type": "correction"}] * 100
        premier = echantillonner(actions, "3b-01")
        self.assertEqual((premier, len(premier)), (echantillonner(actions, "3b-01"), 30))
        self.assertNotEqual(premier, echantillonner(actions, "3b-02"))
        self.assertEqual(echantillonner(actions[:12], "x"), list(range(12)))

    def test_document(self):
        lot = {"lot": "1a-01", "nature": "decisions", "perimetre": ["a", "b"], "actions": [
            {"type": "correction", "cle": "a", "avant": "Piège", "apres": "Casier", "motif": "fiche : crabes",
             "question": "crabes"},
            {"type": "exception", "controle": "references", "cle": "b", "motif": "matière"},
            {"type": "mot_generique", "mot": "Cherry", "motif": "matière"}]}
        doc = document(lot, "Noms d'objets", "résumé", 2828, 2800, True,
                       {"a": "Crab Trap", "b": "Cherry Planks"}.get, {"b": "Planches de cerisier"}.get)
        self.assertEqual((doc["id"], doc["attend_verdict"], doc["actions"], doc["statut"]), ("1a-01", True, 3, "echantillon"))
        self.assertEqual(doc["exceptions"], [{"cle": "b", "controle": "references", "motif": "matière"}])
        premier, deuxieme, troisieme = doc["echantillon"]
        self.assertEqual((premier["n"], premier["anglais"], premier["avant"], premier["apres"]),
                         (1, "Crab Trap", "Piège", "Casier"))
        self.assertEqual((deuxieme["avant"], deuxieme["apres"], deuxieme["controle"]), ("Planches de cerisier", "", "references"))
        self.assertEqual((troisieme["cle"], troisieme["anglais"], troisieme["type"]), ("Cherry", "", "mot_generique"))

    def test_lire_verdicts(self):
        with tempfile.TemporaryDirectory() as d:
            dossier = Path(d) / "verdicts"
            dossier.mkdir()
            for n, v in ((1, {"verdict": "bon"}), (2, {"verdict": "refus", "commentaire": "accord"})):
                (dossier / f"1a-01-{n}.json").write_text(json.dumps(v), encoding="utf-8")
            (dossier / "1a-01-r-1.json").write_text(json.dumps({"verdict": "bon"}), encoding="utf-8")  # autre lot
            page = {"id": "1a-01", "echantillon": [{"n": 1, "cle": "a"}, {"n": 2, "cle": "b"}, {"n": 3, "cle": "c"}]}
            r = lire_verdicts(d, page)
            self.assertTrue(r["complet"])  # le n° 3 n'a pas de verdict : absence = bon
            self.assertEqual([(x["cle"], x["commentaire"]) for x in r["refus"]], [("b", "accord")])
            (dossier / "1a-01-3.json").write_text(json.dumps({"verdict": "bon"}), encoding="utf-8")
            self.assertTrue(lire_verdicts(d, page)["complet"])


if __name__ == "__main__":
    unittest.main()
