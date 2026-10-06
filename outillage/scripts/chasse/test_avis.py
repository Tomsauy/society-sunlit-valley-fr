"""Signalements, avis, verdicts et lots de la chasse (spec 3 §4, §5, §6)."""
import unittest

from chasse.avis import bilan, desaccords, signalements, verdicts
from chasse.textes import Texte
from chasse.vers_lot import actions, lots
from corrections.lot import LotInvalide, valider_lot


def avis(classe, correction="", **k):
    return dict({"classe": classe, "raison": "r", "correction": correction, "preuves": []}, **k)


class TestSignalements(unittest.TestCase):

    def test_reunion_des_filets(self):
        s = signalements({"a": {"ecart": True, "note": "sens"}, "b": {"ecart": False, "note": ""}},
                         {"a": {"accroche": True, "note": "accord"}, "c": {"accroche": True, "note": "mot"}})
        self.assertEqual(s, [{"id": "a", "filets": ["F1", "F2"], "notes": {"F1": "sens", "F2": "accord"}},
                             {"id": "c", "filets": ["F2"], "notes": {"F2": "mot"}}])


class TestVerdicts(unittest.TestCase):

    def test_accord_desaccord_tiers(self):
        a = {"x": avis("majeur", "X1"), "y": avis("fausse_alerte"), "z": avis("mineur", "Z1")}
        b = {"x": avis("majeur", "X2"), "y": avis("majeur", "Y2"), "z": avis("mineur", "Z1")}
        self.assertEqual(desaccords(a, b), ["y"])
        v = verdicts(a, b)
        self.assertEqual((v["x"]["classe"], v["x"]["correction"], v["x"]["variante"]), ("majeur", "X1", "X2"))
        self.assertNotIn("variante", v["z"])
        self.assertEqual(v["y"], {"id": "y", "classe": "en_attente", "source": "desaccord"})
        v = verdicts(a, b, {"y": avis("mineur", "Y3")})
        self.assertEqual((v["y"]["classe"], v["y"]["source"], v["y"]["correction"]), ("mineur", "tiers", "Y3"))
        self.assertEqual(bilan(v), {"majeur": 1, "mineur": 2, "questions": 0})

    def test_question(self):
        a = {"x": avis("majeur", question="« Rail » ou « Voie » ?")}
        b = {"x": avis("majeur", "Voie")}
        self.assertEqual(verdicts(a, b)["x"]["question"], "« Rail » ou « Voie » ?")

    def test_question_de_b_seul(self):
        a = {"x": avis("majeur", "Voie")}
        b = {"x": avis("majeur", "Voie", question="Rail ?")}
        self.assertEqual(verdicts(a, b)["x"]["question"], "Rail ?")

    def test_question_de_a_avec_tiers(self):
        a = {"x": avis("majeur", "Rail", question="Rail ou Voie ?")}
        b = {"x": avis("correct")}
        v = verdicts(a, b, {"x": avis("majeur", "Voie")})
        self.assertEqual((v["x"]["source"], v["x"]["question"]), ("tiers", "Rail ou Voie ?"))

    def test_avis_sur_des_textes_differents(self):
        with self.assertRaises(ValueError):
            desaccords({"x": avis("correct")}, {"y": avis("correct")})


class TestVersLot(unittest.TestCase):

    def test_actions_et_journal(self):
        textes = {"k.a": Texte("k.a", "Apple", "Pome", "projet", "society", "society"),
                  "journal#2": Texte("journal#2", "- Added x", "- Ajout de x", "journal", "journal", "journal"),
                  "journal#4": Texte("journal#4", "- Fixed y", "- Corrigé y", "journal", "journal", "journal"),
                  "k.q": Texte("k.q", "Rail", "Rail", "projet", "society", "society"),
                  "k.m": Texte("k.m", "Mild", "Doux", "projet", "society", "society")}
        journal = "## 4.1.5\n- Ajout de x\n\n- Corrigé y\n"
        v = {"k.a": {"classe": "majeur", "raison": "faute", "correction": "Pomme", "variante": "Pommes", "fr": "Pome"},
             "journal#2": {"classe": "mineur", "raison": "calque", "correction": "- Ajout d'un x", "fr": "- Ajout de x"},
             "journal#4": {"classe": "mineur", "raison": "forme", "correction": "- Correction de y", "fr": "- Corrigé y"},
             "k.q": {"classe": "majeur", "raison": "nom", "correction": "", "question": "?", "fr": "Rail"},
             "k.c": {"classe": "fausse_alerte", "raison": "ok"}, "k.e": {"classe": "en_attente"},
             "k.m": {"classe": "correct", "raison": "ok", "question": "Doux ou Mou ?"}}
        liste, ecartes = actions(v, textes, journal, "chasse society-1")
        self.assertEqual(ecartes, ["k.m", "k.q", "k.e"])
        self.assertEqual(liste[0], {"type": "correction", "cle": "k.a", "avant": "Pome", "apres": "Pomme",
                                    "motif": "[chasse society-1] majeur : faute", "variante": "Pommes"})
        self.assertEqual(liste[1]["cle"], "journal")
        self.assertEqual(liste[1]["apres"], "## 4.1.5\n- Ajout d'un x\n\n- Correction de y\n")
        lot = lots("society-1", liste, {"zone": "society-1"})[0]
        with self.assertRaises(LotInvalide):  # la variante se départage avant d'appliquer
            valider_lot(lot)
        del lot["actions"][0]["variante"]
        valider_lot(lot)
        self.assertEqual((lot["lot"], lot["nature"], lot["perimetre"]), ("society-1-01", "chasse", ["journal", "k.a"]))

    def test_variante_du_journal_refusee(self):
        textes = {"journal#2": Texte("journal#2", "- Added x", "- Ajout de x", "journal", "journal", "journal")}
        v = {"journal#2": {"classe": "mineur", "raison": "r", "correction": "- A", "variante": "- B", "fr": "- Ajout de x"}}
        liste, _ = actions(v, textes, "## 4.1.5\n- Ajout de x\n", "s")
        with self.assertRaises(LotInvalide):
            valider_lot(lots("s", liste, {})[0])

    def test_ligne_du_journal_decalee(self):
        textes = {"journal#2": Texte("journal#2", "- Added x", "- Ajout de x", "journal", "journal", "journal")}
        v = {"journal#2": {"classe": "mineur", "raison": "r", "correction": "- A", "fr": "- Ajout de x"}}
        self.assertEqual(actions(v, textes, "## 4.1.5\n- Nouveau\n- Ajout de x\n", "s"), ([], ["journal#2"]))

    def test_sans_texte_relu(self):
        textes = {"k.a": Texte("k.a", "Apple", "Pome", "projet", "society", "society")}
        v = {"k.a": {"classe": "majeur", "raison": "r", "correction": "Pomme"}}
        self.assertEqual(actions(v, textes, "", "s"), ([], ["k.a"]))

    def test_texte_change_depuis_l_avis(self):
        # Un lot n'écrase pas un texte changé après la relecture : sa correction partirait d'un texte périmé.
        textes = {"k.a": Texte("k.a", "Apple", "Pomme rouge", "projet", "society", "society")}
        v = verdicts({"k.a": avis("majeur", "Pomme")}, {"k.a": avis("majeur", "Pomme")}, vus={"k.a": "Pome"})
        self.assertEqual(v["k.a"]["fr"], "Pome")
        self.assertEqual(actions(v, textes, "", "s"), ([], ["k.a"]))

    def test_decoupe(self):
        liste = [{"type": "correction", "cle": f"k.{i}", "avant": "a", "apres": "b", "motif": "m"} for i in range(301)]
        self.assertEqual([len(l["actions"]) for l in lots("z", liste, {})], [150, 150, 1])


if __name__ == "__main__":
    unittest.main()
