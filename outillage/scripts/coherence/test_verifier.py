"""La ligne de commande du vérificateur."""
import contextlib
import io
import json
import unittest

import verifier
from coherence.fabrique import ESPACE, PACK, donnees_vides, ecrire, pack_et_espace
from coherence.rapport import empreinte
from coherence.test_instantane import copier_le_francais


def lancer(*args):
    sortie, erreurs = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(erreurs):
        code = verifier.main([str(a) for a in args])
    return code, sortie.getvalue(), erreurs.getvalue()


class TestLigneDeCommande(unittest.TestCase):

    def setUp(self):
        self.dossier, self.pack, self.espace = pack_et_espace(PACK, ESPACE)
        self.addCleanup(self.dossier.cleanup)
        ecrire(self.espace, {"provenance.json": {"cles": {"item.society.bac": [{"type": "relecture", "fr": "x"}]},
                                                 "glossaire": {"bin": {}}}})

    # Les contrôles s'ajoutent tâche après tâche : les tests qui attendent un code 0 n'en lancent
    # qu'un, le mécanisme testé ici étant la ligne de commande, pas les contrôles.
    def test_rapport_texte(self):
        code, sortie, _ = lancer("--racine", self.pack, "--espace", self.espace, "--controle", "homonymes")
        self.assertEqual(code, 0)
        self.assertIn("1 clés tracées, 1 décisions, 1 termes au glossaire", sortie)

    def test_rapport_json(self):
        code, sortie, _ = lancer("--racine", self.pack, "--espace", self.espace, "--json")
        rapport = json.loads(sortie)
        self.assertEqual(sorted(rapport), ["bloquants", "code", "compteurs", "couverts", "dette_resolue", "durees",
                                           "en_dette", "orphelines", "provisoires", "renvois_orphelins", "renvoyees",
                                           "sans_motif", "signales", "version"])
        self.assertEqual((rapport["code"], code, rapport["version"]), (1, 1, "4.1.5"))
        self.assertEqual(rapport["compteurs"], {"cles_tracees": 1, "decisions": 1, "termes_glossaire": 1})
        # le témoin coréen sans français bloque ; le canapé défini deux fois est signalé
        self.assertIn(("couverture", "item.society.oubliee"), [(c["controle"], c["cle"]) for c in rapport["bloquants"]])
        self.assertIn(("couverture", "block.furniture.sofa"), [(c["controle"], c["cle"]) for c in rapport["signales"]])
        self.assertEqual(set(rapport["bloquants"][0]), {"controle", "cle", "statut", "actuel", "attendu", "detail",
                                                        "preuve", "objet"})
        self.assertIn("corpus", rapport["durees"])

    def test_fork_sans_instantane(self):
        # Point de vigilance 4 : message clair et code 2, pas de trace de pile. L'espace du fork (outillage/) a ses
        # données, pas les jars extraits.
        fork = self.pack.parent / "fork"
        copier_le_francais(self.pack, fork)
        outillage = ecrire(fork / "outillage", {c: v for c, v in donnees_vides().items() if not c.startswith("references/")})
        code, _, erreurs = lancer("--racine", fork, "--espace", outillage)
        self.assertEqual(code, 2)
        self.assertIn("--instantane", erreurs)
        self.assertNotIn("Traceback", erreurs)

    def test_fichier_de_donnees_absent(self):
        """I1 : un fichier de données absent arrête le vérificateur (code 2) en le nommant, au lieu de vider son
        contrôle sans bruit."""
        (self.espace / "coherence" / "formes_interdites.json").unlink()
        code, sortie, erreurs = lancer("--racine", self.pack, "--espace", self.espace)
        self.assertEqual((code, sortie), (2, ""))
        self.assertIn("formes_interdites.json introuvable", erreurs)
        self.assertNotIn("Traceback", erreurs)

    def test_fork_avec_instantane(self):
        chemin = self.pack.parent / "instantane.json.gz"
        self.assertEqual(lancer("--racine", self.pack, "--espace", self.espace, "--ecrire-instantane", chemin)[0], 0)
        fork = self.pack.parent / "fork"
        copier_le_francais(self.pack, fork)
        code_clone, attendu, _ = lancer("--racine", self.pack, "--espace", self.espace, "--json")
        code, obtenu, _ = lancer("--racine", fork, "--espace", self.espace, "--instantane", chemin, "--json")
        self.assertEqual(code, code_clone)
        retirer_durees = lambda s: {k: v for k, v in json.loads(s).items() if k != "durees"}
        self.assertEqual(retirer_durees(obtenu), retirer_durees(attendu))

    def test_instantane_refuse_sans_hashs_amont(self):
        """M3 : hors d'un clone git, les hashs amont manquent ; si des scripts sont patchés, l'instantané qui les
        omettrait n'est pas écrit (code 2) ; sans script patché, il l'est."""
        chemin = self.pack.parent / "instantane.json.gz"
        ecrire(self.espace, {"coherence/scripts_patches.json": {"kubejs/a.js": {"base": "1" * 40, "motif": "m"}}})
        code, _, erreurs = lancer("--racine", self.pack, "--espace", self.espace, "--ecrire-instantane", chemin)
        self.assertEqual(code, 2)
        self.assertIn("hashs amont", erreurs)
        self.assertFalse(chemin.exists())
        ecrire(self.espace, {"coherence/scripts_patches.json": {}})
        self.assertEqual(lancer("--racine", self.pack, "--espace", self.espace, "--ecrire-instantane", chemin)[0], 0)
        self.assertTrue(chemin.exists())

    def test_donnees_de_mauvaise_forme(self):
        """M2 : code 2 et le fichier nommé, pas de trace de pile."""
        ecrire(self.espace, {"coherence/dette.json": ["x"]})
        code, _, erreurs = lancer("--racine", self.pack, "--espace", self.espace)
        self.assertEqual(code, 2)
        self.assertIn("dette.json", erreurs)
        self.assertNotIn("Traceback", erreurs)

    def test_dette_retirer_resolus(self):
        ecrire(self.espace, {"coherence/dette.json": [{"controle": "homonymes", "cle": "x", "empreinte": "0"}]})
        code, sortie, _ = lancer("--racine", self.pack, "--espace", self.espace, "--controle", "homonymes",
                                 "--dette-retirer-resolus")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads((self.espace / "coherence" / "dette.json").read_text(encoding="utf-8")), [])
        self.assertIn("1 entrée(s) retirée(s)", sortie)
        self.assertIn("  [homonymes] x", sortie)  # chaque entrée retirée est nommée

    def test_dette_retirer_resolus_garde_ce_qui_reste(self):
        """M7 : l'entrée qui couvre encore un constat (le témoin coréen sans français) reste ; seule la résolue part."""
        reste = {"controle": "couverture", "cle": "item.society.oubliee", "empreinte": empreinte("")}
        ecrire(self.espace, {"coherence/dette.json": [reste, {"controle": "couverture", "cle": "x", "empreinte": "0"}]})
        code, sortie, _ = lancer("--racine", self.pack, "--espace", self.espace, "--controle", "couverture",
                                 "--dette-retirer-resolus")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads((self.espace / "coherence" / "dette.json").read_text(encoding="utf-8")), [reste])
        self.assertIn("1 entrée(s) retirée(s) de dette.json\n  [couverture] x\n", sortie)
        self.assertIn("1 en dette", sortie)

    def test_dette_a_retirer_nommee(self):
        ecrire(self.espace, {"coherence/dette.json": [{"controle": "homonymes", "cle": "x", "empreinte": "0"}]})
        code, sortie, _ = lancer("--racine", self.pack, "--espace", self.espace, "--controle", "homonymes")
        self.assertEqual(code, 0)
        self.assertIn("DETTE RÉSOLUE (1) — à retirer avec --dette-retirer-resolus\n  [homonymes] x\n", sortie)

    def test_dette_retirer_resolus_refuse_sur_un_echec(self):
        """I1 : un passage en échec (ici le témoin coréen sans français) ne purge pas la dette : ce qui semble résolu
        peut venir d'un contrôle vidé."""
        dette = [{"controle": "codes", "cle": "x", "empreinte": "0"}]
        ecrire(self.espace, {"coherence/dette.json": dette})
        code, sortie, erreurs = lancer("--racine", self.pack, "--espace", self.espace, "--controle", "couverture",
                                       "--controle", "codes", "--dette-retirer-resolus")
        self.assertEqual(code, 1)
        self.assertIn("--dette-retirer-resolus refusé", erreurs)
        self.assertEqual(json.loads((self.espace / "coherence" / "dette.json").read_text(encoding="utf-8")), dette)
        self.assertNotIn("retirée(s)", sortie)

    def test_dette_base(self):
        """La dette ne fait que décroître (spec §10) : --dette-base échoue si dette.json contient une entrée (contrôle,
        clé, objet) absente de la dette de référence — la garde de l'Action du fork. Une dette qui décroît passe."""
        a = {"controle": "homonymes", "cle": "a", "objet": ["a", "b"], "empreinte": "0"}
        b = {"controle": "homonymes", "cle": "b", "empreinte": "0"}
        base = self.pack.parent / "base.json"
        ecrire(self.pack.parent, {"base.json": [a, b]})
        cas = (([a, b], 0, None), ([a], 0, None),
               ([a, b, {"controle": "codes", "cle": "c", "empreinte": "1"}], 1, "[codes] c"),
               ([dict(a, objet=["a", "b", "c"])], 1, "[homonymes] a (a, b, c)"))
        for dette, code_attendu, nommee in cas:
            with self.subTest(dette=dette):
                ecrire(self.espace, {"coherence/dette.json": dette})
                code, sortie, _ = lancer("--racine", self.pack, "--espace", self.espace, "--controle", "homonymes",
                                         "--dette-base", base)
                self.assertEqual(code, code_attendu)
                if nommee:
                    self.assertIn(f"DETTE EN HAUSSE (1) — absente de {base}", sortie)
                    self.assertIn(f"  {nommee}\n", sortie)
                else:
                    self.assertNotIn("EN HAUSSE", sortie)
        code, _, erreurs = lancer("--racine", self.pack, "--espace", self.espace, "--dette-base", self.pack.parent / "nulle")
        self.assertEqual(code, 2)
        self.assertIn("nulle", erreurs)

    def test_dette_base_en_json(self):
        ecrire(self.pack.parent, {"base.json": []})
        ecrire(self.espace, {"coherence/dette.json": [{"controle": "codes", "cle": "c", "empreinte": "1"}]})
        code, sortie, _ = lancer("--racine", self.pack, "--espace", self.espace, "--controle", "homonymes", "--json",
                                 "--dette-base", self.pack.parent / "base.json")
        rapport = json.loads(sortie)
        self.assertEqual((code, rapport["code"]), (1, 1))
        self.assertEqual(rapport["dette_en_hausse"], [{"controle": "codes", "cle": "c", "empreinte": "1"}])

    def test_dette_base_empreinte_modifiee(self):
        """Résidu 2 (spec §10) : qui touche une clé la corrige — réécrire l'empreinte à la main sans corriger le
        défaut doit échouer --dette-base, même triplet (contrôle, clé, objet). Une entrée retirée reste permise."""
        a = {"controle": "homonymes", "cle": "a", "objet": ["a", "b"], "empreinte": "0"}
        b = {"controle": "homonymes", "cle": "b", "empreinte": "0"}
        base = self.pack.parent / "base.json"
        ecrire(self.pack.parent, {"base.json": [a, b]})
        cas = (([a, b], 0, None),  # empreintes inchangées
               ([a], 0, None),  # b retirée : reste permis
               ([dict(a, empreinte="1"), b], 1, "[homonymes] a (a, b)"))
        for dette, code_attendu, nommee in cas:
            with self.subTest(dette=dette):
                ecrire(self.espace, {"coherence/dette.json": dette})
                code, sortie, _ = lancer("--racine", self.pack, "--espace", self.espace, "--controle", "homonymes",
                                         "--dette-base", base)
                self.assertEqual(code, code_attendu)
                if nommee:
                    self.assertIn(f"DETTE MODIFIÉE (1) — empreinte différente de {base}", sortie)
                    self.assertIn(f"  {nommee}\n", sortie)
                else:
                    self.assertNotIn("MODIFIÉE", sortie)

    def test_dette_base_empreinte_modifiee_en_json(self):
        a = {"controle": "codes", "cle": "c", "empreinte": "1"}
        ecrire(self.pack.parent, {"base.json": [a]})
        ecrire(self.espace, {"coherence/dette.json": [dict(a, empreinte="2")]})
        code, sortie, _ = lancer("--racine", self.pack, "--espace", self.espace, "--controle", "homonymes", "--json",
                                 "--dette-base", self.pack.parent / "base.json")
        rapport = json.loads(sortie)
        self.assertEqual((code, rapport["code"]), (1, 1))
        self.assertEqual(rapport["dette_modifiee"], [{"controle": "codes", "cle": "c", "empreinte": "2"}])

    def test_controle_inconnu(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            verifier.main(["--controle", "nexistepas"])

    def test_cloture(self):
        # homonymes seul : aucun constat sur le petit pack ; la clôture ne tient qu'aux données
        code, sortie, _ = lancer("--racine", self.pack, "--espace", self.espace, "--controle", "homonymes", "--cloture")
        self.assertEqual(code, 0, sortie)
        ecrire(self.espace, {"coherence/exceptions.json": [
            {"controle": "homonymes", "cle": "x", "motif": "en attente", "question": "porte-orange"}]})
        code, sortie, _ = lancer("--racine", self.pack, "--espace", self.espace, "--controle", "homonymes", "--cloture")
        self.assertEqual(code, 1)
        self.assertIn("provisoire", sortie)
        code, sortie, _ = lancer("--racine", self.pack, "--espace", self.espace, "--controle", "homonymes",
                                 "--cloture", "--json")
        self.assertEqual(json.loads(sortie)["cloture"][0], "1 exception(s) provisoire(s) : des questions attendent leur réponse")

    def test_analyser_avec_une_regle_activee(self):
        fr = dict(PACK["kubejs/assets/society/lang/fr_fr.json"], **{"tooltip.society.x": "Remplis ton Bac d'expédition"})
        ecrire(self.pack, {"kubejs/assets/society/lang/fr_fr.json": fr})
        cles = lambda r: {c.cle for c in r.bloquants}  # noqa: E731
        _, _, sans, _ = verifier.analyser(self.pack, self.espace, controles=["casse"])
        _, _, avec, _ = verifier.analyser(self.pack, self.espace, controles=["casse"], regles={"casse_textes": True})
        self.assertNotIn("tooltip.society.x", cles(sans))
        self.assertIn("tooltip.society.x", cles(avec))


class TestGardeFou(unittest.TestCase):

    def test_refus_puis_accord(self):
        dossier, pack, espace = pack_et_espace(PACK, ESPACE)
        self.addCleanup(dossier.cleanup)
        with contextlib.redirect_stderr(io.StringIO()) as erreurs:
            self.assertFalse(verifier.garde_fou(pack, espace))   # témoin coréen sans français
        self.assertIn("construction refusée", erreurs.getvalue())
        propre = {"pakku.json": {"version": "4.1.5"},
                  "kubejs/assets/society/lang/en_us.json": {"item.society.bac": "Shipping Bin"},
                  "kubejs/assets/society/lang/fr_fr.json": {"item.society.bac": "Bac d'expédition"}}
        dossier2, pack2, espace2 = pack_et_espace(propre, {})
        self.addCleanup(dossier2.cleanup)
        self.assertTrue(verifier.garde_fou(pack2, espace2))


if __name__ == "__main__":
    unittest.main()
