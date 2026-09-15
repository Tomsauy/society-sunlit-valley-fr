"""L'installateur, et surtout ce qu'il reprend.

Le défaut corrigé ici est qu'il copiait sans jamais effacer : une instance gardait
indéfiniment un fichier que la traduction avait cessé de porter, et le jeu
continuait de le lire. Les alias de recherche EMI y ont survécu à leur suppression.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import install_fr
from install_fr import RELEVE, a_retirer, lire_releve, retirer


def poser(racine: Path, chemin: str, contenu: str = "{}") -> Path:
    p = racine / chemin
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(contenu, encoding="utf-8")
    return p


class BaseInstance(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dest = Path(self.tmp.name) / "instance"
        self.dest.mkdir()

    def releve(self, *chemins):
        (self.dest / RELEVE).write_text(
            json.dumps({"version": "4.1.5", "pose": list(chemins)}), encoding="utf-8")


class TestLireReleve(BaseInstance):

    def test_absent_ne_fait_rien_retirer(self):
        self.assertEqual(lire_releve(self.dest), [])

    def test_illisible_ne_fait_rien_retirer(self):
        (self.dest / RELEVE).write_text("{ pas du json", encoding="utf-8")
        self.assertEqual(lire_releve(self.dest), [])


class TestARetirer(BaseInstance):

    def test_ce_qui_n_est_plus_pose_s_en_va(self):
        poser(self.dest, "kubejs/assets/emixx/lang/fr_fr.json")
        poser(self.dest, "kubejs/assets/emi/lang/fr_fr.json")
        self.releve("kubejs/assets/emixx/lang/fr_fr.json",
                    "kubejs/assets/emi/lang/fr_fr.json")
        self.assertEqual(a_retirer(self.dest, ["kubejs/assets/emi/lang/fr_fr.json"]),
                         ["kubejs/assets/emixx/lang/fr_fr.json"])

    def test_ce_qui_reste_pose_ne_bouge_pas(self):
        poser(self.dest, "kubejs/assets/emi/lang/fr_fr.json")
        self.releve("kubejs/assets/emi/lang/fr_fr.json")
        self.assertEqual(a_retirer(self.dest, ["kubejs/assets/emi/lang/fr_fr.json"]), [])

    def test_une_entree_du_releve_deja_absente_du_disque_est_ignoree(self):
        self.releve("kubejs/assets/parti/lang/fr_fr.json")
        self.assertEqual(a_retirer(self.dest, []), [])

    # Les instances installées avant le relevé n'ont aucune trace de ce que le
    # script y a posé : les résidus connus sont le seul moyen de les rattraper.
    def test_les_alias_emi_partent_meme_sans_releve(self):
        poser(self.dest, "kubejs/assets/emi/aliases/society_fr.json")
        self.assertEqual(a_retirer(self.dest, []),
                         ["kubejs/assets/emi/aliases/society_fr.json"])

    def test_un_residu_absent_n_est_pas_signale(self):
        self.assertEqual(a_retirer(self.dest, []), [])

    def test_un_residu_deja_dans_le_releve_n_est_compte_qu_une_fois(self):
        poser(self.dest, "kubejs/assets/emi/aliases/society_fr.json")
        self.releve("kubejs/assets/emi/aliases/society_fr.json")
        self.assertEqual(a_retirer(self.dest, []),
                         ["kubejs/assets/emi/aliases/society_fr.json"])


class TestRetirer(BaseInstance):

    def test_sans_sauvegarde_le_fichier_s_en_va(self):
        c = poser(self.dest, "kubejs/assets/emixx/lang/fr_fr.json")
        retirer(c, self.dest)
        self.assertFalse(c.exists())

    def test_la_sauvegarde_reprend_sa_place(self):
        c = poser(self.dest, "kubejs/assets/emi/lang/fr_fr.json", '{"a": "notre pose"}')
        poser(self.dest, "kubejs/assets/emi/lang/fr_fr.json.bak-fr", '{"a": "le pack"}')
        retirer(c, self.dest)
        self.assertEqual(json.loads(c.read_text()), {"a": "le pack"})
        self.assertFalse(c.with_suffix(".json.bak-fr").exists())

    def test_les_dossiers_vides_sont_repris(self):
        poser(self.dest, "kubejs/assets/emi/lang/fr_fr.json")
        c = poser(self.dest, "kubejs/assets/emixx/lang/fr_fr.json")
        retirer(c, self.dest)
        self.assertFalse((self.dest / "kubejs/assets/emixx").exists())
        self.assertTrue((self.dest / "kubejs/assets/emi/lang").is_dir())

    # kubejs/, config/ et patchouli_books/ appartiennent à l'instance, pas à la
    # traduction : les vider ne donne pas le droit de les retirer.
    def test_les_dossiers_structurels_de_l_instance_survivent(self):
        c = poser(self.dest, "kubejs/assets/emixx/lang/fr_fr.json")
        retirer(c, self.dest)
        self.assertTrue((self.dest / "kubejs").is_dir())
        self.assertFalse((self.dest / "kubejs/assets").exists())

    def test_un_dossier_encore_habite_reste(self):
        poser(self.dest, "kubejs/assets/emi/lang/en_us.json")
        c = poser(self.dest, "kubejs/assets/emi/lang/fr_fr.json")
        retirer(c, self.dest)
        self.assertTrue((self.dest / "kubejs/assets/emi/lang").is_dir())

    # Le nettoyage des dossiers vides remonte ; il ne doit jamais dépasser
    # l'instance, sous peine d'emporter le dossier du launcher.
    def test_le_nettoyage_s_arrete_a_l_instance(self):
        c = poser(self.dest, "seul.json")
        retirer(c, self.dest)
        self.assertTrue(self.dest.is_dir())
        self.assertTrue(self.dest.parent.is_dir())

    def test_un_dossier_pose_s_en_va_entier(self):
        poser(self.dest, "patchouli_books/guide/fr_fr/page.json")
        retirer(self.dest / "patchouli_books/guide/fr_fr", self.dest)
        self.assertFalse((self.dest / "patchouli_books/guide/fr_fr").exists())


class TestMain(BaseInstance):
    """Un passage complet, sur une source réduite mais de forme exacte."""

    def setUp(self):
        super().setUp()
        self.src = Path(self.tmp.name) / "pack"
        poser(self.src, "pakku.json", json.dumps({"version": "4.1.5"}))
        poser(self.src, "kubejs/assets/emi/lang/fr_fr.json", '{"a": "A"}')
        poser(self.src, "config/fancymenu/assets/changelog_fr_fr.markdown", "# Journal")
        poser(self.src, "patchouli_books/guide/fr_fr/page.json", '{"p": 1}')
        self._src_avant = install_fr.SRC_REPO
        install_fr.SRC_REPO = self.src
        self.addCleanup(lambda: setattr(install_fr, "SRC_REPO", self._src_avant))
        poser(self.dest, "kubejs/.gardien", "")
        poser(self.dest, "pakku.json", json.dumps({"version": "4.1.5"}))

    def lancer(self, *options):
        argv = sys.argv
        sys.argv = ["install_fr.py", str(self.dest), *options]
        try:
            install_fr.main()
        finally:
            sys.argv = argv

    def test_pose_et_consigne(self):
        self.lancer()
        self.assertTrue((self.dest / "kubejs/assets/emi/lang/fr_fr.json").exists())
        self.assertTrue((self.dest / "patchouli_books/guide/fr_fr/page.json").exists())
        releve = json.loads((self.dest / RELEVE).read_text(encoding="utf-8"))
        self.assertEqual(releve["version"], "4.1.5")
        self.assertEqual(releve["pose"], sorted([
            "config/fancymenu/assets/changelog_fr_fr.markdown",
            "kubejs/assets/emi/lang/fr_fr.json",
            "patchouli_books/guide/fr_fr"]))

    def test_un_fichier_abandonne_entre_deux_passages_est_repris(self):
        poser(self.src, "kubejs/assets/emixx/lang/fr_fr.json", '{"b": "B"}')
        self.lancer()
        self.assertTrue((self.dest / "kubejs/assets/emixx/lang/fr_fr.json").exists())

        # Le mod sort du pack : sa traduction n'est plus portée.
        (self.src / "kubejs/assets/emixx/lang/fr_fr.json").unlink()
        self.lancer()
        self.assertFalse((self.dest / "kubejs/assets/emixx").exists())
        self.assertTrue((self.dest / "kubejs/assets/emi/lang/fr_fr.json").exists())

    def test_les_alias_emi_d_une_vieille_instance_sont_repris(self):
        poser(self.dest, "kubejs/assets/emi/aliases/society_fr.json", '{"alias": 1}')
        self.lancer()
        self.assertFalse((self.dest / "kubejs/assets/emi/aliases").exists())

    def test_dry_run_n_ecrit_ni_ne_detruit_rien(self):
        residu = poser(self.dest, "kubejs/assets/emi/aliases/society_fr.json", '{"alias": 1}')
        self.lancer("--dry-run")
        self.assertTrue(residu.exists())
        self.assertFalse((self.dest / RELEVE).exists())
        self.assertFalse((self.dest / "kubejs/assets/emi/lang/fr_fr.json").exists())


if __name__ == "__main__":
    unittest.main()
