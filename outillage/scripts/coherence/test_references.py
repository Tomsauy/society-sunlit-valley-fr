"""Un texte qui cite un objet emploie son nom affiché."""
import unittest
from pathlib import Path

from coherence.config import Config
from coherence.controles import CONTROLES
from coherence.corpus import ChampLivre, Corpus, Quete, Tache
from coherence.modele import BLOQUANT, SIGNALE, Options
from coherence.registre import Registre

NOMS = {
    "block.society.crab_trap": ("Crab Trap", "Piège à crabes"),
    "item.society.shipping_bin": ("Shipping Bin", "Bac d'expédition"),
    "effect.society.drunk": ("Drunk", "Ivresse"),
    "item.aquaculture.tackle_box": ("Tackle Box", "Boîte à pêche"),
    "item.other.tackle_box": ("Tackle Box", "Coffre de pêche"),
    "item.society.crab_trap_bait": ("Crab Trap Bait", "Appât pour casier à crabes"),
}


def verifier(textes, exceptions=(), ns=None, **champs):
    corpus = Corpus()
    for cle, (en, fr) in {**NOMS, **textes}.items():
        corpus.en[cle], corpus.fr[cle], corpus.origine_fr[cle] = en, fr, "projet"
        corpus.ns_projet[cle] = cle.split(".")[1]
    corpus.ns_projet.update(ns or {})
    for nom, valeur in champs.items():
        setattr(corpus, nom, valeur)
    config = Config(espace=Path("."), exceptions=list(exceptions))
    return CONTROLES["references"](corpus, Registre(corpus, config), config, Options())


def de(constats, cle):
    return [c for c in constats if c.cle == cle]


class TestReferences(unittest.TestCase):

    def test_nom_repris_au_pluriel_dans_une_balise(self):
        c = verifier({"tooltip.society.bin": ("Place &6Shipping Bins&r here", "Place tes &6bacs d'expédition&r ici")})
        self.assertEqual(de(c, "tooltip.society.bin"), [])

    def test_nom_different_du_nom_affiche(self):
        (c,) = de(verifier({"tooltip.society.trap": ("Put bait in the Crab Trap",
                                                     "Mets de l'appât dans le casier à crabes")}), "tooltip.society.trap")
        self.assertEqual((c.attendu, c.objet, c.statut), ("Piège à crabes", "block.society.crab_trap", BLOQUANT))

    def test_faux_ami(self):
        (c,) = de(verifier({"item.society.wine.description": ("Gives the Drunk effect", "Donne l'effet Intoxication")}),
                  "item.society.wine.description")
        self.assertEqual(c.attendu, "Ivresse")

    def test_nom_qui_en_cite_un_autre(self):
        (c,) = de(verifier({}), "item.society.crab_trap_bait")
        self.assertEqual(c.objet, "block.society.crab_trap")

    def test_homonymes_departages_par_le_namespace(self):
        c = verifier({"tooltip.aquaculture.hint": ("Open the Tackle Box", "Ouvre la boîte à pêche")})
        self.assertEqual(de(c, "tooltip.aquaculture.hint"), [])

    def test_homonymes_sans_preuve(self):
        (c,) = de(verifier({"tooltip.society.hint": ("Open the Tackle Box", "Ouvre la boîte")}), "tooltip.society.hint")
        self.assertIn("ambiguë", c.detail)
        self.assertEqual(c.statut, BLOQUANT)

    def test_homonymes_departages_par_une_epingle(self):
        epingle = {"controle": "references", "cle": "tooltip.society.hint", "objet": "item.other.tackle_box",
                   "epingle": True, "motif": "le coffre du marchand"}
        (c,) = de(verifier({"tooltip.society.hint": ("Open the Tackle Box", "Ouvre la boîte")}, [epingle]),
                  "tooltip.society.hint")
        self.assertEqual(c.attendu, "Coffre de pêche")

    def test_epingle_garde_son_objet_quand_les_homonymes_sont_unifies(self):
        """Deux homonymes ramenés au même nom (fiche du 30/09, homonyme-farmland) : le texte attendu ne change pas,
        mais le constat nomme l'objet épinglé, que la dette et les exceptions connaissent, et l'épingle sert."""
        for epinglee in ("item.aquaculture.tackle_box", "item.other.tackle_box"):
            epingle = {"controle": "references", "cle": "tooltip.society.hint", "objet": epinglee,
                       "epingle": True, "motif": "m"}
            (c,) = de(verifier({"item.other.tackle_box": ("Tackle Box", "Boîte à pêche"),
                                "tooltip.society.hint": ("Open the Tackle Box", "Ouvre le coffre")}, [epingle]),
                      "tooltip.society.hint")
            self.assertEqual((c.statut, c.objet, c.attendu), (BLOQUANT, epinglee, "Boîte à pêche"))

    def test_epingle_inutilisee(self):
        epingle = {"controle": "references", "cle": "tooltip.society.bin", "objet": "item.other.tackle_box",
                   "epingle": True, "motif": "m"}
        c = de(verifier({"tooltip.society.bin": ("Place Shipping Bins", "Place tes bacs d'expédition")}, [epingle]),
               "tooltip.society.bin")
        self.assertEqual([x.statut for x in c], [SIGNALE])

    def test_lien_par_la_tache_de_quete(self):
        cle = "ftbquests.chapter.x.quest1.task.1.title"
        quete = Quete("1", "x", "", (cle,), (Tache(cle, ("other:tackle_box",)),))
        (c,) = de(verifier({cle: ("Any Tackle Box", "N'importe quelle boîte à pêche")}, quetes=[quete]), cle)
        self.assertEqual(c.attendu, "Coffre de pêche")

    def test_titre_de_tache_a_plusieurs_objets(self):
        """« Any hammer core » vise deux objets dont l'anglais partage « Core » : le titre reprend le mot qu'ils
        partagent en français ; s'ils n'en partagent aucun (« Petit noyau », « Coeur d'impact »), le constat le dit."""
        noms = {"item.justhammers.small_core": ("Small Core", "Petit noyau"),
                "item.justhammers.impact_core": ("Impact Core", "Coeur d'impact"),
                "item.x.oak_log": ("Oak Log", "Bûche de chêne"),
                "item.x.birch_log": ("Birch Log", "Bûche de bouleau"),
                "item.itemfilters.or": ("OR Filter", "Filtre OR")}
        coeurs, buches, bon = ("ftbquests.chapter.t.quest1.task.1.title", "ftbquests.chapter.t.quest2.task.2.title",
                               "ftbquests.chapter.t.quest3.task.3.title")
        quetes = [Quete("1", "t", "", (coeurs,), (Tache(coeurs, ("justhammers:small_core", "justhammers:impact_core",
                                                                  "itemfilters:or")),)),
                  Quete("2", "t", "", (buches,), (Tache(buches, ("x:oak_log", "x:birch_log")),)),
                  Quete("3", "t", "", (bon,), (Tache(bon, ("x:oak_log", "x:birch_log")),))]
        c = verifier({**noms, coeurs: ("Any hammer core", "N'importe quel noyau de marteau"),
                      buches: ("Any Log", "N'importe quel rondin"), bon: ("Any Log", "N'importe quelle bûche")},
                     quetes=quetes)
        (x,) = de(c, coeurs)
        self.assertIn("« Petit noyau »", x.detail)
        self.assertEqual([x.attendu for x in de(c, buches)], ["Bûche"])
        self.assertEqual(de(c, bon), [])

    def test_titre_de_tache_au_genre_pres(self):
        """« imitatrice » et « imitateur » sont le même mot : le genre suit le nom qu'il qualifie."""
        noms = {"block.copycats.copycat_beam": ("Copycat Beam", "Poutre imitatrice"),
                "block.copycats.copycat_block": ("Copycat Block", "Bloc imitateur")}
        cle = "ftbquests.chapter.t.quest1.task.1.title"
        quete = Quete("1", "t", "", (cle,), (Tache(cle, ("copycats:copycat_beam", "copycats:copycat_block")),))
        c = verifier({**noms, cle: ("Any copycat block", "N'importe quel bloc imitateur")}, quetes=[quete])
        self.assertEqual(de(c, cle), [])

    def test_lien_par_l_infobulle(self):
        c = verifier({"tooltip.society.box": ("Tackle Box contents", "Contenu du coffre de pêche")},
                     infobulles={"tooltip.society.box": {"other:tackle_box"}})
        self.assertEqual(de(c, "tooltip.society.box"), [])

    def test_lien_par_le_prefixe_de_cle(self):
        cle = "item.other.tackle_box.description"
        c = verifier({cle: ("A sturdy Tackle Box", "Un coffre de pêche solide")}, ns={cle: "society"})
        self.assertEqual(de(c, cle), [])

    def test_champ_de_livre(self):
        champ = ChampLivre("almanac/entries/x.json", "/pages/0/text", "Use the Tackle Box", "Utilise la boîte",
                           ("aquaculture:tackle_box",))
        (c,) = de(verifier({}, livres=[champ]), champ.cle)
        self.assertEqual(c.attendu, "Boîte à pêche")

    def test_accents_du_nom_cite(self):
        """Le nom se retrouve aux accents près, mais s'écrit avec les accents du nom affiché : « Gobie ambré »
        ne s'écrit pas comme « Gobie ambre », et la recherche « ambré » ne trouve pas le poisson."""
        noms = {"entity.fish.amber_goby": ("Amber Goby", "Gobie ambre"),
                "dialog.npc.selene.name": ("Selene", "Selene")}
        c = verifier({**noms,
                      "tooltip.fish.goby": ("Catch an Amber Goby", "Attrape un gobie ambré"),
                      "tooltip.fish.gobies": ("Amber Gobies swim here", "Les gobies ambres nagent ici"),
                      "tooltip.x.moon": ("The power of Selene", "Le pouvoir de Séléné"),
                      "tooltip.x.moon2": ("Selene's gift", "Le cadeau de SELENE")})
        (goby,) = de(c, "tooltip.fish.goby")
        self.assertEqual((goby.objet, goby.attendu), ("entity.fish.amber_goby", "Gobie ambre"))
        self.assertIn("« ambré »", goby.detail)
        self.assertEqual(de(c, "tooltip.fish.gobies"), [])  # pluriel et casse ne comptent pas
        self.assertEqual([x.objet for x in de(c, "tooltip.x.moon")], ["dialog.npc.selene.name"])
        self.assertEqual(de(c, "tooltip.x.moon2"), [])

    def test_accents_fautifs_selon_le_vocabulaire(self):
        """Quand l'un des deux mots est mal accentué selon le vocabulaire figé, l'écart n'est pas celui du texte
        cité : un nom affiché fautif (« Fenètre » d'un jar) ou un texte fautif (« Chaudiere », que le contrôle
        accents relève) ne font pas de constat de référence."""
        noms = {"block.vinery.window": ("Window", "Fenètre"),
                "block.railways.locometal_boiler": ("Locometal Boiler", "Chaudière en locométal")}
        corpus = Corpus()
        for cle, (en, fr) in {**noms,
                              "tooltip.x.window": ("Open the Window", "Ouvre la fenêtre"),
                              "block.railways.tuff_locometal_boiler": ("Tuff Locometal Boiler",
                                                                       "Chaudiere en locométal tuf")}.items():
            corpus.en[cle], corpus.fr[cle], corpus.origine_fr[cle] = en, fr, "projet"
            corpus.ns_projet[cle] = cle.split(".")[1]
        vocabulaire = {"fenetre": [{"forme": "fenêtre", "sens": "window"}],
                       "chaudiere": [{"forme": "chaudière", "sens": "boiler"}]}
        config = Config(espace=Path("."), vocabulaire=vocabulaire)
        self.assertEqual(CONTROLES["references"](corpus, Registre(corpus, config), config, Options()), [])

    def test_accents_fautifs_selon_un_double_sens(self):
        """Un mot à double sens que l'anglais du texte tranche (« Slashed » → « coupé ») relève du contrôle
        accents : « Locométal coupe » ne fait pas de constat de référence."""
        corpus = Corpus()
        for cle, (en, fr) in {"block.railways.slashed_locometal": ("Slashed Locometal", "Locométal coupé"),
                              "block.railways.tuff_slashed_locometal": ("Tuff Slashed Locometal",
                                                                        "Locométal coupe tuf")}.items():
            corpus.en[cle], corpus.fr[cle], corpus.origine_fr[cle] = en, fr, "projet"
            corpus.ns_projet[cle] = "railways"
        double_sens = [{"anglais": "slashed", "justes": ["coupé", "coupée"], "motif": "m"}]
        config = Config(espace=Path("."), double_sens=double_sens)
        self.assertEqual(CONTROLES["references"](corpus, Registre(corpus, config), config, Options()), [])

    def test_matiere_declaree_par_exception(self):
        """Spec 2 §7 : sans la règle « même mod », un matériau se déclare par une exception à objet, que le rapport
        applique (le contrôle, lui, relève toujours la citation)."""
        from coherence.rapport import appliquer
        textes = {"item.pam.cherry": ("Cherry", "Cerise"),
                  "block.x.cherry_planks": ("Cherry Planks", "Planches de cerisier")}
        exc = {"controle": "references", "cle": "block.x.cherry_planks", "objet": "item.pam.cherry",
               "motif": "matière : planches de cerisier, pas la cerise"}
        r = appliquer(verifier(textes), [exc], [], lambda cle: "", ("references",))
        self.assertEqual([x for x in r.bloquants if x.cle == "block.x.cherry_planks"], [])
        self.assertEqual([x.cle for x, _ in r.couverts], ["block.x.cherry_planks"])


class TestTitresDeFiches(unittest.TestCase):
    """Le titre d'une fiche de livre nomme ce qu'elle présente, même quand son anglais ne le cite pas."""

    def test_objet_qui_porte_le_nom_du_fichier(self):
        """L'anglais du titre a une coquille (« Dasmelfish ») : le fichier et l'objet lié désignent le poisson."""
        noms = {"entity.fish.duality_damselfish": ("Duality Damselfish", "Poisson-demoiselle de dualité")}
        faux = ChampLivre("fish_finder/entries/fish/duality_damselfish.json", "/name", "Duality Dasmelfish",
                          "Demoiselle de la dualité", ("fish:duality_damselfish", "fish:raw_duality_damselfish"))
        juste = ChampLivre("fish_finder/entries/fish/duality_damselfish.json", "/name", "Duality Dasmelfish",
                           "Poisson-demoiselle de dualité", ("fish:duality_damselfish",))
        (c,) = de(verifier(noms, livres=[faux]), faux.cle)
        self.assertEqual((c.objet, c.attendu), ("entity.fish.duality_damselfish", "Poisson-demoiselle de dualité"))
        self.assertEqual(de(verifier(noms, livres=[juste]), juste.cle), [])

    def test_arbre_de_la_pousse_liee(self):
        """Une fiche d'arbre (« … Tree ») nomme l'arbre de sa pousse (« Pousse alpine » : l'arbre alpin)."""
        noms = {"block.meadow.pine_sapling": ("Alpine Sapling", "Pousse alpine"),
                "block.vinery.dark_cherry_sapling": ("Dark Cherry Sapling", "Pousse de cerisier noir")}
        pin = ChampLivre("almanac/entries/trees/letsdo/pine.json", "/name", "Pine Tree 🌐", "Pin 🌐",
                         ("meadow:pine_sapling",))
        alpin = ChampLivre("almanac/entries/trees/letsdo/pine2.json", "/name", "Pine Tree 🌐", "Arbre alpin 🌐",
                           ("meadow:pine_sapling",))
        cerisier = ChampLivre("almanac/entries/trees/letsdo/darkcherry.json", "/name", "Darkcherry Tree 🌼",
                              "Cerisier sombre 🌼", ("vinery:dark_cherry_sapling",))
        c = verifier(noms, livres=[pin, alpin, cerisier])
        self.assertEqual([x.attendu for x in de(c, pin.cle)], ["alpine"])
        self.assertEqual(de(c, alpin.cle), [])  # « alpin » : le genre de l'arbre n'est pas celui de la pousse
        self.assertEqual([x.attendu for x in de(c, cerisier.cle)], ["cerisier noir"])

    def test_ce_que_la_fiche_ne_presente_pas(self):
        """Pas de constat : l'animal d'une fiche qui partage son identifiant avec sa viande, une catégorie
        (« Trees »), une pousse à la faute connue (« pallisandre »), un titre dont la citation est déjà relevée."""
        noms = {"item.minecraft.chicken": ("Raw Chicken", "Poulet cru"),
                "entity.minecraft.chicken": ("Chicken", "Poule"),
                "block.pam.apple_sapling": ("Apple Sapling", "Pousse de pommier"),
                "block.atmo.rosewood_sapling": ("Rosewood Sapling", "Pousse de pallisandre"),
                "block.atmo.grimwood": ("Grimwood", "Bois de sombrepin"),
                "block.atmo.grimwood_sapling": ("Grimwood Sapling", "Pousse de sombrepin")}
        champs = [ChampLivre("almanac/entries/animals/chicken.json", "/name", "Chicken", "Poule",
                             ("minecraft:chicken",)),
                  ChampLivre("almanac/categories/trees.json", "/name", "Trees", "Arbres", ("pam:apple_sapling",)),
                  ChampLivre("almanac/entries/trees/rosewood.json", "/name", "Rosewood Tree", "Palissandre",
                             ("atmo:rosewood_sapling",)),
                  ChampLivre("almanac/entries/trees/grimwood.json", "/name", "Grimwood Tree", "Arbre grimwood",
                             ("atmo:grimwood_sapling",))]
        corpus = Corpus()
        for cle, (en, fr) in noms.items():
            corpus.en[cle], corpus.fr[cle], corpus.origine_fr[cle] = en, fr, "projet"
            corpus.ns_projet[cle] = cle.split(".")[1]
        corpus.livres = champs
        config = Config(espace=Path("."), formes_interdites=[{"forme": "pallisandre", "juste": "palissandre"}])
        c = CONTROLES["references"](corpus, Registre(corpus, config), config, Options())
        self.assertEqual([(x.cle, x.objet) for x in c if "#" in x.cle], [(champs[3].cle, "block.atmo.grimwood")])

    def test_forme_interdite_sensible_a_la_casse(self):
        """Comme le contrôle orthographe, la correction du nom de la pousse respecte le drapeau « casse » d'une
        forme interdite : « Alpine » (casse exacte) ne touche pas « Pousse alpine »."""
        corpus, cle = Corpus(), "block.meadow.pine_sapling"
        corpus.en[cle], corpus.fr[cle], corpus.origine_fr[cle], corpus.ns_projet[cle] = \
            "Alpine Sapling", "Pousse alpine", "projet", "meadow"
        corpus.livres = [ChampLivre("almanac/entries/trees/letsdo/pine.json", "/name", "Pine Tree 🌐", "Arbre alpin 🌐",
                                    ("meadow:pine_sapling",))]
        config = Config(espace=Path("."), formes_interdites=[{"forme": "Alpine", "juste": "Alpestre", "casse": True}])
        self.assertEqual(CONTROLES["references"](corpus, Registre(corpus, config), config, Options()), [])

    def test_nom_a_gabarit_rempli_du_titre(self):
        """« %s Slime » s'affiche « Slime %s » : la page « Ender Slime » de la fiche « Ender » s'écrit
        « Slime Ender »."""
        noms = {"entity.slimes.splendid_slime": ("%s Slime", "Slime %s")}
        titre = ChampLivre("almanac/entries/slimes/ender.json", "/name", "Ender", "Ender", ("slimes:splendid_slime",))
        page = ChampLivre("almanac/entries/slimes/ender.json", "/pages/1/name", "Ender Slime", "Slime de l'Ender",
                          ("slimes:splendid_slime",))
        ours = ChampLivre("almanac/entries/slimes/bear.json", "/name", "Bear", "Ours", ("slimes:splendid_slime",))
        page_ours = ChampLivre("almanac/entries/slimes/bear.json", "/pages/1/name", "Bear Slime", "Slime ours",
                               ("slimes:splendid_slime",))
        c = verifier(noms, livres=[titre, page, ours, page_ours])
        self.assertEqual([x.attendu for x in de(c, page.cle)], ["Slime Ender"])
        self.assertEqual(de(c, page_ours.cle), [])


class TestCitations(unittest.TestCase):
    """Ce qui compte comme citation : noms d'un mot, noms composés, gabarits."""

    def test_nom_d_origine_d_un_objet_renomme(self):
        """Un objet renommé par le pack garde son identifiant : l'anglais resté sur l'ancien nom (« Growth
        Totem », « Jumping Spider Spawn Egg », l'effet « Drunk ») le cite encore."""
        noms = {"block.arch.growth_totem": ("Totem of Glowth", "Totem de luissance"),
                "item.critters.jumping_spider_spawn_egg": ("Jumping Spider Spawn Crate",
                                                           "Caisse d'apparition d'araignée sauteuse"),
                "effect.brewery.drunk": ("Intoxication", "Ivresse"),
                "item.x.spider_eye": ("Spider Eye", "Oeil d'araignée"),
                "block.y.spider_eye": ("Eye Block", "Bloc d'oeil"),  # « Spider Eye » est l'anglais d'un autre objet
                "item.x.redstone": ("Redstone Dust", "Poudre de redstone")}  # un seul mot : pas d'alias hors effet
        c = verifier({**noms,
                      "tooltip.x.moo": ("Forage: Growth Totem (5% chance)", "Cueillette : Totem de croissance"),
                      "tooltip.x.ferret": ("Gifts: Jumping Spider Spawn Egg", "Cadeaux : Oeuf d'araignée sauteuse"),
                      "tooltip.x.slime": ("Causes Drunk effect when upset", "Provoque l'effet Intoxication"),
                      "tooltip.x.wire": ("Emits a Redstone signal", "Émet un signal de redstone"),
                      "tooltip.x.eye": ("Drop a Spider Eye", "Lâche un oeil d'araignée")})
        self.assertEqual([x.attendu for x in de(c, "tooltip.x.moo")], ["Totem de luissance"])
        self.assertEqual([x.objet for x in de(c, "tooltip.x.ferret")], ["item.critters.jumping_spider_spawn_egg"])
        self.assertEqual([x.attendu for x in de(c, "tooltip.x.slime")], ["Ivresse"])
        self.assertEqual(de(c, "tooltip.x.wire"), [])
        self.assertEqual(de(c, "tooltip.x.eye"), [])

    def test_nom_commun_d_une_famille(self):
        """« Sewing Needle » n'est aucun objet, mais la fin commune de plusieurs (« Iron Sewing Needle »…) : un
        texte lié à l'un d'eux, ou l'étiquette d'un groupe d'objets (stackgroup), le traduit par leur début commun,
        « Aiguille de couture »."""
        noms = {"item.sewingkit.iron_sewing_needle": ("Iron Sewing Needle", "Aiguille de couture en fer"),
                "item.sewingkit.gold_sewing_needle": ("Gold Sewing Needle", "Aiguille de couture en or"),
                "item.minecraft.angler_pottery_sherd": ("Angler Pottery Sherd", "Tesson de poterie de pêcheur"),
                "item.minecraft.archer_pottery_sherd": ("Archer Pottery Sherd", "Tesson de poterie d'archer"),
                "item.x.removed_a_market": ("REMOVED! Buy seeds from the Market!", "SUPPRIMÉ ! Au Marché !"),
                "item.x.removed_b_market": ("REMOVED! Buy bulbs from the Market!", "SUPPRIMÉ ! Au Marché !")}
        textes = {"quest.x.needle": ("It requires a &6Sewing Needle&r to craft.",
                                     "Elle nécessite une &6aiguille à coudre&r pour être fabriquée."),
                  "quest.x.ok": ("It requires a Sewing Needle", "Il faut une aiguille de couture"),
                  "quest.x.iron": ("Craft an Iron Sewing Needle", "Fabrique une aiguille de couture en fer"),
                  "quest.x.libre": ("Any Sewing Needle will do", "N'importe quelle aiguille fera l'affaire"),
                  "quest.x.market": ("Sold at the Market", "Vendu au marché"),
                  "stackgroup.remi.sherds": ("Pottery Sherds", "Éclats de poterie")}
        lies = {cle: {"sewingkit:iron_sewing_needle"} for cle in ("quest.x.needle", "quest.x.ok", "quest.x.iron")}
        lies["quest.x.market"] = {"x:removed_a_market"}
        c = verifier({**noms, **textes}, infobulles=lies)
        (aiguille,) = de(c, "quest.x.needle")
        self.assertEqual(aiguille.attendu, "Aiguille de couture")
        self.assertEqual(de(c, "quest.x.ok") + de(c, "quest.x.iron"), [])
        self.assertEqual(de(c, "quest.x.libre"), [])   # aucun lien : « Sewing Needle » peut désigner autre chose
        self.assertEqual(de(c, "quest.x.market"), [])  # « the Market » : une fin qui n'est pas un nom
        self.assertEqual([x.attendu for x in de(c, "stackgroup.remi.sherds")], ["Tesson de poterie"])

    def test_coordination_a_ellipse(self):
        """« Umbra or Highland Wool » cite « Umbra Wool » autant que « Highland Wool ». Deux mots avant la
        conjonction se tentent avant un : « Dark Oak and Birch Planks » cite « Dark Oak Planks », pas « Oak
        Planks » (vanilla), et « planches de chêne » sans « noir » ne passe pas."""
        noms = {"block.meadow.umbra_wool": ("Umbra Wool", "Laine d'ombre"),
                "block.meadow.highland_wool": ("Highland Wool", "Laine des Highlands"),
                "block.minecraft.oak_planks": ("Oak Planks", "Planches de chêne"),
                "block.x.dark_oak_planks": ("Dark Oak Planks", "Planches de chêne noir"),
                "block.x.birch_planks": ("Birch Planks", "Planches de bouleau")}
        c = verifier({**noms,
                      "tooltip.x.cow": ("Drops: Umbra or Highland Wool", "Butin : Laine umbra ou Laine des Highlands"),
                      "tooltip.x.ok": ("Drops: Umbra or Highland Wool",
                                       "Butin : Laine d'ombre ou Laine des Highlands"),
                      "tooltip.x.wood": ("Use Dark Oak and Birch Planks",
                                         "Utilise des planches de chêne et des planches de bouleau")})
        self.assertEqual([x.attendu for x in de(c, "tooltip.x.cow")], ["Laine d'ombre"])
        self.assertEqual(de(c, "tooltip.x.ok"), [])
        self.assertEqual([x.attendu for x in de(c, "tooltip.x.wood")], ["Planches de chêne noir"])

    def test_nom_d_origine_qui_n_en_est_pas_un(self):
        """Un identifiant qui n'est qu'un nom interne ne cite rien : une partie d'un nom anglais (« fence_gate »
        d'une barrière enneigée, « willow_door » de « Mystic Willow Door »), l'anglais au pluriel, au possessif
        ou avec un trait d'union (« Gearo Berries », « Dolphin's Grace », « Tri-bull »), un effet hors de
        « l'effet X » (« Weather: Clear »), un objet retiré (« REMOVED »)."""
        noms = {"block.snow.fence_gate": ("Snow-Covered Fence Gate", "Portillon enneigé"),
                "block.x.oak_fence_gate": ("Oak Fence Gate", "Portillon en chêne"),
                "block.cluttered.willow_door": ("Mystic Willow Door", "Porte en saule mystique"),
                "item.vd.gearo_berry": ("Gearo Berries", "Baies gearo"),
                "effect.minecraft.dolphins_grace": ("Dolphin's Grace", "Grâce du dauphin"),
                "block.farmlife.tribull_cheese_wheel": ("Tri-bull Cheese Wheel", "Meule de fromage de Tri-bull"),
                "effect.botania.clear": ("Absolution", "Absolution"),
                "item.ffb.red_fertilizer": ("REMOVED - Craft into new fertilizer", "SUPPRIMÉ - à recycler")}
        c = verifier({**noms,
                      "tooltip.x.gate": ("Open the Oak Fence Gate", "Ouvre le portillon en chêne"),
                      "tooltip.x.door": ("A Willow Door", "Une porte en saule"),
                      "tooltip.x.berries": ("Gearo Berries grow here", "Des baies gearo poussent ici"),
                      "tooltip.x.dolphin": ("Grants Dolphins Grace", "Donne la grâce du dauphin"),
                      "tooltip.x.cheese": ("A Tribull Cheese Wheel", "Une meule de tri-bull"),
                      "tooltip.x.weather": ("Weather: Clear", "Météo : dégagée"),
                      "tooltip.x.farm": ("Use Red Fertilizer", "Utilise l'engrais rouge")})
        self.assertEqual([x for x in c if x.cle.startswith("tooltip.")], [])

    def test_mot_courant_en_minuscules(self):
        """Spec §6 et §14 : un nom d'un seul mot reste cité quand l'anglais l'écrit en minuscules, même souvent — pas
        d'assouplissement global. Un mot courant se déclare dans mots_generiques.json, avec son motif."""
        courants = {f"tooltip.x.l{i}": (f"Some light here {i}", f"Un peu de clarté {i}") for i in range(10)}
        noms = {"block.x.light": ("Light", "Lumière")}
        textes = {**courants, **noms, "tooltip.x.maj": ("Place a Light here", "Pose une lampe ici")}
        self.assertEqual(sorted(x.cle for x in verifier(textes) if x.objet == "block.x.light"),
                         sorted([*courants, "tooltip.x.maj"]))
        corpus = Corpus()
        for cle, (en, fr) in textes.items():
            corpus.en[cle], corpus.fr[cle], corpus.origine_fr[cle] = en, fr, "projet"
        config = Config(espace=Path("."), mots_generiques={"Light": "adjectif et nom courants"})
        self.assertEqual(CONTROLES["references"](corpus, Registre(corpus, config), config, Options()), [])

    def test_mot_rare_en_minuscules(self):
        (c,) = de(verifier({"tooltip.x.bu": ("Gives the drunk effect", "Donne l'effet Intoxication")}), "tooltip.x.bu")
        self.assertEqual(c.attendu, "Ivresse")

    def test_nom_d_un_mot_dans_un_nom(self):
        c = verifier({"item.pam.cherry": ("Cherry", "Cerise"),
                      "block.x.cherry_planks": ("Cherry Planks", "Planches de cerisier"),
                      "item.bakery.donut": ("Donut", "Beignet"),
                      "item.bakery.chocolate_donut": ("Chocolate Donut", "Donut au chocolat")},
                     ns={"item.bakery.chocolate_donut": "society"})  # surchargé dans le fichier de society
        self.assertEqual([x.attendu for x in de(c, "block.x.cherry_planks")], ["Cerise"])  # spec 2 §7 : cité
        self.assertEqual([x.attendu for x in de(c, "item.bakery.chocolate_donut")], ["Beignet"])

    def test_mots_separes_dans_un_nom_compose(self):
        c = verifier({"block.x.oak_door": ("Oak Door", "Porte en chêne"),
                      "block.x.tall_oak_door": ("Tall Oak Door", "Grande porte en bois de chêne")})
        self.assertEqual(de(c, "block.x.tall_oak_door"), [])

    def test_gabarits_ignores(self):
        c = verifier({"block.x.cupboard": ("Cupboard", "Armoire"),
                      "block_type.everycomp.cupboard": ("%s Cupboard", "Placard en %s")})
        self.assertEqual(de(c, "block_type.everycomp.cupboard"), [])

    def test_couleurs_claires_de_minecraft(self):
        """« Light Blue » et « Light Gray » sont deux des seize couleurs de teinture : « Light Blue Bath » ne
        cite pas « Blue Bath »."""
        c = verifier({"block.x.blue_bath": ("Blue Bath", "Baignoire bleue"),
                      "block.x.light_blue_bath": ("Light Blue Bath", "Baignoire bleu clair"),
                      "block.x.gray_lamp": ("Gray Lamp", "Lampe grise"),
                      "tooltip.x.lamp": ("Place a Light Gray Lamp", "Pose une lampe gris clair"),
                      "tooltip.x.bath": ("Place a Blue Bath", "Pose une baignoire bleu clair")})
        self.assertEqual(de(c, "block.x.light_blue_bath"), [])
        self.assertEqual(de(c, "tooltip.x.lamp"), [])
        self.assertEqual([x.objet for x in de(c, "tooltip.x.bath")], ["block.x.blue_bath"])  # la couleur seule reste citée

    def test_derives_que_mojang_renomme(self):
        """Mojang nomme Fence Gate, Glass Pane et Rose Bush d'un autre nom que leur base (Portillon, Vitre,
        Rosier) : « Oak Fence Gate » ne cite pas « Oak Fence », ni « Arid Glass Pane » « Arid Glass »."""
        c = verifier({"block.x.oak_fence": ("Oak Fence", "Barrière en chêne"),
                      "block.x.oak_fence_gate": ("Oak Fence Gate", "Portillon en chêne"),
                      "block.x.arid_glass": ("Arid Glass", "Verre aride"),
                      "block.x.arid_glass_pane": ("Arid Glass Pane", "Vitre aride"),
                      "block.x.alabaster_window": ("Alabaster Window", "Fenêtre en albâtre"),
                      "block.x.alabaster_window_pane": ("Alabaster Window Pane", "Vitre en albâtre"),
                      "block.x.red_rose": ("Red Rose", "Rose rouge"),
                      "block.x.red_rose_bush": ("Red Rose Bush", "Rosier rouge"),
                      "tooltip.x.fence": ("Jump over the Oak Fence", "Saute la palissade")})
        self.assertEqual([x.cle for x in c if x.cle.startswith("block.")], [])
        self.assertEqual([x.objet for x in de(c, "tooltip.x.fence")], ["block.x.oak_fence"])  # la base reste citée


if __name__ == "__main__":
    unittest.main()
