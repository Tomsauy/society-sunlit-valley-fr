"""Les consignes des agents (spec 3 §5) : une par filet, qui décrit la sortie que la validation attend."""
import unittest
from pathlib import Path

from chasse.paquets import CLASSES, CONSIGNES, FICHIER_CONSIGNE

DEPOT = Path(__file__).resolve().parents[3]
CHAMPS = {"F1-retro": ("retro",), "F1-comparaison": ("ecart", "note"), "F2": ("accroche", "note"),
          "mesure": ("classe", "raison", "correction", "preuves"),
          "confirmation": ("classe", "raison", "correction", "preuves", "question"),
          "tiers-mesure": ("classe", "raison", "correction", "preuves"),
          "tiers-confirmation": ("classe", "raison", "correction", "preuves")}


class TestConsignes(unittest.TestCase):

    def test_chaque_filet_a_sa_consigne(self):
        for filet, nom in FICHIER_CONSIGNE.items():
            with self.subTest(filet):
                texte = (DEPOT / CONSIGNES / nom).read_text(encoding="utf-8")
                for champ in ("paquet", "sorties", "id", *CHAMPS[filet]):
                    self.assertIn(f'"{champ}"', texte, f"{nom} ne nomme pas « {champ} »")
                self.assertIn("0 problème(s)", texte)

    def test_aveugles_et_preuves(self):
        lire = lambda nom: (DEPOT / CONSIGNES / nom).read_text(encoding="utf-8")  # noqa: E731
        self.assertIn("Tu ne vois pas l'anglais d'origine", lire("F1-retrotraduction.md"))
        self.assertIn("Tu ne vois pas le français", lire("F1-comparaison.md"))
        self.assertIn("Tu ne vois pas l'anglais", lire("F2-lecture.md"))
        for nom in ("confirmation.md", "mesure-relecteur.md", "tiers.md"):
            self.assertIn("N'invente jamais une preuve", lire(nom))
        for famille, classes in CLASSES.items():
            texte = lire(FICHIER_CONSIGNE[famille])
            for classe in classes:
                self.assertIn(f"`{classe}`", texte)

    def test_decisions_et_preuves_exigees(self):
        lire = lambda nom: (DEPOT / CONSIGNES / nom).read_text(encoding="utf-8")  # noqa: E731
        for nom in ("confirmation.md", "mesure-relecteur.md", "tiers.md"):
            texte = lire(nom)
            with self.subTest(nom):
                for repere in ("fr-workspace/chasse/fiche/questions/", "fr-workspace/chasse/zones/*/questions/",
                               "termes_imposes.json", "familles.json", "noms_propres.json",
                               "docs/specs/2026-09-30-fiche-decisions.json", "mc_fr_fr.json", '"question": "',
                               "garde la classe du défaut", '"question": "<qid>"'):
                    self.assertIn(repere, texte)
                # Une question déjà posée ne fait pas d'un défaut une fausse alerte : la mesure le compte.
                self.assertNotIn("Pour ce seul point : `fausse_alerte`", texte)
                self.assertNotIn("Pour ce seul point : `correct`", texte)
        for chemin in ("fr-workspace/coherence/termes_imposes.json", "fr-workspace/coherence/familles.json",
                       "fr-workspace/coherence/noms_propres.json", "docs/specs/2026-09-30-fiche-decisions.json",
                       "fr-workspace/references/mc_fr_fr.json", "fr-workspace/references/mc_en_us.json"):
            self.assertTrue((DEPOT / chemin).is_file(), chemin)
        for nom in ("confirmation.md", "mesure-relecteur.md"):
            texte = lire(nom)
            with self.subTest(nom):
                for repere in ("« jamais affiché : »", "jeu:", "nom faux", "intouchés",
                               "fr-workspace/jars/*.jar", "zipfile", "'/lang/' not in n",
                               "grep -rl '<clé>' society-sunlit-valley/kubejs society-sunlit-valley/config",
                               "→ 0 fichier"):
                    self.assertIn(repere, texte)
                self.assertNotIn("fr-workspace/extracted society", texte)
        self.assertIn("fr-workspace/jars/*.jar", lire("tiers.md"))
        self.assertIn("fr_fr.json", lire("F1-comparaison.md"))
        self.assertIn("en_us.json", lire("F2-lecture.md"))
        self.assertIn("society", lire("F2-lecture.md"))


if __name__ == "__main__":
    unittest.main()
