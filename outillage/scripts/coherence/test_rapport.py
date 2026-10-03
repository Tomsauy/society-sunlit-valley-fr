"""Exceptions motivées, dette décroissante."""
import random
import unittest

from coherence.modele import BLOQUANT, SIGNALE, Constat
from coherence.rapport import appliquer, empreinte, empreinte_du_constat, obstacles_a_la_cloture

VALEURS = {"a": "Valeur A", "b": "Valeur B"}


def rapport(constats, exceptions=(), dette=(), lances=("codes", "accents")):
    return appliquer(list(constats), list(exceptions), list(dette), VALEURS.get, lances)


class TestRapport(unittest.TestCase):

    def test_bloquant_et_signale(self):
        r = rapport([Constat("codes", "a", BLOQUANT), Constat("accents", "b", SIGNALE)])
        self.assertEqual((len(r.bloquants), len(r.signales), r.code), (1, 1, 1))
        self.assertEqual(rapport([Constat("accents", "b", SIGNALE)]).code, 0)

    def test_exception_motivee(self):
        exc = {"controle": "codes", "cle": "a", "motif": "voulu", "date": "2026-09-28"}
        r = rapport([Constat("codes", "a", BLOQUANT)], [exc])
        self.assertEqual((r.bloquants, r.code), ([], 0))
        self.assertIs(r.couverts[0][1], exc)

    def test_exception_restreinte_a_un_objet(self):
        exc = {"controle": "codes", "cle": "a", "objet": "item.x.y", "motif": "voulu"}
        r = rapport([Constat("codes", "a", BLOQUANT, objet="item.x.z")], [exc])
        self.assertEqual(len(r.bloquants), 1)

    def test_exception_sans_motif(self):
        r = rapport([Constat("codes", "a", BLOQUANT)], [{"controle": "codes", "cle": "a", "motif": " "}])
        self.assertEqual((len(r.sans_motif), len(r.bloquants), r.code), (1, 1, 1))

    def test_orphelines_seulement_pour_les_controles_lances(self):
        excs = [{"controle": "codes", "cle": "z", "motif": "m"}, {"controle": "largeur", "cle": "z", "motif": "m"}]
        r = rapport([], excs)
        self.assertEqual([e["controle"] for e in r.orphelines], ["codes"])

    def test_epingle_ignoree(self):
        epingle = {"controle": "codes", "cle": "a", "objet": "item.x.y", "epingle": True, "motif": "m"}
        r = rapport([Constat("codes", "a", BLOQUANT)], [epingle])
        self.assertEqual((len(r.bloquants), r.orphelines), (1, []))

    def test_epingle_sans_motif(self):
        epingle = {"controle": "codes", "cle": "a", "objet": "item.x.y", "epingle": True, "motif": ""}
        r = rapport([Constat("codes", "a", BLOQUANT)], [epingle])
        self.assertEqual((len(r.sans_motif), r.code), (1, 1))

    def test_dette_inchangee(self):
        dette = [{"controle": "codes", "cle": "a", "empreinte": empreinte("Valeur A")}]
        r = rapport([Constat("codes", "a", BLOQUANT)], dette=dette)
        self.assertEqual((len(r.en_dette), r.bloquants, r.code), (1, [], 0))

    def test_dette_dont_la_valeur_a_change(self):
        dette = [{"controle": "codes", "cle": "a", "empreinte": empreinte("Ancienne valeur")}]
        r = rapport([Constat("codes", "a", SIGNALE)], dette=dette)
        self.assertEqual(len(r.bloquants), 1)
        self.assertIn("corriger", r.bloquants[0].detail)
        self.assertEqual(r.dette_resolue, [])

    def test_dette_resolue(self):
        dette = [{"controle": "codes", "cle": "a", "empreinte": "x"}, {"controle": "largeur", "cle": "b", "empreinte": "x"}]
        r = rapport([], dette=dette)
        self.assertEqual([e["controle"] for e in r.dette_resolue], ["codes"])

    def test_exception_a_empreinte_couvre_le_texte_photographie(self):
        exc = {"controle": "codes", "cle": "a", "motif": "voulu", "empreinte": empreinte("Valeur A")}
        r = rapport([Constat("codes", "a", BLOQUANT)], [exc])
        self.assertEqual((r.bloquants, r.orphelines, r.code), ([], [], 0))

    def test_exception_a_empreinte_tombe_quand_le_texte_change(self):
        exc = {"controle": "codes", "cle": "a", "motif": "voulu", "empreinte": empreinte("Ancienne valeur")}
        r = rapport([Constat("codes", "a", BLOQUANT)], [exc])
        self.assertEqual((len(r.bloquants), r.orphelines, r.code), (1, [exc], 1))

    def test_exceptions_a_empreinte_cent_textes_modifies(self):
        """Spec 2 §14 : cent vingt textes couverts par une exception sans objet, chacun modifié : chaque constat
        refait surface et chaque exception devient orpheline."""
        rng = random.Random(20260930)
        valeurs = {f"k{i}": f"Texte {i} {rng.random()}" for i in range(120)}
        excs = [{"controle": "codes", "cle": k, "motif": "voulu", "empreinte": empreinte(v)}
                for k, v in valeurs.items()]
        constats = [Constat("codes", k, BLOQUANT) for k in valeurs]
        avant = appliquer(constats, excs, [], valeurs.get, ("codes",))
        self.assertEqual((len(avant.couverts), avant.bloquants), (120, []))
        modifiees = {k: v + rng.choice([" ", ".", "e", "!"]) for k, v in valeurs.items()}
        apres = appliquer(constats, excs, [], modifiees.get, ("codes",))
        self.assertEqual((len(apres.bloquants), len(apres.couverts), len(apres.orphelines)), (120, 0, 120))


    def test_provisoires(self):
        exc = {"controle": "codes", "cle": "a", "motif": "en attente de la question porte", "question": "porte"}
        r = rapport([Constat("codes", "a", BLOQUANT)], [exc])
        self.assertEqual((r.bloquants, r.provisoires), ([], [exc]))

    def test_renvois(self):
        dette = [{"controle": "codes", "cle": "a", "empreinte": empreinte("Valeur A")}]
        bon = {"controle": "codes", "cle": "a", "motif": "sens à rétablir, étape 3"}
        orphelin = {"controle": "codes", "cle": "z", "motif": "m"}
        r = appliquer([Constat("codes", "a", BLOQUANT)], [], dette, VALEURS.get, ("codes",), [bon, orphelin])
        self.assertEqual((r.renvoyees, r.renvois_orphelins), ([bon], [orphelin]))

    def test_obstacles_a_la_cloture(self):
        dette = [{"controle": "codes", "cle": "a", "empreinte": empreinte("Valeur A")}]
        r = rapport([Constat("codes", "a", BLOQUANT)], dette=dette)
        self.assertEqual(len(obstacles_a_la_cloture(r, dette, [])), 1)          # une entrée de dette sans renvoi
        renvois = [{"controle": "codes", "cle": "a", "motif": "m"}]
        r = appliquer([Constat("codes", "a", BLOQUANT)], [], dette, VALEURS.get, ("codes",), renvois)
        self.assertEqual(obstacles_a_la_cloture(r, dette, renvois), [])
        provisoire = {"controle": "accents", "cle": "b", "motif": "m", "question": "q"}
        r = rapport([Constat("accents", "b", SIGNALE)], [provisoire])
        self.assertEqual(obstacles_a_la_cloture(r, [], []),
                         ["1 exception(s) provisoire(s) : des questions attendent leur réponse"])


class TestDetteParObjet(unittest.TestCase):
    """I2 : la dette s'apparie sur (contrôle, clé, objet) — elle ne couvre que le constat qu'elle a photographié."""

    def test_constat_nouveau_sur_une_cle_en_dette(self):
        """Renommer un objet fait citer, par un texte déjà en dette pour un autre objet, un nom devenu faux : ce constat
        nouveau bloque tel quel, au lieu d'être rangé en dette sans bruit."""
        dette = [{"controle": "codes", "cle": "a", "objet": "item.x.ancien", "empreinte": empreinte("Valeur A")}]
        r = rapport([Constat("codes", "a", BLOQUANT, objet="item.x.ancien"),
                     Constat("codes", "a", BLOQUANT, objet="item.x.nouveau")], dette=dette)
        self.assertEqual([c.objet for c in r.en_dette], ["item.x.ancien"])
        self.assertEqual([c.objet for c in r.bloquants], ["item.x.nouveau"])
        self.assertNotIn("valeur modifiée", r.bloquants[0].detail)

    def test_languagetool_ni_cache_ni_promu(self):
        """Spec §8 : LanguageTool est signalé. Sur une clé en dette pour une forme interdite, son constat n'est ni
        caché sous la dette, ni promu en bloquant quand la valeur change."""
        dette = [{"controle": "orthographe", "cle": "a", "objet": "tout les", "empreinte": empreinte("Ancienne valeur")}]
        lt = Constat("orthographe", "a", SIGNALE, objet="AGREEMENT_TOUT_LE")
        r = rapport([lt], dette=dette, lances=("orthographe",))
        self.assertEqual((r.signales, r.bloquants, r.en_dette), ([lt], [], []))
        self.assertEqual(r.dette_resolue, dette)  # la forme interdite corrigée : l'entrée est résolue

    def test_seule_l_entree_appariee_est_utile(self):
        dette = [{"controle": "codes", "cle": "a", "objet": "x", "empreinte": empreinte("Valeur A")},
                 {"controle": "codes", "cle": "a", "objet": "y", "empreinte": empreinte("Valeur A")}]
        r = rapport([Constat("codes", "a", BLOQUANT, objet="x")], dette=dette)
        self.assertEqual((len(r.en_dette), r.dette_resolue), (1, [dette[1]]))

    def test_objet_d_un_groupe_lu_du_json(self):
        constat = Constat("homonymes", "a", BLOQUANT, actuel="Un | Deux", objet=("a", "b"))
        entree = {"controle": "homonymes", "cle": "a", "objet": ["a", "b"],
                  "empreinte": empreinte_du_constat(constat, VALEURS.get)}
        r = rapport([constat], dette=[entree], lances=("homonymes",))
        self.assertEqual((len(r.en_dette), r.bloquants), (1, []))

    def test_homonymes_empreinte_des_variantes(self):
        """I3 : la dette d'un groupe photographie ses variantes ; un membre modifié (la valeur de la clé de tête ne
        change pas) promeut le constat."""
        avant = Constat("homonymes", "a", BLOQUANT, actuel="Terre labourée | Terres arables", objet=("a", "b"))
        entree = {"controle": "homonymes", "cle": "a", "objet": ["a", "b"],
                  "empreinte": empreinte_du_constat(avant, VALEURS.get)}
        apres = Constat("homonymes", "a", BLOQUANT, actuel="Terre cultivée | Terres arables", objet=("a", "b"))
        r = rapport([apres], dette=[entree], lances=("homonymes",))
        self.assertEqual(len(r.bloquants), 1)
        self.assertIn("valeur modifiée", r.bloquants[0].detail)


if __name__ == "__main__":
    unittest.main()
