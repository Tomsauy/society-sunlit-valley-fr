"""L'installeur Windows (installer.ps1), passé sur les mêmes cas qu'install_fr.py.

Il tourne sous PowerShell : les tests le lancent avec `pwsh` (ou `pwsh-preview`) et
sont sautés si aucun n'est installé (sur macOS : brew install --cask powershell@preview).
PowerShell 7 n'est pas Windows PowerShell 5.1, la version de Windows : le script
s'interdit les tournures propres à la 7, mais un essai sur un vrai Windows reste dû.

Le point qui compte, comme pour install_fr.py : ce qu'une installation précédente a
posé et que la traduction ne porte plus est repris, et la sauvegarde rendue.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import install_fr
from install_fr import RELEVE, lire_releve

SCRIPT = Path(__file__).resolve().parent / "installer.ps1"
PWSH = shutil.which("pwsh") or shutil.which("pwsh-preview")


def poser(racine: Path, chemin: str, contenu: str = "{}") -> Path:
    p = racine / chemin
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(contenu, encoding="utf-8")
    return p


class TestCompatibilite51(unittest.TestCase):
    """Windows PowerShell 5.1 n'est pas testable ici : on s'interdit ce qu'il ne connaît pas."""

    def setUp(self):
        self.brut = SCRIPT.read_bytes()
        self.texte = self.brut.decode("utf-8-sig")

    # Sans BOM, PowerShell 5.1 lit le script en ANSI : « Français » devient illisible.
    def test_le_script_porte_un_bom(self):
        self.assertTrue(self.brut.startswith(b"\xef\xbb\xbf"))

    def test_pas_de_tournure_de_powershell_7(self):
        code = "\n".join(l.split("#")[0] for l in self.texte.splitlines()
                         if not l.lstrip().startswith("#"))
        for motif, nom in (("??", "coalescence nulle"), ("?.", "accès conditionnel"),
                           ("&&", "chaînage"), ("||", "chaînage"), ("-AsHashtable", "ConvertFrom-Json -AsHashtable"),
                           ("-Parallel", "ForEach-Object -Parallel")):
            self.assertNotIn(motif, code, nom)


@unittest.skipUnless(PWSH, "PowerShell absent : installer.ps1 non testé")
class TestInstallerPs1(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        racine = Path(self.tmp.name)
        # Le paquet décompressé, de forme exacte : le script prend ses fichiers à côté de lui.
        self.paquet = racine / "paquet"
        shutil.copy2(SCRIPT, poser(self.paquet, "installer.ps1", ""))
        poser(self.paquet, "version.txt", "4.1.5\n")
        poser(self.paquet, "kubejs/assets/emi/lang/fr_fr.json", '{"a": "A"}')
        poser(self.paquet, "config/fancymenu/assets/changelog_fr_fr.markdown", "# Journal")
        poser(self.paquet, "patchouli_books/guide/fr_fr/page.json", '{"p": 1}')
        poser(self.paquet, "mods/accentfold-1.0.0.jar", "jar")
        self.dest = racine / "instance"
        poser(self.dest, "kubejs/.gardien", "")
        poser(self.dest, "pakku.json", json.dumps({"version": "4.1.5"}))

    def lancer(self, *options) -> subprocess.CompletedProcess:
        r = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File",
                            str(self.paquet / "installer.ps1"), str(self.dest), *options],
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def releve(self) -> dict:
        return json.loads((self.dest / RELEVE).read_text(encoding="utf-8"))

    def test_pose_et_consigne(self):
        self.lancer()
        self.assertEqual((self.dest / "kubejs/assets/emi/lang/fr_fr.json").read_text(encoding="utf-8"), '{"a": "A"}')
        self.assertTrue((self.dest / "patchouli_books/guide/fr_fr/page.json").exists())
        self.assertTrue((self.dest / "config/fancymenu/assets/changelog_fr_fr.markdown").exists())
        self.assertTrue((self.dest / "mods/accentfold-1.0.0.jar").exists())
        r = self.releve()
        self.assertEqual(r["version"], "4.1.5")
        self.assertEqual(sorted(r["pose"]), sorted([
            "config/fancymenu/assets/changelog_fr_fr.markdown",
            "kubejs/assets/emi/lang/fr_fr.json",
            "mods/accentfold-1.0.0.jar",
            "patchouli_books/guide/fr_fr"]))

    # Un BOM empêcherait json.loads de lire le relevé : install_fr.py croirait
    # alors n'avoir rien posé, et ne reprendrait plus rien.
    def test_le_releve_est_lisible_par_install_fr_py(self):
        self.lancer()
        self.assertFalse((self.dest / RELEVE).read_bytes().startswith(b"\xef\xbb\xbf"))
        self.assertIn("kubejs/assets/emi/lang/fr_fr.json", lire_releve(self.dest))

    def test_la_traduction_du_pack_est_sauvegardee_puis_rendue(self):
        poser(self.dest, "kubejs/assets/emixx/lang/fr_fr.json", '{"b": "le pack"}')
        poser(self.paquet, "kubejs/assets/emixx/lang/fr_fr.json", '{"b": "notre pose"}')
        self.lancer()
        self.assertEqual(json.loads((self.dest / "kubejs/assets/emixx/lang/fr_fr.json.bak-fr").read_text()),
                         {"b": "le pack"})
        # Le mod n'est plus traduit par nous : la traduction d'origine revient.
        shutil.rmtree(self.paquet / "kubejs/assets/emixx")
        self.lancer()
        self.assertEqual(json.loads((self.dest / "kubejs/assets/emixx/lang/fr_fr.json").read_text()),
                         {"b": "le pack"})
        self.assertFalse((self.dest / "kubejs/assets/emixx/lang/fr_fr.json.bak-fr").exists())

    def test_un_fichier_abandonne_entre_deux_passages_est_repris(self):
        poser(self.paquet, "kubejs/assets/emixx/lang/fr_fr.json", '{"b": "B"}')
        self.lancer()
        self.assertTrue((self.dest / "kubejs/assets/emixx/lang/fr_fr.json").exists())
        shutil.rmtree(self.paquet / "kubejs/assets/emixx")
        self.lancer()
        self.assertFalse((self.dest / "kubejs/assets/emixx").exists())
        self.assertTrue((self.dest / "kubejs/assets/emi/lang/fr_fr.json").exists())
        self.assertTrue((self.dest / "kubejs").is_dir())

    def test_les_alias_emi_d_une_vieille_instance_sont_repris(self):
        poser(self.dest, "kubejs/assets/emi/aliases/society_fr.json", '{"alias": 1}')
        r = self.lancer()
        self.assertFalse((self.dest / "kubejs/assets/emi/aliases").exists())
        self.assertIn("1 fichier retiré — la traduction ne le porte plus", r.stdout)

    def test_dry_run_n_ecrit_ni_ne_detruit_rien(self):
        residu = poser(self.dest, "kubejs/assets/emi/aliases/society_fr.json", '{"alias": 1}')
        self.lancer("-DryRun")
        self.assertTrue(residu.exists())
        self.assertFalse((self.dest / RELEVE).exists())
        self.assertFalse((self.dest / "kubejs/assets/emi/lang/fr_fr.json").exists())
        self.assertFalse((self.dest / "mods").exists())

    def test_un_livre_existant_est_sauvegarde(self):
        poser(self.dest, "patchouli_books/guide/fr_fr/ancienne.json", '{"v": 0}')
        self.lancer()
        self.assertTrue((self.dest / "patchouli_books/guide/fr_fr.bak-fr/ancienne.json").exists())
        self.assertFalse((self.dest / "patchouli_books/guide/fr_fr/ancienne.json").exists())
        self.assertTrue((self.dest / "patchouli_books/guide/fr_fr/page.json").exists())

    # Deux versions du même mod dans mods/ : Forge refuse de démarrer.
    def test_une_autre_version_d_accent_fold_est_mise_de_cote(self):
        poser(self.dest, "mods/accentfold-0.9.0.jar", "vieux")
        self.lancer()
        self.assertFalse((self.dest / "mods/accentfold-0.9.0.jar").exists())
        self.assertTrue((self.dest / "mods/accentfold-0.9.0.jar.bak-fr").exists())
        self.assertTrue((self.dest / "mods/accentfold-1.0.0.jar").exists())

    def test_une_nouvelle_version_du_mod_remplace_celle_posee(self):
        self.lancer()
        (self.paquet / "mods/accentfold-1.0.0.jar").unlink()
        poser(self.paquet, "mods/accentfold-1.1.0.jar", "jar")
        self.lancer()
        self.assertFalse((self.dest / "mods/accentfold-1.0.0.jar").exists())
        self.assertFalse((self.dest / "mods/accentfold-1.0.0.jar.bak-fr").exists())
        self.assertTrue((self.dest / "mods/accentfold-1.1.0.jar").exists())

    def test_sans_accent_fold(self):
        self.lancer("-SansAccentFold")
        self.assertFalse((self.dest / "mods").exists())
        self.assertNotIn("mods/accentfold-1.0.0.jar", self.releve()["pose"])

    def test_une_version_differente_demande_confirmation(self):
        poser(self.dest, "pakku.json", json.dumps({"version": "4.2.0"}))
        r = subprocess.run([PWSH, "-NoProfile", "-File", str(self.paquet / "installer.ps1"), str(self.dest)],
                           input="n\n", capture_output=True, text=True, timeout=120)
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.dest / RELEVE).exists())
        self.lancer("-Oui")
        self.assertTrue((self.dest / RELEVE).exists())

    # powershell -File "..\minecraft\" -DryRun : Windows lit \" comme un guillemet
    # littéral, et le script reçoit « ..\minecraft" -DryRun » en un seul argument.
    def test_un_chemin_mal_decoupe_par_windows_est_recoupe(self):
        r = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", str(self.paquet / "installer.ps1"),
                            str(self.dest) + '/" -DryRun'], capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("-DryRun", r.stdout)
        self.assertFalse((self.dest / RELEVE).exists())

    def test_un_chemin_termine_par_une_barre_est_accepte(self):
        r = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", str(self.paquet / "installer.ps1"),
                            str(self.dest) + "/"], capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((self.dest / RELEVE).exists())

    def test_un_dossier_sans_kubejs_est_signale(self):
        shutil.rmtree(self.dest / "kubejs")
        r = self.lancer("-DryRun")
        self.assertIn("kubejs", r.stdout)


@unittest.skipUnless(PWSH, "PowerShell absent : installer.ps1 non testé")
class TestInteroperabilite(unittest.TestCase):
    """Les deux installeurs partagent le relevé : l'un reprend ce que l'autre a posé."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        racine = Path(self.tmp.name)
        self.paquet = racine / "paquet"
        shutil.copy2(SCRIPT, poser(self.paquet, "installer.ps1", ""))
        poser(self.paquet, "version.txt", "4.1.5\n")
        poser(self.paquet, "kubejs/assets/emi/lang/fr_fr.json", '{"a": "A"}')
        poser(self.paquet, "config/fancymenu/assets/changelog_fr_fr.markdown", "# Journal")
        poser(self.paquet, "patchouli_books/guide/fr_fr/page.json", '{"p": 1}')
        poser(self.paquet, "mods/accentfold-1.0.0.jar", "jar")
        # La même source, vue par install_fr.py (arbre du pack) et son mod.
        self.pack = racine / "pack"
        poser(self.pack, "pakku.json", json.dumps({"version": "4.1.5"}))
        poser(self.pack, "kubejs/assets/emi/lang/fr_fr.json", '{"a": "A"}')
        poser(self.pack, "config/fancymenu/assets/changelog_fr_fr.markdown", "# Journal")
        poser(self.pack, "patchouli_books/guide/fr_fr/page.json", '{"p": 1}')
        self.jars = racine / "accent-fold/build/libs"
        poser(self.jars, "accentfold-1.0.0.jar", "jar")
        for nom, valeur in (("SRC_REPO", self.pack), ("ACCENT_FOLD", self.jars)):
            avant = getattr(install_fr, nom)
            setattr(install_fr, nom, valeur)
            self.addCleanup(setattr, install_fr, nom, avant)
        self.dest = racine / "instance"
        poser(self.dest, "kubejs/.gardien", "")
        poser(self.dest, "pakku.json", json.dumps({"version": "4.1.5"}))

    def python(self):
        argv = sys.argv
        sys.argv = ["install_fr.py", str(self.dest)]
        try:
            install_fr.main()
        finally:
            sys.argv = argv

    def powershell(self):
        r = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File",
                            str(self.paquet / "installer.ps1"), str(self.dest)],
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_les_deux_poses_ont_le_meme_releve(self):
        self.python()
        pose_py = sorted(lire_releve(self.dest))
        self.powershell()
        self.assertEqual(sorted(lire_releve(self.dest)), pose_py)

    def test_powershell_reprend_ce_que_python_a_pose(self):
        poser(self.pack, "kubejs/assets/emixx/lang/fr_fr.json", '{"b": "B"}')
        self.python()
        self.assertTrue((self.dest / "kubejs/assets/emixx/lang/fr_fr.json").exists())
        self.powershell()   # le paquet ne porte pas emixx
        self.assertFalse((self.dest / "kubejs/assets/emixx").exists())
        self.assertTrue((self.dest / "mods/accentfold-1.0.0.jar").exists())

    def test_python_reprend_ce_que_powershell_a_pose_sans_toucher_au_mod(self):
        poser(self.paquet, "kubejs/assets/emixx/lang/fr_fr.json", '{"b": "B"}')
        self.powershell()
        self.python()       # le pack ne porte pas emixx
        self.assertFalse((self.dest / "kubejs/assets/emixx").exists())
        self.assertTrue((self.dest / "mods/accentfold-1.0.0.jar").exists())


if __name__ == "__main__":
    unittest.main()
