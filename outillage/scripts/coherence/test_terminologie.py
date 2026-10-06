"""Termes imposés."""
import unittest
from pathlib import Path

from coherence import rapport
from coherence.config import Config
from coherence.controles import CONTROLES
from coherence.corpus import ChampLivre, Corpus
from coherence.modele import BLOQUANT, SIGNALE, Options
from coherence.registre import Registre

TERMES = [
    {"anglais": "crimson", "francais": "carmin", "motif": "STYLE §7"},
    {"anglais": "ash", "francais": "frêne", "cles": r"\.ash_", "motif": "essence Ash"},
    {"anglais": "polished", "francais": ["poli", "polie", "polis", "polies"], "motif": "vanilla"},
]
LIGNES = {
    "block.x.crimson_planks": ("Crimson Planks", "Planches cramoisies"),
    "block.x.crimson_slab": ("Crimson Slab", "Dalle carmin"),
    "tooltip.x.crimson": ("Found in Crimson Forests", "Se trouve dans les forêts cramoisies"),
    "block.x.ash_door": ("Ash Door", "Porte en cendre"),
    "item.x.ash": ("Ash", "Cendre"),
    "block.x.polished_andesite": ("Polished Andesite", "Andésite polie"),
}


class TestTerminologie(unittest.TestCase):

    def test_constats(self):
        c = Corpus()
        for cle, (en, fr) in LIGNES.items():
            c.en[cle], c.fr[cle], c.origine_fr[cle] = en, fr, "projet"
        config = Config(espace=Path("."), termes_imposes=TERMES)
        constats = {x.cle: x for x in CONTROLES["terminologie"](c, Registre(c, config), config, Options())}
        self.assertEqual({k: v.statut for k, v in constats.items()},
                         {"block.x.crimson_planks": BLOQUANT, "tooltip.x.crimson": SIGNALE, "block.x.ash_door": BLOQUANT})
        self.assertEqual(constats["block.x.ash_door"].attendu, "frêne")

    def test_champs_de_livres(self):
        """Le terme est imposé partout, livres compris : un champ de livre est un texte, donc signalé."""
        c = Corpus()
        c.livres = [ChampLivre("almanac/entries/trees/darkcherry.json", "/name", "Crimson Tree", "Arbre cramoisi"),
                    ChampLivre("almanac/entries/trees/crimson.json", "/name", "Crimson Tree", "Arbre carmin")]
        config = Config(espace=Path("."), termes_imposes=TERMES)
        constats = CONTROLES["terminologie"](c, Registre(c, config), config, Options())
        self.assertEqual([(x.cle, x.statut) for x in constats], [(c.livres[0].cle, SIGNALE)])

    def test_portee(self):
        """M7 : « portee » limite un terme aux noms d'objets (« noms ») ou aux textes (« textes ») ; « tout » par défaut."""
        c = Corpus()
        for cle, (en, fr) in {"block.x.ash_log": ("Ash Log", "Bûche de cendre"),
                              "tooltip.x.ash": ("Burn it to ash", "Brûle-le en cendre")}.items():
            c.en[cle], c.fr[cle], c.origine_fr[cle] = en, fr, "projet"
        attendus = {"noms": ["block.x.ash_log"], "textes": ["tooltip.x.ash"], "tout": ["block.x.ash_log", "tooltip.x.ash"]}
        for portee, cles in attendus.items():
            with self.subTest(portee=portee):
                config = Config(espace=Path("."), termes_imposes=[{"anglais": "ash", "francais": "frêne", "portee": portee,
                                                                   "motif": "essai"}])
                constats = CONTROLES["terminologie"](c, Registre(c, config), config, Options())
                self.assertEqual(sorted(x.cle for x in constats), cles)

    def test_forme_a_majuscule(self):
        """Une forme imposée écrite avec sa majuscule (STYLE §7 : « Maîtrise du minage ») la garde partout."""
        termes = [{"anglais": "mining mastery", "francais": "Maîtrise du minage", "motif": "STYLE §7"}]
        c = Corpus()
        for cle, (en, fr) in {"jei.x.mining": ("Requires Mining Mastery", "Nécessite la maîtrise du minage"),
                              "quest.x.mining": ("Unlock Mining Mastery", "Débloque la Maîtrise du minage"),
                              "quest.x.debut": ("Mining Mastery unlocks it", "Maîtrise du minage requise")}.items():
            c.en[cle], c.fr[cle], c.origine_fr[cle] = en, fr, "projet"
        config = Config(espace=Path("."), termes_imposes=termes)
        constats = CONTROLES["terminologie"](c, Registre(c, config), config, Options())
        self.assertEqual([x.cle for x in constats], ["jei.x.mining"])
        self.assertIn("majuscule", constats[0].detail)


def _interdits(lignes, termes, exceptions=(), regle=True):
    """Les constats « rendu interdit » du contrôle sur ces lignes, et le résultat une fois les exceptions appliquées."""
    c = Corpus()
    for cle, (en, fr) in lignes.items():
        c.en[cle], c.fr[cle], c.origine_fr[cle] = en, fr, "projet"
    config = Config(espace=Path("."), termes_imposes=termes, exceptions=list(exceptions))
    config.regles["terminologie_interdits"] = regle
    constats = [x for x in CONTROLES["terminologie"](c, Registre(c, config), config, Options()) if "≠" in x.objet]
    return constats, rapport.appliquer(constats, config.exceptions, [], c.texte, ["terminologie"])


class TestInterdits(unittest.TestCase):
    """Un rendu interdit (« interdits ») resté dans un texte dont l'anglais emploie le terme est bloquant, nom ou texte."""

    def test_rendu_interdit_bloquant(self):
        termes = [{"anglais": "crimson", "francais": "carmin", "interdits": ["cramoisi"], "motif": "STYLE §7"}]
        constats, _ = _interdits({"tooltip.x.crimson": ("Crimson wood", "Bois carmin, dit cramoisi"),
                                  "tooltip.x.bon": ("Crimson wood", "Bois carmin"),
                                  "tooltip.x.autre": ("Red wood", "Bois cramoisi")}, termes)
        self.assertEqual([(x.cle, x.statut) for x in constats], [("tooltip.x.crimson", BLOQUANT)])
        self.assertEqual(constats[0].objet, "crimson ≠ cramoisi")
        self.assertIn("cramoisi", constats[0].detail)

    def test_regle_en_attente(self):
        """Sous la règle terminologie_interdits (regles.json) seulement : désactivée, aucun rendu interdit n'est relevé."""
        termes = [{"anglais": "crimson", "francais": "carmin", "interdits": ["cramoisi"], "motif": "STYLE §7"}]
        constats, _ = _interdits({"tooltip.x.crimson": ("Crimson wood", "Bois carmin, dit cramoisi")}, termes,
                                 regle=False)
        self.assertEqual(constats, [])

    def test_casse_et_accents(self):
        termes = [{"anglais": "aging casks?", "francais": "tonneau", "interdits": ["fût"], "motif": "essai"}]
        constats, _ = _interdits({"tooltip.x.majuscules": ("Aging Cask", "Tonneau, ancien FÛT"),
                                  "tooltip.x.sans_accent": ("Aging Cask", "Tonneau (ex-fut)")}, termes)
        self.assertEqual(sorted(x.cle for x in constats), ["tooltip.x.majuscules", "tooltip.x.sans_accent"])

    def test_pluriels(self):
        termes = [{"anglais": "crab traps?", "francais": "casier à crabes", "interdits": ["piège à crabes"],
                   "motif": "essai"}]
        constats, _ = _interdits({"tooltip.x.crabes": ("Crab Traps", "Les casiers à crabes, ou pièges à crabes")},
                                 termes)
        self.assertEqual([x.cle for x in constats], ["tooltip.x.crabes"])

    def test_interdit_contenu_dans_le_rendu_impose(self):
        """« clé » est interdit, « mot clé » imposé : le mot de la forme imposée ne déclenche rien, une clé seule si."""
        termes = [{"anglais": "tags?", "francais": "mot clé", "interdits": ["clé"], "motif": "essai"}]
        constats, _ = _interdits({"tooltip.x.juste": ("Item Tags", "Mots clés d'objet"),
                                  "tooltip.x.faux": ("Item Tags", "Mots clés d'objet (clés)")}, termes)
        self.assertEqual([x.cle for x in constats], ["tooltip.x.faux"])

    def test_portee_et_cles(self):
        """L'interdit ne vaut que dans la portée de l'entrée : mêmes « cles », même « portee »."""
        termes = [{"anglais": "ash", "francais": "frêne", "cles": r"\.ash_", "portee": "noms", "interdits": ["cendre"],
                   "motif": "essai"}]
        constats, _ = _interdits({"block.x.ash_door": ("Ash Door", "Porte en cendre"),
                                  "item.x.ash": ("Ash", "Cendre"),
                                  "tooltip.x.ash_door": ("Ash Door", "Frêne, pas cendre")}, termes)
        self.assertEqual([x.cle for x in constats], ["block.x.ash_door"])

    def test_exception_leve_le_bloquant(self):
        termes = [{"anglais": "crimson", "francais": "carmin", "interdits": ["cramoisi"], "motif": "STYLE §7"}]
        exception = {"controle": "terminologie", "cle": "tooltip.x.crimson", "objet": "crimson ≠ cramoisi",
                     "motif": "citation", "date": "2026-10-06"}
        constats, resultat = _interdits({"tooltip.x.crimson": ("Crimson wood", "Bois carmin, dit cramoisi")}, termes,
                                        [exception])
        self.assertEqual(len(constats), 1)
        self.assertEqual(resultat.bloquants, [])
        self.assertEqual(len(resultat.couverts), 1)


if __name__ == "__main__":
    unittest.main()
