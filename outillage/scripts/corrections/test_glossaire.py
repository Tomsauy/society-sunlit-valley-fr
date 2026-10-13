"""Le glossaire : provenance.json fait foi, GLOSSAIRE.md en est régénéré."""
import json
import tempfile
import unittest
from pathlib import Path

from coherence.config import TERME_GARDE
from corrections.glossaire import ecrire_md, fixer, raison_lisible


def espace_avec(d, glossaire):
    espace = Path(d)
    (espace / "provenance.json").write_text(json.dumps({"cles": {}, "glossaire": glossaire}), encoding="utf-8")
    return espace


def lire(espace):
    return json.loads((espace / "provenance.json").read_text(encoding="utf-8"))["glossaire"]


ADD = {"en": "Add", "fr": "Ajouter", "garde_anglais": False, "origine": "traduction officielle du mod", "raison": "y"}


class TestFixer(unittest.TestCase):

    def test_remplace_l_entree_et_regenere_le_md(self):
        with tempfile.TemporaryDirectory() as d:
            espace = espace_avec(d, [dict(ADD, en="Dye", fr="Colorant")])
            fixer(espace, "Dye", "Teinture", "nom de Mojang")
            self.assertEqual([(e["en"], e["fr"], e["origine"]) for e in lire(espace)],
                             [("Dye", "Teinture", "décision de l'utilisateur")])
            self.assertIn("| Dye | Teinture | Nom de Mojang |", (espace / "GLOSSAIRE.md").read_text(encoding="utf-8"))

    def test_la_casse_distingue_deux_termes(self):
        with tempfile.TemporaryDirectory() as d:
            espace = espace_avec(d, [ADD])
            self.assertIn("proche", fixer(espace, "ADD", "ADD", "mode gardé", garde_anglais=True))
            fixer(espace, "Add", "Ajouter", "mise à jour")
            self.assertEqual({e["en"]: (e["fr"], e["garde_anglais"]) for e in lire(espace)},
                             {"Add": ("Ajouter", False), "ADD": ("ADD", True)})

    def test_un_sens_ne_remplace_que_son_entree(self):
        with tempfile.TemporaryDirectory() as d:
            espace = espace_avec(d, [dict(ADD, en="Jar", fr="Bocal")])
            fixer(espace, "Jar", "Pot", "nom du mod", sens="bloc décoratif")
            fixer(espace, "Jar", "Pot", "nom officiel", sens="bloc décoratif")
            self.assertEqual(sorted((e["fr"], e.get("sens", "")) for e in lire(espace)),
                             [("Bocal", ""), ("Pot", "bloc décoratif")])

    def test_garde_anglais_n_est_change_que_s_il_est_donne(self):
        with tempfile.TemporaryDirectory() as d:
            espace = espace_avec(d, [dict(ADD, en="SHIFT", fr="SHIFT", garde_anglais=True)])
            fixer(espace, "SHIFT", "SHIFT", "touche")
            self.assertTrue(lire(espace)[0]["garde_anglais"])


class TestMarkdown(unittest.TestCase):

    def test_sections_dans_l_ordre_et_termes_gardes_a_part(self):
        with tempfile.TemporaryDirectory() as d:
            espace = espace_avec(d, [
                dict(ADD, en="Zinc", fr="Zinc", origine="identique en français"),
                dict(ADD, en="Copper", fr="Cuivre", origine="Minecraft vanilla (officiel Mojang)"),
                dict(ADD, en="Discord", fr="Discord", garde_anglais=True, raison="marque"),
                dict(ADD, en="Odd", fr="Bizarre", origine="origine inconnue")])
            self.assertEqual(ecrire_md(espace), 4)
            md = (espace / "GLOSSAIRE.md").read_text(encoding="utf-8")
            titres = [l for l in md.splitlines() if l.startswith("## ")]
            self.assertEqual(titres, ["## Termes gardés en anglais — 1", "## Minecraft (traduction officielle de Mojang) — 1",
                                      "## Arbitrages de traduction — 1", "## Mots qui s'écrivent comme en anglais — 1"])
            self.assertIn("| Discord | Marque |", md)
            garde = (espace / "KEEP-ENGLISH.md").read_text(encoding="utf-8")
            self.assertIn("| **Discord** | Marque |", garde)
            self.assertEqual(TERME_GARDE.findall(garde), ["Discord"])

    def test_une_barre_ou_un_saut_de_ligne_ne_cassent_pas_le_tableau(self):
        with tempfile.TemporaryDirectory() as d:
            espace = espace_avec(d, [dict(ADD, en="A|B", fr="Ligne 1\nLigne 2")])
            ecrire_md(espace)
            self.assertIn("| A\\|B | Ligne 1 Ligne 2 |", (espace / "GLOSSAIRE.md").read_text(encoding="utf-8"))

    def test_le_sens_precede_la_raison(self):
        with tempfile.TemporaryDirectory() as d:
            espace = espace_avec(d, [dict(ADD, en="Jar", fr="Pot", sens="bloc décoratif", raison="nom du mod")])
            ecrire_md(espace)
            self.assertIn("| Jar | Pot | sens : bloc décoratif ; Nom du mod |", (espace / "GLOSSAIRE.md").read_text(encoding="utf-8"))


class TestRaisonLisible(unittest.TestCase):

    def test_les_renvois_aux_lots_et_aux_fiches_disparaissent(self):
        cas = {
            "fiche du 30/09 : fut-tonneau": "",
            "fiche du 30/09, question teinture : pluriel du nom Mojang « Teinture noire »":
                "Pluriel du nom Mojang « Teinture noire »",
            "lot 5-01 : Controllable, manette": "Controllable, manette",
            "fiche du sous-projet 3 : mob-ou-creature": "",
            "fiche du sous-projet 3 : travertin-persimmon, garder (option papaye) ; traduction officielle du jar":
                "Traduction officielle du jar",
            "réponse du 01/10 à la question pinceau-better-archeology : versions du pinceau de Mojang":
                "Versions du pinceau de Mojang",
            "réponse de l'utilisateur du 06/10 (lag-ou-ralentissement) : le jeu qui rame": "Le jeu qui rame",
            "réponse de l'utilisateur du 06/10 : light-blue-botania, « bleu clair » comme Mojang":
                "« bleu clair » comme Mojang",
            "jar Railways ; « vert clair » par la fiche du sous-projet 3 : vert-clair-lime": "Jar Railways ; « vert clair »",
            "jar Refined Storage ; « oe », jamais la ligature (fiche du 30/09, question coeur-noyau)":
                "Jar Refined Storage ; « oe », jamais la ligature",
            "marque ; le coréen garde l'anglais": "Marque ; le coréen garde l'anglais",
            "« pierres », comme Mojang ; lot rq-03a": "« pierres », comme Mojang",
            "Lot rq-04a, verdict mineur de mesure-finale-3 du 06/10 (advancements.x.feast.title) : tag « Festins »":
                "Tag « Festins »",
        }
        for brut, attendu in cas.items():
            with self.subTest(brut=brut):
                self.assertEqual(raison_lisible(brut), attendu)


if __name__ == "__main__":
    unittest.main()
