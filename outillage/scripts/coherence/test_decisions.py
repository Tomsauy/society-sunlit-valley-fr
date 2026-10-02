"""Décisions verrouillées et réconciliation de provenance.json."""
import unittest
from pathlib import Path

import reconcilier_provenance as rp
from coherence.config import Config
from coherence.controles import CONTROLES
from coherence.controles.decisions import valeur_actuelle, valeur_decidee
from coherence.corpus import ChampLivre, Corpus
from coherence.modele import Options

PROVENANCE = {"cles": {
    "a": [{"type": "relecture", "fr": "Un", "fichier": "kubejs/assets/society/lang/fr_fr.json"}],
    "b": [{"type": "arbitrage_identique", "decision": "garde_anglais"}],
    "c": [{"type": "relecture", "fr": "Deux"}, {"type": "relecture", "fr": "Trois"}],
    "d": [{"type": "relecture", "fr": "Cle rouge"}],
    "e": [{"type": "relecture", "fr": "X", "fichier": "kubejs/assets/trials/lang/fr_fr.json"}],
    "wood_type.atmospheric.aspen": [{"type": "relecture", "fr": "Tremble"}],
}, "cles_mortes_ecartees": [], "_statistiques": {"arbitrages": 1}}
FR = {"a": "Un", "c": "Deux", "d": "Clé rouge"}


class TestDecisions(unittest.TestCase):

    def test_valeur_decidee(self):
        self.assertEqual(valeur_decidee(PROVENANCE["cles"]["c"]), "Trois")
        self.assertIsNone(valeur_decidee(PROVENANCE["cles"]["b"]))

    def test_controle(self):
        c = Corpus(fr=dict(FR))
        config = Config(espace=Path("."), provenance=PROVENANCE)
        constats = {x.cle: x for x in CONTROLES["decisions"](c, None, config, Options())}
        self.assertEqual(sorted(constats), ["c", "d", "e", "wood_type.atmospheric.aspen"])
        self.assertEqual((constats["c"].actuel, constats["c"].attendu), ("Deux", "Trois"))
        self.assertIn("absente", constats["e"].detail)

    def test_journal(self):
        """Le journal, tracé sous « journal » par l'applicateur des lots, est lu dans corpus.journal_fr."""
        provenance = {"cles": {"journal": [{"type": "correction", "fr": "- Ajout de la hutte Ribbit"}]}}
        config = Config(espace=Path("."), provenance=provenance)
        self.assertEqual(CONTROLES["decisions"](Corpus(journal_fr="- Ajout de la hutte Ribbit"), None, config,
                                                Options()), [])
        constats = CONTROLES["decisions"](Corpus(journal_fr="- Ajout de la hutte ribbit"), None, config, Options())
        self.assertEqual([(x.cle, x.actuel) for x in constats], [("journal", "- Ajout de la hutte ribbit")])
        self.assertIsNone(valeur_actuelle(Corpus(), "journal"))

    def test_classer_et_appliquer(self):
        import copy
        provenance = copy.deepcopy(PROVENANCE)
        corpus = Corpus(fr=dict(FR), essences=["wood_type.atmospheric.aspen"])
        classes = rp.classer(provenance, corpus)
        self.assertEqual({k: sorted(v) for k, v in classes.items()},
                         {"conformes": ["a"], "accents": ["d"], "ligature": [], "ecarts": ["c"],
                          "a_ecrire": ["wood_type.atmospheric.aspen"], "absentes": ["e"], "sans_valeur": ["b"]})
        rp.appliquer(provenance, corpus, classes)
        self.assertIn("wood_type.atmospheric.aspen", provenance["cles"])  # essence activée : à écrire, pas morte
        self.assertEqual(provenance["cles"]["d"][-1]["type"], "reaccentuation")
        self.assertEqual(provenance["cles"]["d"][-1]["fr"], "Clé rouge")
        self.assertNotIn("e", provenance["cles"])
        self.assertEqual(provenance["cles_mortes_ecartees"][-1]["ns"], "trials")
        self.assertNotIn("_statistiques", provenance)


LIVRE = "almanac/entries/animals/cow.json"
PROVENANCE_LIVRES = {"cles": {
    f"{LIVRE}#/name": [{"type": "relecture", "fr": "Vache", "fichier": "patchouli_books/almanac/fr_fr/entries/animals/cow.json"}],
    f"{LIVRE}#/pages/0/text": [{"type": "relecture", "fr": "Butin : Bœuf cru"}],
    f"{LIVRE}#/pages/1/text": [{"type": "relecture", "fr": "Une vache."}],
    f"{LIVRE}#/pages/9/name": [{"type": "relecture", "fr": "Pousse de vache"}],
    "cle.ligature": [{"type": "relecture", "fr": "Un cœur"}],
}}


def corpus_des_livres() -> Corpus:
    return Corpus(fr={"cle.ligature": "Un coeur"}, livres=[
        ChampLivre(LIVRE, "/name", "Cow", "Vache"),
        ChampLivre(LIVRE, "/pages/0/text", "Loot: Raw Beef", "Butin : Boeuf cru"),
        ChampLivre(LIVRE, "/pages/1/text", "A cow.", "Une génisse.")])


class TestDecisionsDesLivres(unittest.TestCase):
    """I5 : une décision tracée sur un champ de livre (« <livre>/<fichier>#/<pointeur> ») est verrouillée comme celle
    d'une clé de langue (spec §9 : « chaque clé dont provenance.json fixe une valeur »)."""

    def test_controle(self):
        config = Config(espace=Path("."), provenance=PROVENANCE_LIVRES)
        constats = {x.cle: x for x in CONTROLES["decisions"](corpus_des_livres(), None, config, Options())}
        self.assertEqual(sorted(constats), [f"{LIVRE}#/pages/0/text", f"{LIVRE}#/pages/1/text",
                                            f"{LIVRE}#/pages/9/name", "cle.ligature"])
        self.assertEqual((constats[f"{LIVRE}#/pages/1/text"].actuel, constats[f"{LIVRE}#/pages/1/text"].attendu),
                         ("Une génisse.", "Une vache."))
        self.assertIn("absente", constats[f"{LIVRE}#/pages/9/name"].detail)  # champ que le livre n'a pas

    def test_valeur_actuelle(self):
        corpus = corpus_des_livres()
        self.assertEqual(valeur_actuelle(corpus, f"{LIVRE}#/name"), "Vache")
        self.assertIsNone(valeur_actuelle(corpus, f"{LIVRE}#/pages/9/name"))
        self.assertIsNone(valeur_actuelle(corpus, "cle.absente"))

    def test_classer_et_tracer_la_ligature(self):
        """Un champ de livre présent n'est pas une clé morte ; un écart de la seule ligature se trace comme la
        réaccentuation : convention « oe » de CLAUDE.md, appliquée par le fork 01708c67."""
        import copy
        provenance = copy.deepcopy(PROVENANCE_LIVRES)
        corpus = corpus_des_livres()
        classes = rp.classer(provenance, corpus)
        self.assertEqual({k: sorted(v) for k, v in classes.items() if v},
                         {"conformes": [f"{LIVRE}#/name"], "ligature": [f"{LIVRE}#/pages/0/text", "cle.ligature"],
                          "ecarts": [f"{LIVRE}#/pages/1/text"], "absentes": [f"{LIVRE}#/pages/9/name"]})
        rp.appliquer(provenance, corpus, classes)
        trace = provenance["cles"][f"{LIVRE}#/pages/0/text"][-1]
        self.assertEqual((trace["type"], trace["fr"], trace["date"], trace["commit"]),
                         ("ligature", "Butin : Boeuf cru", "2026-09-09", "01708c67"))
        self.assertIn("CLAUDE.md", trace["raison"])
        self.assertEqual(valeur_decidee(provenance["cles"]["cle.ligature"]), "Un coeur")
        self.assertEqual(provenance["cles_mortes_ecartees"][-1]["ns"], "almanac")  # le livre, pour un champ mort

    def test_ligne_de_commande_sans_donnees(self):
        """M8 : le réconciliateur, face à une donnée manquante, dit laquelle et rend 2, sans trace de pile."""
        import contextlib
        import io
        from coherence.fabrique import PACK, pack_et_espace
        dossier, pack, espace = pack_et_espace(PACK, {})
        self.addCleanup(dossier.cleanup)
        (espace / "coherence" / "dette.json").unlink()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as erreurs:
            code = rp.main(["--racine", str(pack), "--espace", str(espace)])
        self.assertEqual(code, 2)
        self.assertIn("dette.json introuvable", erreurs.getvalue())

    def test_arbitrage_en_attente_jamais_resolu_mecaniquement(self):
        """Une clé que la dette tient en attente de décision (« Cœur d'ange » : ni « Coeur », ni la décision ; l'objet
        s'appelle « Noyau d'ange ») reste un vrai écart, même quand seule la ligature la sépare de sa décision."""
        classes = rp.classer(PROVENANCE_LIVRES, corpus_des_livres(), en_attente={"cle.ligature"})
        self.assertEqual((classes["ligature"], classes["ecarts"]),
                         ([f"{LIVRE}#/pages/0/text"], [f"{LIVRE}#/pages/1/text", "cle.ligature"]))


if __name__ == "__main__":
    unittest.main()
