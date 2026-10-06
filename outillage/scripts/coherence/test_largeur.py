"""Noms vendus en boutique, libellés contraints de largeurs.json, contraintes d'affichage des mods."""
import unittest
from pathlib import Path

from coherence.config import Config
from coherence.controles import CONTROLES
from coherence.corpus import Corpus
from coherence.modele import BLOQUANT, SIGNALE, Options
from coherence.police import lignes, px

LONG = "Appât pour poisson-chat des cavernes géant"
ACTIVE = {"casse_textes": False, "pourcentages": "", "nombres": False, "largeurs_mods": True}
INACTIVE = dict(ACTIVE, largeurs_mods=False)


def corpus(valeurs) -> Corpus:
    """{clé : (anglais, français, origine)}."""
    c = Corpus()
    for cle, (en, fr, origine) in valeurs.items():
        c.en[cle], c.fr[cle], c.origine_fr[cle] = en, fr, origine
    return c


def contrainte(limite=40, comportement="coupé", **champs):
    return dict({"limite": limite, "comportement": comportement, "mod": "mod_x", "preuve": "Ecran#rendu : 40 px"},
                **champs)


def constats(c, largeurs, regles=ACTIVE):
    config = Config(espace=Path("."), largeurs=largeurs, regles=dict(regles))
    return {x.cle: x for x in CONTROLES["largeur"](c, None, config, Options())}


class TestLargeur(unittest.TestCase):

    def test_constats(self):
        c = Corpus(vendus={"society:long", "jar:long", "society:court", "society:bloc"})
        valeurs = {"item.society.long": (LONG, "projet"), "item.jar.long": (LONG, "jar"),
                   "item.society.court": ("Pomme", "projet"), "block.society.bloc": (LONG, "projet"),
                   "gui.x.titre": ("Boutiques", "projet"), "gui.x.autre": ("Achats", "projet")}
        for cle, (fr, origine) in valeurs.items():
            c.fr[cle], c.origine_fr[cle] = fr, origine
        config = Config(espace=Path("."), largeurs=[{"cle": "gui.x.titre", "limite": 46, "motif": "SelectorScreen"},
                                                   {"cle": "gui.x.autre", "limite": 46, "motif": "SelectorScreen"}])
        constats = {x.cle: x.statut for x in CONTROLES["largeur"](c, None, config, Options())}
        self.assertEqual(constats, {"item.society.long": BLOQUANT, "item.jar.long": SIGNALE,
                                    "block.society.bloc": BLOQUANT, "gui.x.titre": BLOQUANT})

    def test_ancienne_entree_toujours_active(self):
        """L'entrée manuelle {cle, limite, motif} : motif est sa justification, pas une expression ; elle reste
        active sans la règle, et bloque quel que soit l'anglais."""
        c = corpus({"gui.x.titre": ("Shop selector, far too long", "Boutiques", "projet")})
        ancienne = [{"cle": "gui.x.titre", "limite": 46, "motif": "SelectorScreen centre le titre"}]
        x = constats(c, ancienne, INACTIVE)["gui.x.titre"]
        self.assertEqual((x.statut, x.preuve), (BLOQUANT, "SelectorScreen centre le titre"))

    def test_regle_inactive(self):
        c = corpus({"gui.a": ("Go", "Commencer maintenant", "projet")})
        self.assertEqual(constats(c, [contrainte(cles=["gui.a"])], INACTIVE), {})
        self.assertIn("gui.a", constats(c, [contrainte(cles=["gui.a"])], ACTIVE))

    def test_toutes_regles(self):
        c = corpus({"gui.a": ("Go", "Commencer maintenant", "projet")})
        config = Config(espace=Path("."), largeurs=[contrainte(cles=["gui.a"])], regles=dict(INACTIVE))
        self.assertEqual(len(CONTROLES["largeur"](c, None, config, Options(toutes_regles=True))), 1)

    def test_cles(self):
        c = corpus({"gui.a": ("Go", "Commencer maintenant", "projet"), "gui.b": ("Stop", "Arrêt", "projet"),
                    "gui.c": ("Go", "Commencer maintenant", "projet")})
        self.assertEqual(set(constats(c, [contrainte(cles=["gui.a", "gui.b"])])), {"gui.a"})

    def test_cle_seule(self):
        c = corpus({"gui.a": ("Go", "Commencer maintenant", "projet")})
        self.assertEqual(set(constats(c, [contrainte(cle="gui.a")])), {"gui.a"})

    def test_motif(self):
        c = corpus({"gui.mod.bouton.a": ("Go", "Commencer maintenant", "projet"),
                    "gui.mod.bouton.b": ("Go", "Commencer maintenant", "jar"),
                    "gui.autre.bouton.c": ("Go", "Commencer maintenant", "projet")})
        resultat = constats(c, [contrainte(motif=r"^gui\.mod\.bouton\.")])
        self.assertEqual({k: x.statut for k, x in resultat.items()},
                         {"gui.mod.bouton.a": BLOQUANT, "gui.mod.bouton.b": BLOQUANT})

    def test_cles_et_motif_reunis(self):
        c = corpus({"gui.a": ("Go", "Commencer maintenant", "projet"),
                    "gui.mod.b": ("Go", "Commencer maintenant", "projet")})
        self.assertEqual(set(constats(c, [contrainte(cles=["gui.a"], motif=r"^gui\.mod\.")])), {"gui.a", "gui.mod.b"})

    def test_anglais_qui_tient(self):
        """L'anglais tient, le français dépasse : bloquant, que le texte vienne du projet ou du jar."""
        c = corpus({"gui.a": ("Go", "Commencer maintenant", "jar")})
        x = constats(c, [contrainte(cles=["gui.a"])])["gui.a"]
        self.assertEqual(x.statut, BLOQUANT)
        self.assertIn(f"{px('Commencer maintenant')} px", x.detail)
        self.assertIn("40", x.detail)
        self.assertIn(f"{px('Go')} px", x.detail)
        self.assertIn("mod_x", x.preuve)
        self.assertIn("Ecran#rendu", x.preuve)

    def test_francais_qui_tient(self):
        c = corpus({"gui.a": ("Start", "Lancer", "projet")})
        self.assertEqual(constats(c, [contrainte(cles=["gui.a"])]), {})

    def test_anglais_qui_depasse(self):
        """L'anglais dépasse déjà : le français ne doit pas être plus long ; s'il l'est, signalé seulement."""
        en = "Begin the process now"
        c = corpus({"gui.long": (en, "Commencer le processus maintenant", "projet"),
                    "gui.court": (en, "Commencer", "projet"),
                    "gui.egal": (en, en, "projet")})
        resultat = constats(c, [contrainte(cles=["gui.long", "gui.court", "gui.egal"])])
        self.assertGreater(px(en), 40)
        self.assertEqual({k: x.statut for k, x in resultat.items()}, {"gui.long": SIGNALE})

    def test_defile(self):
        c = corpus({"gui.a": ("Go", "Commencer maintenant", "projet")})
        x = constats(c, [contrainte(cles=["gui.a"], comportement="défile (bouton vanilla)")])["gui.a"]
        self.assertEqual(x.statut, SIGNALE)

    def test_lignes(self):
        """lignes:2x60 : le français replié sur 60 px tient en deux lignes au plus."""
        trois, en_long = "Un texte bien trop long", "An English text too long"
        self.assertEqual(lignes(trois, 60), 3)
        c = corpus({"gui.a": ("A short text", trois, "projet"),
                    "gui.b": ("A short text", "Un texte court", "projet"),
                    "gui.c": (en_long, trois + " ici et la", "projet"),
                    "gui.d": (en_long, trois, "projet")})
        self.assertEqual((lignes(en_long, 60), lignes(trois + " ici et la", 60)), (3, 4))
        resultat = constats(c, [contrainte(60, "lignes:2x60", lignes=2, cles=["gui.a", "gui.b", "gui.c", "gui.d"])])
        self.assertEqual({k: x.statut for k, x in resultat.items()}, {"gui.a": BLOQUANT, "gui.c": SIGNALE})
        self.assertIn("3 lignes", resultat["gui.a"].detail)

    def test_un_constat_par_cle(self):
        """Une clé visée par deux contraintes, ou par la boutique et une contrainte : un constat, le plus grave."""
        c = corpus({"gui.a": ("Go", "Commencer maintenant", "jar")})
        resultat = CONTROLES["largeur"](c, None, Config(espace=Path("."), regles=dict(ACTIVE), largeurs=[
            contrainte(cles=["gui.a"], comportement="défile"), contrainte(cles=["gui.a"])]), Options())
        self.assertEqual([(x.cle, x.statut) for x in resultat], [("gui.a", BLOQUANT)])

    def test_francais_vide(self):
        c = corpus({"gui.a": ("Go", "", "projet")})
        self.assertEqual(constats(c, [contrainte(cles=["gui.a"])]), {})


if __name__ == "__main__":
    unittest.main()
