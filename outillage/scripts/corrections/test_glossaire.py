"""Une entrée du glossaire écrite aux deux endroits qui la portent."""
import json
import tempfile
import unittest
from pathlib import Path

from corrections.glossaire import SECTION, fixer


class TestGlossaire(unittest.TestCase):

    def test_fixer(self):
        with tempfile.TemporaryDirectory() as d:
            espace = Path(d)
            (espace / "provenance.json").write_text(json.dumps({"cles": {}, "glossaire": [
                {"en": "Dye", "fr": "Colorant", "garde_anglais": False, "origine": "x", "raison": "y"}]}), encoding="utf-8")
            (espace / "GLOSSAIRE.md").write_text("# Glossaire\n\n| Anglais | Français | Origine |\n|---|---|---|\n"
                                                 "| Dye | Colorant | x |\n", encoding="utf-8")
            fixer(espace, "Dye", "Teinture", "fiche du 30/09 : teinture")
            glossaire = json.loads((espace / "provenance.json").read_text(encoding="utf-8"))["glossaire"]
            self.assertEqual((len(glossaire), glossaire[0]["fr"], glossaire[0]["en"]), (1, "Teinture", "Dye"))
            self.assertIn("| Dye | Teinture | fiche du 30/09 : teinture |", (espace / "GLOSSAIRE.md").read_text(encoding="utf-8"))
            fixer(espace, "Crab Trap", "Casier à crabes", "fiche du 30/09 : crabes")
            md = (espace / "GLOSSAIRE.md").read_text(encoding="utf-8")
            self.assertIn(SECTION, md)
            self.assertTrue(md.endswith("| Crab Trap | Casier à crabes | fiche du 30/09 : crabes |\n"))

    def _espace(self, d):
        espace = Path(d)
        (espace / "provenance.json").write_text(json.dumps({"cles": {}, "glossaire": [
            {"en": "Add", "fr": "Ajouter", "garde_anglais": False, "origine": "x", "raison": "y"}]}), encoding="utf-8")
        (espace / "GLOSSAIRE.md").write_text("# Glossaire\n\n| Anglais | Français | Origine |\n|---|---|---|\n"
                                             "| Add | Ajouter | x |\n", encoding="utf-8")
        return espace

    def test_la_casse_distingue_deux_termes(self):
        with tempfile.TemporaryDirectory() as d:
            espace = self._espace(d)
            msg = fixer(espace, "ADD", "ADD", "mode gardé")
            self.assertIn("proche", msg)  # avertissement, pas écrasement
            fixer(espace, "Add", "Ajouter", "mise à jour")
            gl = {e["en"]: e["fr"] for e in json.loads((espace / "provenance.json").read_text(encoding="utf-8"))["glossaire"]}
            self.assertEqual(gl, {"Add": "Ajouter", "ADD": "ADD"})
            md = (espace / "GLOSSAIRE.md").read_text(encoding="utf-8")
            self.assertIn("| Add | Ajouter | mise à jour |", md)
            self.assertIn("| ADD | ADD | mode gardé |", md)
            self.assertEqual(md.count("| Add |"), 1)

    def test_mise_a_jour_meme_casse(self):
        with tempfile.TemporaryDirectory() as d:
            espace = self._espace(d)
            fixer(espace, "Add", "Additionner", "nouvelle décision")
            gl = json.loads((espace / "provenance.json").read_text(encoding="utf-8"))["glossaire"]
            self.assertEqual([(e["en"], e["fr"]) for e in gl], [("Add", "Additionner")])


if __name__ == "__main__":
    unittest.main()
