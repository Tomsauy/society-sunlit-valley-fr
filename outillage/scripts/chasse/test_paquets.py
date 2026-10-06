"""Paquets des agents : ce que chaque filet voit, la forme de ce qu'il rend (spec 3 §5)."""
import json
import tempfile
import unittest
from pathlib import Path

from chasse.paquets import ecrire_entrees, entrees, lire_sorties, valider, verifier_preuve

ELEMENTS = [{"id": f"k.{i}", "espace": "society", "en": f"Apple {i}", "fr": f"Pomme {i}", "retro": f"Apple {i}",
             "temoins": {}, "notes": {"F2": "?"}} for i in range(5)]


class TestEntrees(unittest.TestCase):

    def test_aveugles(self):
        retro = entrees("F1-retro", "z", ELEMENTS)[0]["elements"][0]
        comparaison = entrees("F1-comparaison", "z", ELEMENTS)[0]["elements"][0]
        lecture = entrees("F2", "z", ELEMENTS)[0]["elements"][0]
        self.assertEqual(sorted(retro), ["espace", "fr", "id"])
        self.assertEqual(sorted(comparaison), ["en", "espace", "id", "retro"])
        self.assertNotIn("en", lecture)

    def test_decoupe_et_noms(self):
        paquets = entrees("F2", "society-1", ELEMENTS, taille=2)
        self.assertEqual([p["paquet"] for p in paquets], ["society-1/F2/001", "society-1/F2/002", "society-1/F2/003"])
        self.assertEqual([len(p["elements"]) for p in paquets], [2, 2, 1])
        self.assertEqual(paquets[0]["consigne"], "fr-workspace/chasse/consignes/F2-lecture.md")
        with self.assertRaises(ValueError):
            entrees("F1-comparaison", "z", [{"id": "k", "en": "x"}])  # sans rétrotraduction


class TestValider(unittest.TestCase):

    def setUp(self):
        self.entree = entrees("confirmation", "z", ELEMENTS[:3])[0]

    def sortie(self, items):
        return {"paquet": "z/confirmation/001", "sorties": items}

    def avis(self, i, **k):
        base = {"id": f"k.{i}", "classe": "fausse_alerte", "raison": "le sens passe", "correction": "", "preuves": []}
        base.update(k)
        return base

    def test_bonne_sortie(self):
        items = [self.avis(0), self.avis(1, classe="majeur", correction="Pommes 1", preuves=["cle:k.1"]), self.avis(2)]
        self.assertEqual(valider(self.entree, self.sortie(items)), [])

    def test_cles_en_trop_en_moins_en_double(self):
        # Point d'attention 4 : une sortie qui ne répond pas exactement au paquet est refusée tout entière.
        items = [self.avis(0), self.avis(0), self.avis(9)]
        p = valider(self.entree, self.sortie(items))
        self.assertIn("k.0 : rendu 2 fois", p)
        self.assertIn("k.1 : manque dans la sortie", p)
        self.assertIn("k.2 : manque dans la sortie", p)
        self.assertIn("k.9 : n'est pas dans le paquet", p)

    def test_champs(self):
        items = [self.avis(0, classe="peut-etre"), self.avis(1, classe="majeur", correction="Pomme 1"),
                 self.avis(2, classe="mineur", correction="", preuves=["j'ai vérifié"])]
        p = valider(self.entree, self.sortie(items))
        self.assertIn("k.0 : « classe » parmi majeur, mineur, fausse_alerte", p)
        self.assertIn("k.1 : « correction » identique au texte", p)
        self.assertIn("k.2 : « correction » vide pour un défaut", p)
        self.assertTrue(any(x.startswith("k.2 : « preuves »") for x in p))

    def test_question_sans_correction(self):
        items = [self.avis(0, classe="majeur", question="« Rail » ou « Voie » ?"), self.avis(1), self.avis(2)]
        self.assertEqual(valider(self.entree, self.sortie(items)), [])

    def test_mauvais_paquet_et_forme(self):
        self.assertEqual(valider(self.entree, []), ["la sortie n'est pas un objet JSON"])
        p = valider(self.entree, {"paquet": "autre", "sorties": "x"})
        self.assertEqual(p, ["« paquet » vaut 'autre', attendu 'z/confirmation/001'",
                             "« sorties » : une liste d'objets est attendue"])

    def test_f1_et_f2(self):
        retro = entrees("F1-retro", "z", ELEMENTS[:1])[0]
        self.assertEqual(valider(retro, {"paquet": "z/F1-retro/001", "sorties": [{"id": "k.0", "retro": " "}]}),
                         ["k.0 : « retro » vide"])
        f2 = entrees("F2", "z", ELEMENTS[:1])[0]
        self.assertEqual(valider(f2, {"paquet": "z/F2/001", "sorties": [{"id": "k.0", "accroche": True}]}),
                         ["k.0 : « note » vide pour un signalement"])
        self.assertEqual(valider(f2, {"paquet": "z/F2/001", "sorties": [{"id": "k.0", "accroche": "oui"}]}),
                         ["k.0 : « accroche » : true ou false"])


class TestFichiers(unittest.TestCase):

    def test_lire_sorties_et_preuves(self):
        with tempfile.TemporaryDirectory() as d:
            chemins = ecrire_entrees(d, entrees("F2", "z", ELEMENTS, taille=3))
            self.assertEqual([c.name for c in chemins], ["001.entree.json", "002.entree.json"])
            (Path(d) / "F2" / "001.sortie.json").write_text(json.dumps({"paquet": "z/F2/001", "sorties": [
                {"id": f"k.{i}", "accroche": i == 1, "note": "bizarre" if i == 1 else ""} for i in range(3)]}))
            rendus, problemes = lire_sorties(d, "F2")
            self.assertEqual(sorted(rendus), ["k.0", "k.1", "k.2"])
            self.assertEqual(problemes, ["z/F2/002 : pas de sortie (002.sortie.json)"])
            self.assertEqual(lire_sorties(d, "F2", "A")[1][0], "z/F2/001 : pas de sortie (001.sortie-A.json)")
            self.assertEqual(lire_sorties(d, "F2", numero="001")[1], [])  # le seul paquet 001 : complet
            (Path(d) / "a.txt").write_text("un\ndeux\n")
            self.assertEqual(verifier_preuve("fichier:a.txt:2", set(), [d]), "")
            self.assertEqual(verifier_preuve("fichier:a.txt:3", set(), [d]), "fichier:a.txt:3 : ligne 3 hors du fichier")
            self.assertEqual(verifier_preuve("fichier:b.txt", set(), [d]), "fichier:b.txt : fichier introuvable")
            self.assertEqual(verifier_preuve("cle:k.1", {"k.1"}, [d]), "")
            self.assertEqual(verifier_preuve("cle:k.9", {"k.1"}, [d]), "cle:k.9 : clé inconnue du corpus")


if __name__ == "__main__":
    unittest.main()
