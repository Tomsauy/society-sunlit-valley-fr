"""Le vérificateur du chantier des accents."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import compare_accents
from compare_accents import comparer, plier

# Table de référence, tenue identique dans les trois implémentations : ce fichier,
# site/server/search.test.js, et AccentsTest.java dans le dépôt du mod. Elle
# n'existe qu'en triple, faute de corpus commun — la tenir à jour est manuel.
CAS_DE_REFERENCE = (
    ("Ragoût", "ragout"),
    ("Clé rouge", "cle rouge"),
    ("Cœur", "coeur"),
    ("Ægir", "aegir"),
    ("ǣ", "ae"),               # ordre : ligature APRÈS le NFC, sinon « æ »
    ("Ǿl", "ol"),              # idem pour le O barré accentué
    ("Straße", "strasse"),
    ("STRAẞE", "strasse"),     # le S dur majuscule doit converger avec le minuscule
    ("Łącze magazynowe", "lacze magazynowe"),
    ("Cài đặt", "cai dat"),
    ("Avbjóðing", "avbjoding"),
    ("한국어", "한국어"),         # ni décomposé en jamos, ni touché
)


class TestPlier(unittest.TestCase):

    def test_table_de_reference(self):
        for texte, attendu in CAS_DE_REFERENCE:
            with self.subTest(texte=texte):
                self.assertEqual(plier(texte), attendu)

    def test_la_table_de_reference_est_idempotente(self):
        for texte, _ in CAS_DE_REFERENCE:
            with self.subTest(texte=texte):
                self.assertEqual(plier(plier(texte)), plier(texte))

    def test_retire_les_accents(self):
        self.assertEqual(plier("Ragoût de morue"), "ragout de morue")
        self.assertEqual(plier("Clé rouge"), "cle rouge")
        self.assertEqual(plier("Hameçon"), "hamecon")

    def test_traite_les_ligatures(self):
        self.assertEqual(plier("Cœur"), "coeur")
        self.assertEqual(plier("Cœur"), plier("Coeur"))

    def test_laisse_les_ideogrammes(self):
        self.assertEqual(plier("한국어"), "한국어")
        self.assertEqual(plier("中文"), "中文")

    def test_est_idempotent(self):
        for texte in ("Ragoût", "Cœur", "한국어", "Blé", ""):
            self.assertEqual(plier(plier(texte)), plier(texte))

    def test_distingue_accent_et_fond(self):
        # Le coeur du vérificateur : « Canapé » et « Canape » ne diffèrent que
        # par l'accent ; « Canapé » et « Canape chic » diffèrent sur le fond.
        self.assertEqual(plier("Canapé blanc"), plier("Canape blanc"))
        self.assertNotEqual(plier("Canapé blanc"), plier("Canape chic blanc"))


class TestComparer(unittest.TestCase):
    """Le classement lui-même, sur un vrai dépôt à deux commits.

    `comparer()` portait toute la logique du contrôle sans aucun test : c'est
    elle qui a rangé une clé ressuscitée dans un compteur, où personne ne
    pouvait la voir. Les quatre cas qu'elle doit distinguer ont chacun le leur.
    """

    LANG = "kubejs/assets/society/lang/fr_fr.json"

    @classmethod
    def setUpClass(cls):
        cls.depot = Path(tempfile.mkdtemp(prefix="compare-accents-"))
        cls._git("init", "-q", "-b", "principale")
        cls._git("config", "user.email", "test@example.invalid")
        cls._git("config", "user.name", "Test")
        cls._ecrire(cls.LANG, json.dumps({
            "item.society.wheat": "Ble",
            "item.society.couch": "Canape blanc",
            "item.society.dead": "Jeton mort",
        }))
        cls._ecrire("patchouli_books/guide/fr_fr/entries/a.json", json.dumps(
            {"pages": [{"text": "Un ragout de morue"}]}))
        cls._commit("depart")
        cls.avant = cls._sha()
        cls._ecrire(cls.LANG, json.dumps({
            "item.society.wheat": "Blé",              # accent seul
            "item.society.couch": "Canapé chic blanc",  # fond (et accent)
            "item.society.new": "Carte autorisée",    # apparue
        }))                                            # .dead : disparue
        cls._ecrire("patchouli_books/guide/fr_fr/entries/a.json", json.dumps(
            {"pages": [{"text": "Un ragoût de morue"}]}))
        cls._commit("chantier")
        cls.apres = cls._sha()
        cls._ecrire(cls.LANG, "{ceci n'est pas du JSON")
        cls._commit("casse")
        cls.casse = cls._sha()
        cls._pack_reel = compare_accents.PACK
        compare_accents.PACK = cls.depot

    @classmethod
    def tearDownClass(cls):
        compare_accents.PACK = cls._pack_reel
        shutil.rmtree(cls.depot, ignore_errors=True)

    @classmethod
    def _git(cls, *args):
        subprocess.run(["git", "-C", str(cls.depot), *args], check=True,
                       capture_output=True, text=True)

    @classmethod
    def _ecrire(cls, chemin, contenu):
        f = cls.depot / chemin
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(contenu, encoding="utf-8")

    @classmethod
    def _commit(cls, message):
        cls._git("add", "-A")
        cls._git("commit", "-q", "-m", message)

    @classmethod
    def _sha(cls):
        r = subprocess.run(["git", "-C", str(cls.depot), "rev-parse", "HEAD"],
                           check=True, capture_output=True, text=True)
        return r.stdout.strip()

    def test_une_cle_apparue_est_listee_et_nommee(self):
        r = comparer(self.avant, self.apres)
        self.assertEqual([(c, v) for _, c, v in r["apparues"]],
                         [("item.society.new", "Carte autorisée")])

    def test_une_cle_disparue_est_listee_et_nommee(self):
        r = comparer(self.avant, self.apres)
        self.assertEqual([(c, v) for _, c, v in r["disparues"]],
                         [("item.society.dead", "Jeton mort")])

    def test_une_difference_de_fond_est_isolee_des_accents(self):
        r = comparer(self.avant, self.apres)
        self.assertEqual([c for _, c, _, _ in r["fond"]],
                         ["item.society.couch"])
        # « Ble » → « Blé » dans le fichier de langue, « ragout » → « ragoût »
        # dans le livre Patchouli : deux différences d'accents, pas plus.
        self.assertEqual(r["accents"], 2)
        self.assertEqual(r["illisibles"], [])

    def test_un_fichier_illisible_est_signale_et_non_compte_ailleurs(self):
        r = comparer(self.apres, self.casse)
        self.assertEqual([(e.ref, e.chemin) for e in r["illisibles"]],
                         [(self.casse, self.LANG)])
        # Le fichier est sauté, mais bruyamment : aucune de ses clés ne part
        # grossir `disparues`, où elle aurait passé pour une suppression.
        self.assertEqual(r["disparues"], [])
        self.assertEqual(r["fond"], [])

    def test_aucune_difference_quand_les_refs_sont_les_memes(self):
        r = comparer(self.apres, self.apres)
        self.assertEqual(
            (r["accents"], r["fond"], r["apparues"], r["disparues"],
             r["illisibles"]), (0, [], [], [], []))


if __name__ == "__main__":
    unittest.main()
