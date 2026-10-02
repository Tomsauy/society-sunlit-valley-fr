"""L'applicateur : chaque destination, chaque refus, le diff minimal, la trace, l'idempotence (spec 2 §8)."""
import contextlib
import io
import json
import unittest

import appliquer_lot
from coherence import config as config_mod
from coherence import corpus as corpus_mod
from coherence.fabrique import ESPACE, PACK_COMPLET, ecrire, pack_et_espace
from coherence.rapport import empreinte
from corrections.applicateur import ecrire as ecrire_plan
from corrections.applicateur import planifier
from corrections.lot import valider_lot

LANGUE_SOCIETY = "kubejs/assets/society/lang/fr_fr.json"
LANGUE_FURNITURE = "kubejs/assets/furniture/lang/fr_fr.json"
CHEVRE = "patchouli_books/almanac/fr_fr/entries/animals/goat.json"
JOURNAL_FR = "config/fancymenu/assets/changelog_fr_fr.markdown"


class TestApplicateur(unittest.TestCase):

    def setUp(self):
        self.dossier, self.pack, self.espace = pack_et_espace(PACK_COMPLET, {
            **ESPACE,
            "extracted/aquaculture-2.5/aquaculture/en_us.json": {"item.aquaculture.hook": "Hook"},
            "extracted/aquaculture-2.5/aquaculture/fr_fr.json": {"item.aquaculture.hook": "Hamecon"},
        })
        self.addCleanup(self.dossier.cleanup)
        # Dans le pack, les fichiers de langue sont triés et indentés à 2, les livres indentés à 4 : les fixtures aussi.
        for chemin in self.pack.glob("kubejs/assets/*/lang/*.json"):
            donnees = json.loads(chemin.read_text(encoding="utf-8"))
            chemin.write_text(json.dumps(donnees, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        for chemin in self.pack.glob("patchouli_books/*/*/**/*.json"):
            donnees = json.loads(chemin.read_text(encoding="utf-8"))
            chemin.write_text(json.dumps(donnees, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")

    def lot(self, actions, perimetre=None):
        cles = sorted({a["cle"] for a in actions if "cle" in a})
        lot = {"lot": "t-01", "nature": "references", "perimetre": cles if perimetre is None else perimetre,
               "actions": actions}
        valider_lot(lot)
        return lot

    def planifier(self, actions, perimetre=None):
        corpus = corpus_mod.charger(self.pack, self.espace)
        config = config_mod.charger_config(self.espace)
        return planifier(self.lot(actions, perimetre), corpus, config, self.pack, self.espace, jour="2026-10-01")

    def appliquer(self, actions, perimetre=None):
        plan = self.planifier(actions, perimetre)
        self.assertEqual(plan.refus, [])
        ecrire_plan(plan, self.pack, self.espace)
        return plan

    def lire(self, fichier):
        return (self.pack / fichier).read_text(encoding="utf-8")

    def provenance(self, cle):
        return json.loads((self.espace / "provenance.json").read_text(encoding="utf-8"))["cles"].get(cle, [])

    @staticmethod
    def corriger(cle, avant, apres, **champs):
        return {"type": "correction", "cle": cle, "avant": avant, "apres": apres, "motif": "essai", **champs}

    def test_correction_d_un_texte_du_projet(self):
        avant = self.lire(LANGUE_SOCIETY).splitlines()
        self.appliquer([self.corriger("item.society.bac", "Bac d'expédition", "Bac d'expédition neuf", question="q1")])
        apres = self.lire(LANGUE_SOCIETY).splitlines()
        self.assertEqual(len(apres), len(avant))
        self.assertEqual([l for l in apres if l not in avant], ['  "item.society.bac": "Bac d\'expédition neuf",'])
        self.assertEqual(self.provenance("item.society.bac"), [
            {"type": "correction", "lot": "t-01", "fr": "Bac d'expédition neuf", "raison": "essai",
             "date": "2026-10-01", "question": "q1"}])

    def test_cle_definie_deux_fois(self):
        # Point de vigilance 2 : furniture dit « Sofa », society « Canapé », qui s'affiche (chargé après).
        self.appliquer([self.corriger("block.furniture.sofa", "Canapé", "Canapé moelleux")])
        for fichier in (LANGUE_SOCIETY, LANGUE_FURNITURE):
            self.assertEqual(json.loads(self.lire(fichier))["block.furniture.sofa"], "Canapé moelleux", fichier)

    def test_cle_definie_deux_fois_texte_affiche_deja_bon(self):
        # Le texte affiché (« Canapé », society) est le bon : la correction aligne l'autre définition, puis se rejoue à vide.
        self.appliquer([self.corriger("block.furniture.sofa", "Canapé", "Canapé")])
        self.assertEqual(json.loads(self.lire(LANGUE_FURNITURE))["block.furniture.sofa"], "Canapé")
        self.assertEqual(self.appliquer([self.corriger("block.furniture.sofa", "Canapé", "Canapé")]).deja, [0])

    def test_champ_de_livre(self):
        cle = "almanac/entries/animals/goat.json#/pages/0/text"
        nouveau = "Les chèvres donnent du $(item)lait$() frais."
        self.appliquer([self.corriger(cle, "Les chèvres donnent du $(item)lait$().", nouveau)])
        self.assertEqual(json.loads(self.lire(CHEVRE))["pages"][0]["text"], nouveau)
        self.assertTrue(self.lire(CHEVRE).startswith('{\n    "name"'))  # indentation 4 gardée

    def test_journal(self):
        avant = self.lire(JOURNAL_FR)
        apres = avant.replace("Ajout d'une chose", "Ajout d'un objet")
        self.appliquer([self.corriger("journal", avant, apres)])
        self.assertEqual(self.lire(JOURNAL_FR), apres)

    def test_surcharge_d_une_traduction_officielle(self):
        self.appliquer([self.corriger("block.furniture.table", "Table", "Table basse")])
        self.assertEqual(json.loads(self.lire(LANGUE_FURNITURE))["block.furniture.table"], "Table basse")

    def test_surcharge_cree_le_fichier_du_mod(self):
        self.appliquer([self.corriger("item.aquaculture.hook", "Hamecon", "Hameçon")])
        self.assertEqual(json.loads(self.lire("kubejs/assets/aquaculture/lang/fr_fr.json")),
                         {"item.aquaculture.hook": "Hameçon"})

    def test_mojang_refuse(self):
        plan = self.planifier([self.corriger("block.minecraft.stone", "Roche", "Pierre")])
        self.assertIn("Mojang", plan.refus[0][1])

    def test_hors_perimetre_refuse(self):
        plan = self.planifier([self.corriger("item.society.bac", "Bac d'expédition", "Bac")], perimetre=["autre.cle"])
        self.assertIn("hors du périmètre", plan.refus[0][1])

    def test_texte_change_refuse(self):
        plan = self.planifier([self.corriger("item.society.bac", "Ancien texte", "Bac")])
        self.assertIn("a changé", plan.refus[0][1])

    def test_deux_corrections_de_la_meme_cle_refusees(self):
        plan = self.planifier([self.corriger("item.society.bac", "Bac d'expédition", "Bac"),
                               self.corriger("item.society.bac", "Bac d'expédition", "Caisse")])
        self.assertIn("deux corrections", plan.refus[0][1])

    def test_cle_absente_avec_espace(self):
        self.appliquer([self.corriger("wood_type.everycomp.x", None, "Érable rouge", espace="everycomp")])
        self.assertEqual(json.loads(self.lire("kubejs/assets/everycomp/lang/fr_fr.json")),
                         {"wood_type.everycomp.x": "Érable rouge"})

    def test_exception_sans_objet_prend_l_empreinte_du_texte_final(self):
        self.appliquer([self.corriger("item.society.bac", "Bac d'expédition", "Bac d'expédition neuf"),
                        {"type": "exception", "controle": "casse", "cle": "item.society.bac", "motif": "voulu"}])
        (exc,) = config_mod.charger_config(self.espace).exceptions
        self.assertEqual(exc["empreinte"], empreinte("Bac d'expédition neuf"))

    def test_exception_remplacee_puis_retiree(self):
        ecrire(self.espace, {"coherence/exceptions.json": [
            {"controle": "casse", "cle": "item.society.bac", "motif": "ancien", "date": "2026-09-29"}]})
        self.appliquer([{"type": "exception", "controle": "casse", "cle": "item.society.bac", "motif": "nouveau",
                         "question": "q2"}])
        (exc,) = config_mod.charger_config(self.espace).exceptions
        self.assertEqual((exc["motif"], exc["question"]), ("nouveau", "q2"))
        self.appliquer([{"type": "retrait", "controle": "casse", "cle": "item.society.bac", "motif": "q2 tranchée"}])
        self.assertEqual(config_mod.charger_config(self.espace).exceptions, [])

    def test_retrait_sans_effet_refuse(self):
        # Un retrait qui ne retire rien n'est pas « déjà appliqué » : cible absente, ou exception épinglée.
        retrait = {"type": "retrait", "controle": "casse", "cle": "item.society.bac", "motif": "tranchée"}
        plan = self.planifier([retrait])
        self.assertEqual(plan.deja, [])
        self.assertEqual(len(plan.refus), 1)
        self.assertIn("aucune exception", plan.refus[0][1])
        ecrire(self.espace, {"coherence/exceptions.json": [
            {"controle": "casse", "cle": "item.society.bac", "motif": "voulu", "epingle": True,
             "date": "2026-09-29"}]})
        plan = self.planifier([retrait])
        self.assertEqual((plan.deja, plan.retraits, len(plan.refus)), ([], [], 1))
        self.assertIn("épinglée", plan.refus[0][1])

    def test_mot_generique_et_renvoi(self):
        self.appliquer([{"type": "mot_generique", "mot": "Cherry", "motif": "matière"},
                        {"type": "renvoi", "controle": "references", "cle": "item.society.bac", "motif": "sens"}],
                       perimetre=["item.society.bac"])
        config = config_mod.charger_config(self.espace)
        self.assertEqual(config.mots_generiques, {"Cherry": "matière"})
        self.assertEqual(config.renvois, [{"controle": "references", "cle": "item.society.bac", "motif": "sens"}])

    def test_trace(self):
        bonne = {"type": "trace", "cle": "item.society.bac", "fr": "Bac d'expédition", "motif": "vérifié dans le jar"}
        self.appliquer([bonne])
        self.assertEqual(self.provenance("item.society.bac")[-1]["type"], "decision")
        plan = self.planifier([dict(bonne, fr="Autre texte")])
        self.assertIn("tel qu'il sera", plan.refus[0][1])

    def test_idempotence(self):
        actions = [self.corriger("item.society.bac", "Bac d'expédition", "Bac d'expédition neuf"),
                   {"type": "exception", "controle": "casse", "cle": "item.society.cle_rouge", "motif": "voulu"}]
        self.appliquer(actions)
        avant = {p: p.read_bytes() for p in list(self.pack.rglob("*.json")) + list(self.espace.rglob("*.json"))}
        plan = self.appliquer(actions)
        self.assertEqual(len(plan.deja), 2)
        self.assertEqual({p: p.read_bytes() for p in avant}, avant)

    def test_rejouer_apres_un_autre_changement(self):
        # Point de vigilance 3
        actions = [self.corriger("item.society.bac", "Bac d'expédition", "Bac d'expédition neuf")]
        self.appliquer(actions)
        self.appliquer([self.corriger("item.society.cle_rouge", "Clé rouge", "Clé écarlate")])
        self.assertEqual(self.appliquer(actions).deja, [0])

    def test_valeurs_avec_echappements(self):
        # Point de vigilance 1
        valeur = 'Dit "bonjour" \\ puis\nà %1$s : 25 % ✨'
        self.appliquer([self.corriger("tooltip.society.bac", "Place tes &6bacs d'expédition&r ici", valeur)])
        self.assertEqual(corpus_mod.charger(self.pack, self.espace).texte("tooltip.society.bac"), valeur)

    def test_ligne_de_commande(self):
        chemin = self.espace / "lot.json"
        chemin.write_text(json.dumps(self.lot([self.corriger("item.society.bac", "Bac d'expédition", "Bac neuf")])),
                          encoding="utf-8")

        def lancer(*args):
            sortie = io.StringIO()
            with contextlib.redirect_stdout(sortie), contextlib.redirect_stderr(io.StringIO()):
                code = appliquer_lot.main([str(chemin), "--racine", str(self.pack), "--espace", str(self.espace), *args])
            return code, sortie.getvalue()

        code, sortie = lancer()
        self.assertEqual(code, 0)
        self.assertIn("0 refus", sortie)
        self.assertEqual(json.loads(self.lire(LANGUE_SOCIETY))["item.society.bac"], "Bac d'expédition")  # rien d'écrit
        code, _ = lancer("--appliquer")
        self.assertEqual((code, json.loads(self.lire(LANGUE_SOCIETY))["item.society.bac"]), (0, "Bac neuf"))


if __name__ == "__main__":
    unittest.main()
