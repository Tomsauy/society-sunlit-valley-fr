"""La ligne de commande de la chasse, de bout en bout sur un petit pack (spec 3 §4 à §6)."""
import contextlib
import io
import json
import unittest
from pathlib import Path

import chasser
from coherence.fabrique import ESPACE, PACK_COMPLET, pack_et_espace


class TestChasser(unittest.TestCase):

    def setUp(self):
        self.dossier, self.pack, self.espace = pack_et_espace(PACK_COMPLET, ESPACE)
        self.addCleanup(self.dossier.cleanup)
        self.chasse = self.espace / "chasse"
        self.chasse.mkdir()
        (self.chasse / "themes.json").write_text(json.dumps({"deco": ["furniture"]}), encoding="utf-8")

    def lancer(self, *args):
        sortie = io.StringIO()
        with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(sortie):
            code = chasser.main(["--racine", str(self.pack), "--espace", str(self.espace), "--chasse", str(self.chasse),
                                 *map(str, args)])
        return code, sortie.getvalue()

    def test_de_bout_en_bout(self):
        code, sortie = self.lancer("zones")
        self.assertEqual(code, 0, sortie)
        zones = json.loads((self.chasse / "zones.json").read_text(encoding="utf-8"))["zones"]
        ids = sorted(i for z in zones for i in z["textes"])
        self.assertIn("item.society.bac", ids)
        self.assertNotIn("block.minecraft.stone", ids)  # Mojang
        self.assertEqual(self.lancer("zones", "--verifier")[0], 0)
        tirage = self.chasse / "mesure-depart" / "tirage.json"
        self.assertEqual(self.lancer("tirer", "--n", 10, "--graine", "g", "--sortie", tirage)[0], 0)
        dossier = self.chasse / "mesure-depart" / "paquets"
        self.assertEqual(self.lancer("paquets", "--filet", "mesure", "--tirage", tirage, "--dossier", dossier)[0], 0)
        entree = json.loads((dossier / "mesure" / "001.entree.json").read_text(encoding="utf-8"))
        for relecteur, classe in (("A", "majeur"), ("B", "correct")):
            items = [{"id": e["id"], "classe": classe, "raison": "r", "preuves": [f"cle:{e['id']}"],
                      "correction": e["fr"] + " !" if classe == "majeur" else ""} for e in entree["elements"]]
            (dossier / "mesure" / f"001.sortie-{relecteur}.json").write_text(
                json.dumps({"paquet": entree["paquet"], "sorties": items}), encoding="utf-8")
        self.assertEqual(self.lancer("valider", "--dossier", dossier, "--filet", "mesure", "--relecteur", "A", "--preuves")[0], 0)
        verdicts = self.chasse / "mesure-depart" / "verdicts.json"
        code, sortie = self.lancer("verdicts", "--dossier", dossier, "--famille", "mesure", "--sortie", verdicts)
        self.assertEqual(code, 1, sortie)  # dix désaccords attendent le tiers
        self.assertEqual(self.lancer("paquets", "--filet", "tiers-mesure", "--dossier", dossier)[0], 0)
        tiers = json.loads((dossier / "tiers-mesure" / "001.entree.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(tiers["elements"][0]["avis"]), ["A", "B"])
        items = [{"id": e["id"], "classe": "correct", "raison": "r", "preuves": []} for e in tiers["elements"]]
        (dossier / "tiers-mesure" / "001.sortie-C.json").write_text(
            json.dumps({"paquet": tiers["paquet"], "sorties": items}), encoding="utf-8")
        self.assertEqual(self.lancer("verdicts", "--dossier", dossier, "--famille", "mesure", "--sortie", verdicts)[0], 0)
        resultat = self.chasse / "mesure-depart" / "resultat.json"
        code, sortie = self.lancer("mesurer", "--tirage", tirage, "--verdicts", verdicts, "--sortie", resultat)
        self.assertEqual(code, 0, sortie)
        self.assertIn("0 défaut(s) majeur(s) sur 10", sortie)
        code, sortie = self.lancer("avancement")
        self.assertEqual(json.loads((self.chasse / "avancement.json").read_text())["mesures"]["depart"]["n"], 10)

    def test_filets_md(self):
        filets = self.chasse / "filets.md"
        chasser.ajouter_section(filets, "Sur le banc", "| a |\n")
        chasser.ajouter_section(filets, "Sur tout le pack", "| b |\n")
        self.assertEqual(filets.read_text(encoding="utf-8"),
                         "# Rendement des filets\n\n## Sur le banc\n\n| a |\n\n## Sur tout le pack\n\n| b |\n")

    def test_mortes_reconnues(self):
        (self.chasse / "mortes.json").write_text(json.dumps([{"cle": "item.society.bac", "motif": "essai"}]),
                                                 encoding="utf-8")
        self.lancer("zones")
        zones = json.loads((self.chasse / "zones.json").read_text(encoding="utf-8"))
        self.assertNotIn("item.society.bac", [i for z in zones["zones"] for i in z["textes"]])
        self.assertEqual(zones["exclus"]["morte"], 1)

    def test_compter(self):
        question = self.chasse / "q.json"
        question.write_text(json.dumps({"id": "q", "cles": ["autre"]}), encoding="utf-8")
        code, sortie = self.lancer("compter", "--en", "shipping", "--fr", "bac", "--ajouter-a", question)
        self.assertEqual(code, 0, sortie)
        self.assertTrue(sortie.startswith("2 texte(s) ; society 2"), sortie)
        self.assertEqual(json.loads(question.read_text(encoding="utf-8"))["cles"],
                         ["autre", "item.society.bac", "tooltip.society.bac"])

    def test_sortie_d_agent_fautive(self):
        self.lancer("zones")
        zone = json.loads((self.chasse / "zones.json").read_text(encoding="utf-8"))["zones"][0]["id"]
        dossier = self.chasse / "zones" / zone / "paquets"
        self.lancer("paquets", "--filet", "F2", "--zone", zone, "--dossier", dossier)
        entree = json.loads((dossier / "F2" / "001.entree.json").read_text(encoding="utf-8"))
        (dossier / "F2" / "001.sortie.json").write_text(json.dumps({"paquet": entree["paquet"], "sorties": [
            {"id": "inventee", "accroche": False, "note": ""}]}), encoding="utf-8")
        code, sortie = self.lancer("valider", "--dossier", dossier, "--filet", "F2")
        self.assertEqual(code, 1)
        self.assertIn("inventee : n'est pas dans le paquet", sortie)

    def _paquet_f2(self):
        self.lancer("zones")
        zone = json.loads((self.chasse / "zones.json").read_text(encoding="utf-8"))["zones"][0]["id"]
        dossier = self.chasse / "zones" / zone / "paquets"
        self.assertEqual(self.lancer("paquets", "--filet", "F2", "--zone", zone, "--dossier", dossier)[0], 0)
        entree = json.loads((dossier / "F2" / "001.entree.json").read_text(encoding="utf-8"))
        return zone, dossier, entree

    def test_id_pas_une_chaine(self):
        _, dossier, entree = self._paquet_f2()
        for faux in (["a"], {"a": 1}):
            (dossier / "F2" / "001.sortie.json").write_text(json.dumps({"paquet": entree["paquet"], "sorties": [
                {"id": faux, "accroche": False, "note": ""}]}), encoding="utf-8")
            code, sortie = self.lancer("valider", "--dossier", dossier, "--filet", "F2")
            self.assertEqual(code, 1, sortie)
            self.assertIn("« id » doit être une chaîne", sortie)

    def test_utf8_invalide(self):
        _, dossier, _ = self._paquet_f2()
        (dossier / "F2" / "001.sortie.json").write_bytes(b"\xff\xfe{")
        code, sortie = self.lancer("valider", "--dossier", dossier, "--filet", "F2")
        self.assertEqual(code, 1, sortie)
        self.assertIn("sortie illisible", sortie)

    def test_aucun_paquet(self):
        code, sortie = self.lancer("valider", "--dossier", self.chasse / "absent", "--filet", "F2")
        self.assertEqual(code, 2, sortie)
        self.assertIn("aucun paquet sous", sortie)

    def test_paquets_sans_ecrasement(self):
        zone, dossier, _ = self._paquet_f2()
        (dossier / "F2" / "001.sortie.json").write_text("{}", encoding="utf-8")
        code, sortie = self.lancer("paquets", "--filet", "F2", "--zone", zone, "--dossier", dossier)
        self.assertEqual(code, 1, sortie)
        self.assertIn(str(dossier / "F2"), sortie)
        self.assertTrue((dossier / "F2" / "001.sortie.json").is_file())
        code, sortie = self.lancer("paquets", "--filet", "F2", "--zone", zone, "--dossier", dossier, "--remplacer")
        self.assertEqual(code, 0, sortie)
        self.assertFalse((dossier / "F2" / "001.sortie.json").exists())
        self.assertTrue((dossier / "F2" / "001.entree.json").is_file())

    def test_paquets_sans_selecteur(self):
        code, sortie = self.lancer("paquets", "--filet", "F2", "--dossier", self.chasse / "p")
        self.assertEqual(code, 2, sortie)
        self.assertIn("--zone", sortie)

    def test_voir_refus_explique(self):
        code, sortie = self.lancer("voir", "block.minecraft.stone")
        self.assertEqual(code, 2)
        self.assertIn("cherche avec grep", sortie)

    def test_cles_compte_ce_qu_il_ecrit(self):
        zone, _, _ = self._paquet_f2()
        sortie_cles = self.chasse / "cles.txt"
        code, sortie = self.lancer("cles", "--zone", zone, "--sortie", sortie_cles)
        n = len(sortie_cles.read_text(encoding="utf-8").splitlines())
        self.assertIn(f"{n} clé(s)", sortie)


if __name__ == "__main__":
    unittest.main()
