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
            fixer(espace, "dye", "Teinture", "fiche du 30/09 : teinture")
            glossaire = json.loads((espace / "provenance.json").read_text(encoding="utf-8"))["glossaire"]
            self.assertEqual((len(glossaire), glossaire[0]["fr"], glossaire[0]["en"]), (1, "Teinture", "Dye"))
            self.assertIn("| Dye | Teinture | fiche du 30/09 : teinture |", (espace / "GLOSSAIRE.md").read_text(encoding="utf-8"))
            fixer(espace, "Crab Trap", "Casier à crabes", "fiche du 30/09 : crabes")
            md = (espace / "GLOSSAIRE.md").read_text(encoding="utf-8")
            self.assertIn(SECTION, md)
            self.assertTrue(md.endswith("| Crab Trap | Casier à crabes | fiche du 30/09 : crabes |\n"))


if __name__ == "__main__":
    unittest.main()
