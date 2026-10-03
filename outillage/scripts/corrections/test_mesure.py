"""La mesure d'un sous-lot : sélection, paquets, squelette, attendus sûrs, questions de la fiche."""
import json
import tempfile
import unittest
from pathlib import Path

from coherence.modele import BLOQUANT, SIGNALE, Constat
from coherence.rapport import Resultat
from corrections.mesure import ANNEXE, attendus_surs, cles_des_questions, premier_paquet, selectionner, squelette


def constat(controle, cle, objet="", attendu="", actuel="x", detail=""):
    return Constat(controle, cle, BLOQUANT, actuel=actuel, attendu=attendu, objet=objet, detail=detail)


class TestMesure(unittest.TestCase):

    def test_selectionner(self):
        r = Resultat(bloquants=[constat("casse", "a")], en_dette=[constat("references", "b")],
                     signales=[Constat("terminologie", "c", SIGNALE)])
        self.assertEqual([c.cle for c in selectionner(r, controles=["references", "terminologie"])], ["b", "c"])
        self.assertEqual([c.cle for c in selectionner(r, cles=["a"])], ["a"])
        self.assertEqual([c.cle for c in selectionner(r, controles=["casse", "references"], bloquants_seulement=True)], ["a"])

    def test_paquet_par_objet(self):
        constats = [constat("references", f"t{i}", objet=f"o{i % 3}") for i in range(9)]
        paquet = premier_paquet(constats, 7, par_objet=True)
        self.assertEqual(sorted({c.objet for c in paquet}), ["o0", "o1"])  # deux groupes de 3 tiennent, pas trois
        self.assertEqual(len(paquet), 6)

    def test_groupe_plus_grand_que_la_taille(self):
        # Point de vigilance 5
        constats = [constat("references", f"t{i:03}", objet="o") for i in range(200)]
        self.assertEqual(len(premier_paquet(constats, 150, par_objet=True)), 150)

    def test_squelette(self):
        lot = squelette("3b-01", "references", {"controles": ["references"]},
                        [constat("references", "b", objet="o")], {"e"}, dette=[{}] * 5)
        self.assertEqual((lot["perimetre"], lot["actions"], lot["mesure"]["dette"]), (["b", "e"], [], 5))
        self.assertEqual(lot["constats"][0]["cle"], "b")

    def test_attendus_surs(self):
        textes = {"a": "x", "b": "x", "c": "x", "d": "x", "e": "x"}
        constats = [constat("accents", "a", attendu="à"), constat("references", "b", attendu="Nom"),
                    constat("conventions", "c", attendu=""), constat("casse", "d", attendu="y"),
                    constat("accents", "d", attendu="z"), constat("orthographe", "e", objet="savanne", attendu="savane")]
        actions, laissees = attendus_surs(constats, textes.get, formes_interdites={"savanne"})
        self.assertEqual([(a["cle"], a["avant"], a["apres"]) for a in actions], [("a", "x", "à"), ("e", "x", "savane")])
        self.assertEqual(sorted(laissees), ["b", "c", "d"])

    def test_cles_des_questions(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / ANNEXE).parent.mkdir(parents=True)
            (Path(d) / ANNEXE).write_text(json.dumps({"questions": [{"id": "crabes", "cles": ["k1", "k2"]},
                                                                    {"id": "koi", "cles": ["k3"]}]}), encoding="utf-8")
            self.assertEqual(cles_des_questions(d, ["crabes", "koi"]), {"k1", "k2", "k3"})
            with self.assertRaises(ValueError):
                cles_des_questions(d, ["inconnue"])


if __name__ == "__main__":
    unittest.main()
