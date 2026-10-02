"""Le générateur des familles dérivées."""
import contextlib
import io
import json
import shutil
import unittest

import generer_derives
from coherence import config as config_mod, corpus as corpus_mod
from coherence.fabrique import ecrire, pack_et_espace
from coherence.registre import Registre

POISSONS = ["entity.aquaculture.{id}", "entity.unusualfishmod.{id}"]
PACK = {
    "pakku.json": {"version": "4.1.5"},
    "kubejs/assets/society/lang/en_us.json": {"item.society.pike_roe": "Pike Roe",
                                              "item.society.catfish_bait": "Giant Cave Catfish Bait",
                                              "item.society.frosty_fin_roe": "Frosty Fin Roe",
                                              "item.society.aged_frosty_fin_roe": "Aged Frosty Fin Roe"},
    "kubejs/assets/society/lang/fr_fr.json": {"item.society.carp_roe": "Oeufs de carpe",
                                              "item.society.smoked_carp": "Carpe fumé",
                                              "item.society.smoked_pike": "Brochet fumé",
                                              "item.society.frosty_fin_roe": "Oeufs de nageoire givrée",
                                              "item.society.aged_frosty_fin_roe": "Oeufs de nageoire givrée vieillis",
                                              "item.society.tomato_preserves": "Conserve de tomates",
                                              "item.society.apricot_preserves": "Conserve d'abricots"},
    "kubejs/data/society_trading/shops/fisher.json": {"trades": [{"offer": {"item": "society:catfish_bait"}}]},
}
ESPACE = {
    "extracted/aquaculture-1/aquaculture/en_us.json": {"entity.aquaculture.carp": "Carp", "entity.aquaculture.pike": "Pike",
                                                       "entity.aquaculture.catfish": "Giant Cave Catfish"},
    "extracted/aquaculture-1/aquaculture/fr_fr.json": {"entity.aquaculture.carp": "Carpe", "entity.aquaculture.pike": "Brochet",
                                                       "entity.aquaculture.catfish": "Poisson-chat des cavernes géant"},
    "extracted/ufm-1/unusualfishmod/en_us.json": {"entity.unusualfishmod.frostyfin": "Frosty Fin"},
    "extracted/fruits-1/fruits/en_us.json": {"item.fruits.tomato": "Tomato", "item.fruits.apricot": "Apricot"},
    "extracted/fruits-1/fruits/fr_fr.json": {"item.fruits.tomato": "Tomate", "item.fruits.apricot": "Abricot"},
    "extracted/ufm-1/unusualfishmod/fr_fr.json": {"entity.unusualfishmod.frostyfin": "Nageoire givrée"},
    "provenance.json": {"cles": {}},
    "coherence/familles.json": {
        "familles": [
            {"nom": "oeufs_vieillis", "motif": "item.society.aged_{id}_roe", "source": ["item.society.{id}_roe"],
             "gabarit": "{Source} vieillis", "anglais": "Aged {source} Roe"},
            {"nom": "conserve", "motif": "item.society.{id}_preserves", "source": ["item.fruits.{id}"],
             "gabarit": "Conserve de {sources}", "anglais": "{source} Preserves"},
            {"nom": "oeufs", "motif": "item.society.{id}_roe", "source": POISSONS, "gabarit": "Oeufs de {source}", "anglais": "{source} Roe"},
            {"nom": "appat", "motif": "item.society.{id}_bait", "source": POISSONS, "gabarit": "Appât pour {source}", "anglais": "{source} Bait"},
            {"nom": "fume", "motif": "item.society.smoked_{id}", "source": POISSONS, "gabarit": "{Source} fumé{e}{s}", "anglais": "Smoked {source}"},
        ],
        "accords": {"entity.aquaculture.carp": {"genre": "f", "nombre": "s"}},
    },
}


class TestGenerateur(unittest.TestCase):

    def setUp(self):
        self.dossier, self.pack, self.espace = pack_et_espace(PACK, ESPACE)
        self.addCleanup(self.dossier.cleanup)
        self.corpus = corpus_mod.charger(self.pack, self.espace)
        self.config = config_mod.charger_config(self.espace)

    def test_propositions_et_refus(self):
        ecritures, refus, laissees = generer_derives.propositions(self.corpus, self.config)
        self.assertEqual(laissees, [])
        self.assertEqual([(c, a, b) for c, a, b, _ in ecritures],
                         [("item.society.pike_roe", "", "Oeufs de brochet"),
                          ("item.society.smoked_carp", "Carpe fumé", "Carpe fumée")])
        raisons = dict(refus)
        self.assertIn("deux lignes", raisons["item.society.catfish_bait"])
        self.assertIn("source inconnue", raisons["item.society.frosty_fin_roe"])
        self.assertIn("genre inconnu", raisons["item.society.smoked_pike"])
        self.assertIn("pluriel inconnu", raisons["item.society.tomato_preserves"])

    def test_proposer(self):
        p = generer_derives.proposer(self.corpus, self.config, Registre(self.corpus, self.config))
        # la famille en chaîne (oeufs vieillis) n'a pas de source à proposer : elle suit les oeufs
        self.assertEqual(p["sources"], {"oeufs": {"frosty_fin": ["entity.unusualfishmod.frostyfin"]}})
        self.assertEqual({k: (v["genre"], v["nombre"]) for k, v in p["accords"].items() if "genre" in v},
                         {"entity.aquaculture.pike": ("m", "s")})
        self.assertEqual({k: v["pluriel"] for k, v in p["accords"].items() if "pluriel" in v},
                         {"item.fruits.apricot": "abricots", "item.fruits.tomato": "tomates"})

    def test_appliquer(self):
        with contextlib.redirect_stdout(io.StringIO()):
            code = generer_derives.main(["--racine", str(self.pack), "--espace", str(self.espace), "--appliquer"])
        self.assertEqual(code, 1)  # des refus : la sortie le dit, l'écriture a lieu pour le reste
        fr = json.loads((self.pack / "kubejs/assets/society/lang/fr_fr.json").read_text(encoding="utf-8"))
        self.assertEqual((fr["item.society.pike_roe"], fr["item.society.smoked_carp"]), ("Oeufs de brochet", "Carpe fumée"))
        prov = json.loads((self.espace / "provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(prov["cles"]["item.society.smoked_carp"][-1]["type"], "regle")
        self.assertEqual(prov["cles"]["item.society.smoked_carp"][-1]["avant"], "Carpe fumé")

    def test_action_de(self):
        corpus = corpus_mod.Corpus()
        corpus.fr["block.x.a"] = "Ancien"
        self.assertEqual(generer_derives.action_de("block.x.a", "Ancien", "Nouveau", "oeufs", corpus),
                         {"type": "correction", "cle": "block.x.a", "avant": "Ancien", "apres": "Nouveau",
                          "motif": "rendu de la famille oeufs (familles.json)"})
        absente = generer_derives.action_de("block.x.b", "", "Nouveau", "oeufs", corpus)
        self.assertEqual((absente["avant"], absente["espace"]), (None, "x"))


CARPE = "item.society.smoked_carp"  # « Carpe fumé » dans le pack ; la règle rend « Carpe fumée »


class TestCeQueLeGenerateurNeDefaitPas(unittest.TestCase):
    """Spec §7 (« sauf exception ») et §9 (une décision « ne peut plus être défaite en silence ») : ni un écart
    déclaré, ni une décision humaine tracée, ni une clé en attente de décision ne se réécrivent sans --forcer."""

    def setUp(self):
        self.dossier, self.pack, self.espace = pack_et_espace(PACK, ESPACE)
        self.addCleanup(self.dossier.cleanup)
        self.corpus = corpus_mod.charger(self.pack, self.espace)
        self.config = config_mod.charger_config(self.espace)

    def ecrites(self, **options):
        ecritures, refus, laissees = generer_derives.propositions(self.corpus, self.config, **options)
        return [c for c, *_ in ecritures], dict(refus), dict(laissees)

    def test_ecart_declare_laisse(self):
        self.config.exceptions = [{"controle": "familles", "cle": CARPE, "motif": "voulu", "date": "2026-09-29"}]
        ecrites, refus, laissees = self.ecrites()
        self.assertNotIn(CARPE, ecrites)
        self.assertNotIn(CARPE, refus)  # laissée, pas refusée : l'écart est voulu
        self.assertEqual(laissees, {CARPE: "voulu"})

    def test_exception_sans_motif_ou_d_un_autre_controle_ne_laisse_rien(self):
        self.config.exceptions = [{"controle": "familles", "cle": CARPE, "motif": " "},
                                  {"controle": "casse", "cle": CARPE, "motif": "autre contrôle"}]
        self.assertIn(CARPE, self.ecrites()[0])

    def test_decision_humaine_contraire_refusee(self):
        self.config.provenance = {"cles": {CARPE: [{"type": "relecture", "fr": "Carpe fumé", "raison": "choix"}]}}
        ecrites, refus, _ = self.ecrites()
        self.assertNotIn(CARPE, ecrites)
        self.assertIn("décision tracée", refus[CARPE])
        self.assertIn("Carpe fumé", refus[CARPE])

    def test_decision_sans_valeur_refusee(self):
        self.config.provenance = {"cles": {CARPE: [{"type": "arbitrage", "decision": "garde_anglais"}]}}
        self.assertIn("décision tracée", self.ecrites()[1][CARPE])

    def test_decision_conforme_ou_regle_acceptee(self):
        for decisions in ([{"type": "relecture", "fr": "Carpe fumée"}],
                          [{"type": "relecture", "fr": "Carpe fumé"}, {"type": "regle", "fr": "Carpe fumé"}]):
            with self.subTest(decisions=decisions):
                self.config.provenance = {"cles": {CARPE: decisions}}
                self.assertIn(CARPE, self.ecrites()[0])

    def test_dette_en_attente_de_decision_refusee(self):
        self.config.dette = [{"controle": "familles", "cle": CARPE, "empreinte": "x", "en_attente_de_decision": True}]
        ecrites, refus, _ = self.ecrites()
        self.assertNotIn(CARPE, ecrites)
        self.assertIn("en attente de décision", refus[CARPE])
        self.config.dette[0].pop("en_attente_de_decision")  # une dette ordinaire se corrige : la règle l'écrit
        self.assertIn(CARPE, self.ecrites()[0])

    def test_forcer(self):
        self.config.exceptions = [{"controle": "familles", "cle": CARPE, "motif": "voulu", "date": "2026-09-29"}]
        self.config.provenance = {"cles": {CARPE: [{"type": "relecture", "fr": "Carpe fumé"}]}}
        self.config.dette = [{"controle": "familles", "cle": CARPE, "empreinte": "x", "en_attente_de_decision": True}]
        ecrites, refus, laissees = self.ecrites(forcer=True)
        self.assertIn(CARPE, ecrites)
        self.assertEqual((refus.get(CARPE), laissees), (None, {}))

    def test_ligne_de_commande(self):
        ecrire(self.espace, {
            "provenance.json": {"cles": {CARPE: [{"type": "relecture", "fr": "Carpe fumé", "raison": "choix"}]}},
            "coherence/exceptions.json": [{"controle": "familles", "cle": "item.society.pike_roe", "motif": "voulu",
                                           "date": "2026-09-29"}]})
        lancer = lambda *args: generer_derives.main(["--racine", str(self.pack), "--espace", str(self.espace), *args])
        fichier = self.pack / "kubejs/assets/society/lang/fr_fr.json"
        with contextlib.redirect_stdout(io.StringIO()) as sortie:
            self.assertEqual(lancer("--appliquer"), 1)
        self.assertIn(f"LAISSÉE {'item.society.pike_roe'} : écart déclaré, laissé (voulu)", sortie.getvalue())
        self.assertIn(f"REFUS {CARPE} : décision tracée", sortie.getvalue())
        fr = json.loads(fichier.read_text(encoding="utf-8"))
        self.assertEqual((fr[CARPE], fr.get("item.society.pike_roe")), ("Carpe fumé", None))
        with contextlib.redirect_stdout(io.StringIO()):
            lancer("--appliquer", "--forcer")
        fr = json.loads(fichier.read_text(encoding="utf-8"))
        self.assertEqual((fr[CARPE], fr["item.society.pike_roe"]), ("Carpe fumée", "Oeufs de brochet"))
        prov = json.loads((self.espace / "provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(prov["cles"][CARPE][-1]["type"], "regle")

    def test_donnees_absentes(self):
        """M8 : une donnée manquante donne un message et le code 2, pas une trace de pile."""
        (self.espace / "coherence" / "familles.json").unlink()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as erreurs:
            code = generer_derives.main(["--racine", str(self.pack), "--espace", str(self.espace)])
        self.assertEqual(code, 2)
        self.assertIn("familles.json introuvable", erreurs.getvalue())
        shutil.rmtree(self.espace / "extracted")
        ecrire(self.espace, {"coherence/familles.json": {"familles": [], "accords": {}}})
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as erreurs:
            code = generer_derives.main(["--racine", str(self.pack), "--espace", str(self.espace)])
        self.assertEqual(code, 2)
        self.assertIn("--instantane", erreurs.getvalue())


if __name__ == "__main__":
    unittest.main()
