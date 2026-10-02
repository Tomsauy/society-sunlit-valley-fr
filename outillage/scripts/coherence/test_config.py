"""Chargement des données de cohérence."""
import tempfile
import unittest
from pathlib import Path

from coherence import config as config_mod
from coherence.config import ConfigInvalide, _exceptions, _renvois
from coherence.fabrique import donnees_vides, ecrire
from coherence.modele import Options


class TestConfig(unittest.TestCase):

    def setUp(self):
        self.dossier = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier.cleanup)
        self.espace = Path(self.dossier.name)
        ecrire(self.espace, donnees_vides())

    def test_fichiers_vides(self):
        c = config_mod.charger_config(self.espace)
        self.assertEqual((c.exceptions, c.dette, c.familles), ([], [], {"familles": [], "accords": {}}))
        self.assertEqual(c.provenance, {"cles": {}})
        self.assertEqual(c.regles, {"casse_textes": False, "pourcentages": ""})
        self.assertEqual(c.majuscules, {})

    def test_fichier_absent(self):
        """Un fichier de données absent viderait son contrôle sans bruit, et le rapport inviterait à purger la
        dette : chaque fichier lu est requis, et l'erreur le nomme."""
        requis = [chemin for chemin in donnees_vides() if chemin in config_mod.FICHIERS_REQUIS]
        self.assertEqual(sorted(requis), sorted(config_mod.FICHIERS_REQUIS))
        self.assertIn("accents/vocabulaire.json", requis)
        self.assertIn("provenance.json", requis)
        self.assertIn("KEEP-ENGLISH.md", requis)
        self.assertIn("coherence/majuscules.json", requis)
        for chemin in requis:
            with self.subTest(fichier=chemin):
                (self.espace / chemin).unlink()
                with self.assertRaisesRegex(config_mod.ConfigInvalide, f"{Path(chemin).name} introuvable"):
                    config_mod.charger_config(self.espace)
                ecrire(self.espace, {chemin: donnees_vides()[chemin]})

    def test_fichiers_lus(self):
        ecrire(self.espace, {
            "coherence/exceptions.json": [{"controle": "codes", "cle": "a", "motif": "voulu"}],
            "accents/vocabulaire.json": {"cle": [{"forme": "clé", "sens": "key"}]},
            "KEEP-ENGLISH.md": "| Terme | Pourquoi |\n|---|---|\n| **Backyard** | titre |\n",
        })
        c = config_mod.charger_config(self.espace)
        self.assertEqual(c.exceptions[0]["motif"], "voulu")
        self.assertEqual(c.vocabulaire["cle"][0]["forme"], "clé")
        self.assertEqual(c.garder_anglais, {"Backyard"})

    def test_termes_gardes(self):
        """M5 : une seule source des termes écrits tels quels à dessein, que casse, anglais_residuel et le test
        d'injection partagent : noms propres, KEEP-ENGLISH, termes que le glossaire garde en anglais. Pas
        majuscules.json, que casse lit seul (STYLE §2) : accents et anglais_residuel ne l'exemptent pas."""
        ecrire(self.espace, {
            "coherence/noms_propres.json": {"Cozy Cafe": "nom du café"},
            "coherence/majuscules.json": {"Slime": "garde sa majuscule, comme une personne"},
            "KEEP-ENGLISH.md": "| **Backyard** | titre |\n",
            "provenance.json": {"cles": {}, "glossaire": [{"en": "Toast", "garde_anglais": True},
                                                          {"en": "Bin", "fr": "Bac", "garde_anglais": False}]},
        })
        self.assertEqual(sorted(config_mod.charger_config(self.espace).termes_gardes()), ["Backyard", "Cozy Cafe", "Toast"])

    def test_json_illisible(self):
        ecrire(self.espace, {"coherence/dette.json": "[{"})
        with self.assertRaisesRegex(config_mod.ConfigInvalide, "dette.json"):
            config_mod.charger_config(self.espace)

    def test_forme_ou_valeur_invalide(self):
        """M2 : un JSON valide mais de mauvaise forme, ou une valeur hors de son domaine, est refusé au chargement en
        nommant le fichier, au lieu d'une trace de pile ou d'une règle activée à rebours."""
        cas = {
            "coherence/dette.json": ["x"],
            "coherence/exceptions.json": [{"controle": "codes"}],
            "coherence/termes_imposes.json": [{"anglais": "crimson", "motif": "sans français"}],
            "coherence/regles.json": {"casse_textes": False, "pourcentages": "espaces"},
            "coherence/familles.json": {"familles": [{"nom": "x"}], "accords": {}},
            "coherence/largeurs.json": [{"cle": "a", "limite": "46", "motif": "m"}],
            "coherence/formes_interdites.json": [{"forme": "savanne"}],
            "coherence/mots_generiques.json": ["Light"],
            "coherence/gabarits.json": {"a": [["nom"]]},
            "coherence/scripts_patches.json": {"kubejs/a.js": {"motif": "sans base"}},
            "coherence/double_sens.json": [{"anglais": "dry(", "justes": ["sec"], "motif": "m"}],
            "coherence/majuscules.json": ["Slime"],
            "provenance.json": {"glossaire": []},
        }
        for chemin, contenu in cas.items():
            with self.subTest(fichier=chemin):
                ecrire(self.espace, {chemin: contenu})
                with self.assertRaisesRegex(config_mod.ConfigInvalide, Path(chemin).name):
                    config_mod.charger_config(self.espace)
                ecrire(self.espace, {chemin: donnees_vides()[chemin]})
        config_mod.charger_config(self.espace)  # tout est revenu à sa valeur vide, valide

    def test_regles_en_attente(self):
        c = config_mod.charger_config(self.espace)
        self.assertEqual((c.regle("casse_textes", Options()), c.regle("pourcentages", Options())), (False, ""))
        tout = Options(toutes_regles=True)
        self.assertEqual((c.regle("casse_textes", tout), c.regle("pourcentages", tout)), (True, "espace"))
        c.regles["pourcentages"] = "colle"
        self.assertEqual(c.regle("pourcentages", tout), "colle")

    def test_ecriture(self):
        config_mod.ecrire(self.espace, "dette", [{"cle": "é"}])
        texte = (self.espace / "coherence" / "dette.json").read_text(encoding="utf-8")
        self.assertEqual(texte, '[\n {\n  "cle": "é"\n }\n]\n')

    def test_exception_empreinte_et_question(self):
        _exceptions(Path("exceptions.json"), [{"controle": "codes", "cle": "a", "motif": "m",
                                               "empreinte": "0123456789ab", "question": "porte-orange"}])
        for champ in ("empreinte", "question"):
            with self.subTest(champ=champ), self.assertRaises(ConfigInvalide):
                _exceptions(Path("exceptions.json"), [{"controle": "codes", "cle": "a", "motif": "m", champ: 12}])

    def test_renvois(self):
        _renvois(Path("renvois.json"), [{"controle": "codes", "cle": "a", "motif": "étape 3"}])
        with self.assertRaises(ConfigInvalide):
            _renvois(Path("renvois.json"), [{"controle": "codes", "cle": "a"}])   # sans motif


if __name__ == "__main__":
    unittest.main()
