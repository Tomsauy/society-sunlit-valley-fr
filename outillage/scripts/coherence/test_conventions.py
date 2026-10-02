"""Typographie, registre, nommage des blocs, pourcentages."""
import unittest
from pathlib import Path

from coherence.config import Config
from coherence.controles import CONTROLES
from coherence.corpus import ChampLivre, Corpus
from coherence.modele import Options

LIGNES = {
    ("society", "aquaculture.hook.desc"): "Déclenche une alerte à l’approche",
    ("society", "item.society.egg"): "Œuf doré",
    ("society", "item.society.nbsp"): "Bien joué !",
    ("society", "item.society.axe.broken"): "Votre hache s'est brisée",
    ("society", "item.society.glass.view"): "Maintenez [%s] pour voir",
    ("society", "item.society.chez"): "Rends-toi chez le forgeron, c'est assez près",
    ("minecraft", "gui.x.vous"): "Voulez-vous quitter ?",
    ("society", "block.society.cask.no_skill"): "La compétence « Vieillissement » manque",
    ("ftbquestlocalizer", "ftbquests.chapter.a.quest1.description1"): "« Bienvenue » à la ferme",
    ("trials", "block.trials.tuff_stairs"): "Escalier de tuf",
    ("trials", "block.trials.brick_stairs"): "Escalier en briques",
    ("x", "block.x.oak_vertical_slab"): "Dalle verticale de chêne",
    ("x", "block.x.stone_slab"): "Dalle en pierre",
    ("x", "block.x.brick_wall"): "Muret en briques",
    ("x", "block.x.sconce_candle_wall"): "Applique murale",
    ("society", "tooltip.society.chance"): "25% de chance, 10 %% de bonus",
    ("society", "item.society.rdv"): "Tu as rendez-vous ?",
}


def constats(options=Options()):
    c = Corpus()
    for (ns, cle), fr in LIGNES.items():
        c.en[cle], c.fr[cle], c.origine_fr[cle], c.ns_projet[cle] = "x", fr, "projet", ns
    c.livres = [ChampLivre("almanac/e.json", "/text", "x", "Placez la graine", ())]
    return {(x.cle, x.objet) for x in CONTROLES["conventions"](c, None, Config(espace=Path(".")), options)}


class TestConventions(unittest.TestCase):

    def test_constats(self):
        self.assertEqual(constats(), {
            ("aquaculture.hook.desc", "apostrophe"), ("item.society.egg", "ligature"),
            ("item.society.nbsp", "insecable"), ("item.society.axe.broken", "vouvoiement"),
            ("item.society.glass.view", "vouvoiement"), ("block.society.cask.no_skill", "guillemets"),
            ("block.trials.tuff_stairs", "nommage"), ("block.x.stone_slab", "nommage"),
            ("block.x.brick_wall", "nommage"), ("almanac/e.json#/text", "vouvoiement")})

    def test_pourcentages_quand_la_regle_est_active(self):
        self.assertIn(("tooltip.society.chance", "pourcentage"), constats(Options(toutes_regles=True)))

    def test_pourcentage_apres_une_variable(self):
        """Fiche du 30/09 (pourcentages) : « 25 % » vaut aussi après une variable, « +%s %% »."""
        c = Corpus()
        for cle, fr in {"tooltip.society.variable": "+%s%% cases, %1$s%% et %d%%",
                        "tooltip.society.espacee": "%1$s %% pour 1 %%"}.items():
            c.en[cle], c.fr[cle], c.origine_fr[cle], c.ns_projet[cle] = "x", fr, "projet", "society"
        resultat = {(x.cle, x.objet) for x in CONTROLES["conventions"](c, None, Config(espace=Path(".")),
                                                                           Options(toutes_regles=True))}
        self.assertIn(("tooltip.society.variable", "pourcentage"), resultat)
        self.assertNotIn(("tooltip.society.espacee", "pourcentage"), resultat)

    def test_bandes_de_danger_de_railways(self):
        """Les bandes de danger de Railways : « Chevron X sur noir », « Bandes de danger X sur blanc » ; ni
        « sur fond » (32 noms sur 124), ni « Chevrons ». Le singulier de l'anglais est le choix de la
        contre-analyse (ligne 656), bien que minoritaire : 30 « Chevron » contre 32 « Chevrons »."""
        lignes = {"block.railways.ochrum_hazard_stripes_chevron_on_white": "Chevrons ochrum sur fond blanc",
                  "block.railways.royal_blue_hazard_stripes_diagonal_on_black":
                      "Bandes de danger bleu roi sur fond noir",
                  "block.railways.gray_hazard_stripes_chevron_on_black": "Chevrons gris sur noir",
                  "block.railways.blue_hazard_stripes_chevron_on_black": "Chevron bleu sur noir",
                  "block.railways.blue_hazard_stripes_diagonal_on_white": "Bandes de danger bleues sur blanc",
                  "block.railways.tuff_hazard_stripes_diagonal_on_black": "Bandes de danger tuf sur blanc",
                  # Sans préfixe de couleur, les blocs de locométal suivent la même forme (relecture de 2-05).
                  "block.railways.hazard_stripes_chevron_on_black": "Chevrons en locométal sur noir",
                  "block.railways.hazard_stripes_chevron_on_white": "Chevron en locométal sur blanc",
                  "block.railways.hazard_stripes_diagonal_on_white": "Bandes de danger en locométal sur fond blanc",
                  "block.railways.hazard_stripes_diagonal_on_black": "Bandes de danger en locométal sur noir"}
        c = Corpus()
        for cle, fr in lignes.items():
            c.en[cle], c.fr[cle], c.origine_fr[cle], c.ns_projet[cle] = "x", fr, "projet", "railways"
        resultat = {x.cle for x in CONTROLES["conventions"](c, None, Config(espace=Path(".")), Options())
                    if x.objet == "nommage"}
        self.assertEqual(resultat, {"block.railways.ochrum_hazard_stripes_chevron_on_white",
                                    "block.railways.royal_blue_hazard_stripes_diagonal_on_black",
                                    "block.railways.gray_hazard_stripes_chevron_on_black",
                                    "block.railways.tuff_hazard_stripes_diagonal_on_black",
                                    "block.railways.hazard_stripes_chevron_on_black",
                                    "block.railways.hazard_stripes_diagonal_on_white"})

    def test_dalles_de_bois_et_de_pierre(self):
        """Fiche du 30/09 (dalles) : une dalle dont la base a des planches est « en » son bois, ou prend l'adjectif
        des bois du Nether ; une autre dalle est « de » sa pierre."""
        lignes = {"block.x.poplar_planks": "Planches de peuplier", "block.x.poplar_slab": "Dalle de peuplier",
                  "block.x.laurel_planks": "Planches de laurier", "block.x.laurel_vertical_slab": "Dalle verticale en laurier",
                  "block.minecraft.crimson_planks": "Planches carmin", "block.x.crimson_slab": "Dalle carmin",
                  "block.x.tuff_slab": "Dalle de tuf", "block.x.cobble_slab": "Dalle en pierre"}
        c = Corpus()
        for cle, fr in lignes.items():
            c.en[cle], c.fr[cle], c.origine_fr[cle], c.ns_projet[cle] = "x", fr, "projet", "x"
        resultat = {x.cle for x in CONTROLES["conventions"](c, None, Config(espace=Path(".")), Options())
                    if x.objet == "nommage"}
        self.assertEqual(resultat, {"block.x.poplar_slab", "block.x.cobble_slab"})

    def test_insecable_fine(self):
        c = Corpus()
        cle = "item.society.fine"
        c.en[cle], c.fr[cle], c.origine_fr[cle], c.ns_projet[cle] = "x", "Bien joué !", "projet", "society"
        resultat = {(x.cle, x.objet) for x in CONTROLES["conventions"](c, None, Config(espace=Path(".")), Options())}
        self.assertEqual(resultat, {(cle, "insecable")})


if __name__ == "__main__":
    unittest.main()
