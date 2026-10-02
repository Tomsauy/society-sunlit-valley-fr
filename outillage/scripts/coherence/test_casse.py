"""Majuscules internes des noms, majuscules en corps de phrase."""
import unittest
from pathlib import Path

from coherence.config import Config
from coherence.controles import CONTROLES, casse
from coherence.corpus import Corpus
from coherence.modele import BLOQUANT, Options
from coherence.registre import Registre

TEXTES = {
    "block.betterarcheology.chicken_fossil": ("Chicken Fossil", "Fossile de Poulet", "jar"),
    "block.x.cauliflower_seeds": ("Cauliflower Seeds", "Graines de chou-Fleur", "projet"),
    "item.society.aegis_wine": ("Aegis Wine", "Vin Aegis", "projet"),
    "item.x.tnt_minecart": ("Minecart with TNT", "Wagonnet avec TNT", "projet"),
    "item.x.ray": ("X-Ray Glass", "Verre à rayon X", "projet"),
    "item.society.blueprint": ("Blueprint", "Plans", "projet"),
    "item.society.sparkstone": ("Sparkstone", "Sparkstone", "projet"),
    "dialog.npc.banker.name": ("Caroline", "Caroline", "projet"),
    "ftbquests.chapter.a.quest1.description1": ("x", "Les &6Plans&r servent. Achète des Plans utiles. Parle à Caroline.",
                                                "projet"),
    "block.society.auto_grabber.description.fuel": ("Requires Sparkstone", "Nécessite de la Sparkstone", "projet"),
    "tooltip.x.liste": ("x", "$(li)Plans et Sparkstone : Plans", "projet"),
    "biome.minecraft.end_barrens": ("End Barrens", "Terres stériles de l'End", "vanilla"),
    "block.x.tarrey_sign": ("Tarrey Town Sign", "Panneau de Tarrey Town", "projet"),
    "dialog.npc.blueprints.name": ("Blueprints", "Plans", "projet"),
    "tooltip.x.vin": ("x", "Un verre de vin Aegis", "projet"),
    "tooltip.x.gadget": ("x", "Il faut un gadget &6Copier-Coller&r", "projet"),
    "item.x.copy_paste": ("Copy-Paste Gadget", "Gadget copier-coller", "projet"),
    "ftbquests.chapter.a.quest2.title": ("x", "Villageois Pêcheur invité", "projet"),
    "shop.society_trading.banker": ("Banker", "Banquier", "projet"),
    "ftbquests.chapter.a.quest3.description1": ("x", "Il est vendu par le villageois &6Banquier&r.", "projet"),
}


def corpus_de(textes) -> Corpus:
    c = Corpus()
    for cle, (en, fr, origine) in textes.items():
        c.en[cle], c.fr[cle], c.origine_fr[cle] = en, fr, origine
    return c


def constats(options=Options(), textes=None, noms_propres=None, **donnees):
    c = corpus_de(textes or TEXTES)
    config = Config(espace=Path("."), noms_propres=noms_propres or {"Aegis": "nom inventé (vin de Vinery)"},
                    provenance={"cles": {}, "glossaire": [{"en": "Tarrey Town", "fr": "Tarrey Town",
                                                           "garde_anglais": True}]}, **donnees)
    return {x.cle: x for x in CONTROLES["casse"](c, Registre(c, config), config, options)}


# Majuscules légitimes ailleurs qu'au premier caractère : le premier mot après un code ou un symbole de tête, un
# mot qui ouvre une phrase, une citation, ou un segment après une numérotation ou un intitulé en capitales suivis
# d'un tiret espacé. Après deux-points ou parenthèse, la minuscule reste de règle.
OUVERTURES = {
    "biome.x.desert_caves": (":pick: Desert Caves", ":pick: Grottes du désert", "projet"),
    "biome.x.frozen_caves": (" :pick: Frozen Caves", " :pick: Grottes gelées", "projet"),
    "item.x.galaxy_sword": ("<ltcolor>c=AA0000;w=10;p=2;Galaxy Sword</ltcolor>",
                            "<ltcolor>c=AA0000;w=10;p=2;Épée galactique</ltcolor>", "projet"),
    "block.x.modern_catalog": ("♧ Modern Catalog", "♧ Catalogue moderne", "projet"),
    "block.x.carrots": ("REMOVED! Purchase Carrot seeds from Market!",
                        "SUPPRIMÉ ! Acheter des graines de carotte au Marché !", "projet"),
    "block.x.fertilized_farmland": ("REMOVED - No longer functions. Break for new fertilizer!",
                                    "SUPPRIMÉ - Ne fonctionne plus. Casser pour un nouvel engrais !", "projet"),
    "ftbquests.chapter.x.title": ("I - Getting Started", "I - Premiers pas", "projet"),
    "block.x.no_solicitors": ("'No Solicitors!' Sign", 'Panneau "Pas de démarchage !"', "projet"),
    "block.x.bottle": ("A Bottle of 'Red Dawn'", "Une bouteille de 'Rouge aurore'", "jar"),
    "ftbquests.chapter.x.quest1.subtitle": ("Reward: Neptunium-Infused Hook",
                                             "Récompense : Hameçon infusé au neptunium", "projet"),
    "item.x.infinity_upgrade": ("Infinity Upgrade (Admin)", "Amélioration infinie (Admin)", "jar"),
    "item.x.iron_brush": ("Iron Brush", "Brosse en Fer", "jar"),
}

# Le tiret espacé n'ouvre un segment qu'après une numérotation (« I - », « Palier III - », « IV.II - ») ou un
# intitulé en capitales (« SUPPRIMÉ - », « FE - »). Après un nom commun, le mot qui suit reste vérifié : ces données ne
# déclarant aucun métier, « Forgeron » de « Maison de villageois - Forgeron » reste relevé (un métier déclaré garderait
# sa majuscule : voir METIERS).
TIRETS = {
    "ftbquests.loot_table.1.title": ("Villager Home - Blacksmith", "Maison de villageois - Forgeron", "projet"),
    "ftbquests.chapter.x.quest2.title": ("Layer III - The Deep Desert", "Palier III - Le désert enfoui", "projet"),
    "ftbquests.chapter.y.title": ("IV.II - Mystical Farming", "IV.II - Agriculture mystique", "projet"),
    "ftbquests.chapter.x.quest3.subtitle": ("FE - Furniture Energy", "FE - Fourniture d'énergie", "projet"),
    "item.x.green_fertilizer": ("REMOVED - Craft into new fertilizer", "SUPPRIMÉ - Transformer en nouvel engrais",
                                "projet"),
}

# STYLE §7 : « Maîtrise » suivie de son domaine est le nom propre d'un talent ; ailleurs, la minuscule.
MAITRISES = {
    "ftbquests.chapter.x.quest4.task.1.title": ("Unlock Fishing Mastery", "Débloque la Maîtrise de la pêche",
                                                "projet"),
    "ftbquests.chapter.x.quest5.task.1.title": ("Unlock Mining Mastery", "Débloque la Maîtrise du minage", "projet"),
    "ftbquests.chapter.x.quest6.task.1.title": ("Unlock Husbandry Mastery", "Débloque la Maîtrise de l'élevage",
                                                "projet"),
    "item.x.mastery_book": ("Mastery Book", "Livre de Maîtrise", "projet"),
}

# Un nom propre de plusieurs mots n'est exempté que là où il figure en entier ; un mot seul, partout.
EXPRESSIONS = {
    "block.x.teleporter": ("Skull Cavern Teleporter", "Téléporteur de la Caverne du Crâne", "projet"),
    "biome.x.skull_caves": ("Skull Caves", "Grottes du Crâne", "projet"),
    "item.x.cavern_map": ("Cavern Map", "Carte de la Caverne", "projet"),
    "block.x.tribull_cheese": ("Tri-bull Cheese Wheel", "Meule de fromage de Tri-bull", "projet"),
    "item.x.aegis_wine": ("Aged Aegis Wine", "Vin Aegis vieilli", "projet"),
    "block.x.oak_sign": ("Wise Oak Sign", "Panneau du Chêne sage", "projet"),
    "block.x.oak_planks": ("Oak Planks", "Planches de Chêne", "projet"),
    "dialog.npc.wise_oak.name": ("Wise Oak", "Chêne sage", "projet"),
}


# Le titre d'un livre de compétence (item.society.<id> décrit par society_skills.books.<id>) est un titre d'œuvre :
# après l'article, le premier nom prend la majuscule (« La Qualité de la terre ») ; ce n'est pas une majuscule interne.
LIVRES = {
    "item.society.the_quality_of_the_earth": ("The Quality Of The Earth", "La Qualité de la terre", "projet"),
    "society_skills.books.the_quality_of_the_earth.description": ("x", "y", "projet"),
    "item.society.phenomenology_of_treasure": ("The Phenomenology of Treasure", "La phénoménologie du trésor",
                                               "projet"),
    "society_skills.books.phenomenology_of_treasure.description": ("x", "y", "projet"),
    "item.society.the_spark_also_rises": ("The Spark Also Rises", "La Sparkstone se lève aussi", "projet"),
    "society_skills.books.the_spark_also_rises.description": ("x", "y", "projet"),
    "item.society.canadian_and_famous": ("Canadian And Famous", "Canadien et célèbre", "projet"),
    "society_skills.books.canadian_and_famous.description": ("x", "y", "projet"),
    "item.x.the_box": ("The Box", "La boîte", "projet"),
}


# Règle en attente (casse_textes) : le terme générique d'un toponyme reste en minuscule devant « de/du/des » et un
# nom propre, en corps de phrase ; pas en début de phrase ou d'élément de liste, ni dans un nom propre déclaré ou un
# nom du registre.
TOPONYMES = {
    "dialog.npc.trader.a": ("x", "Je parie que tu adorerais les Grottes de Camuy !", "projet"),
    "dialog.npc.trader.b": ("x", "Je parie que tu adorerais les grottes de Camuy !", "projet"),
    "dialog.npc.trader.c": ("x", "Quel voyage. Lac d'Annecy, puis la Mer du Nord.", "projet"),
    "tooltip.x.liste": ("x", "$(li)Forêt de Brocéliande$(li)Île de Sein", "projet"),
    "tooltip.x.crane": ("x", "Au fond de la Caverne du Crâne.", "projet"),
    "tooltip.x.roche": ("x", "Elle vit dans une sorte d'Océan de Roche... ?", "projet"),
    "tooltip.x.biome": ("x", "Traverse la Forêt de Cendre au nord.", "projet"),
    "biome.x.ash_forest": ("Ash Forest", "Forêt de Cendre", "projet"),
    "tooltip.x.commun": ("x", "Une Forêt de bouleaux borde la ferme.", "projet"),
}


# Décision du 29/09/2026 (STYLE §2) : les métiers des villageois (noms affichés des clés entity.minecraft.villager.<id>
# et entity.minecraft.villager.<mod>.<id>) et les boutiques (shop.society_trading.<id>, sans suffixe), tirés des
# données, se traitent comme des noms de personnes : leur majuscule est acceptée dans un nom, un titre ou une phrase ;
# un nom de plusieurs mots, là seulement où il figure en entier. La minuscule n'est pas imposée (« un pêcheur »).
METIERS = {
    "entity.minecraft.villager": ("Living Gnome", "Gnome vivant", "projet"),
    "entity.minecraft.villager.fisherman": ("Fisherman", "Pêcheur", "projet"),
    "entity.minecraft.villager.shepherd": ("Shepherd", "Berger", "projet"),
    "entity.minecraft.villager.armorer": ("Armorer", "Armurier", "vanilla"),
    "entity.minecraft.villager.fletcher": ("Exotic Trader", "Marchand exotique", "projet"),
    "entity.minecraft.villager.brewery.brewer": ("Brewmaster", "Maître brasseur", "projet"),
    "shop.society_trading.market": ("Market", "Marché", "projet"),
    "shop.society_trading.market.description": ("Sells seeds", "Vend des graines", "projet"),
    "shop.society_trading.building_shop.market": ("Market Home", "Maison du marché", "projet"),
    "shop.society_trading.trader": ("Trader", "Marchand", "projet"),
    "shop.society_trading.invitations": ("Invitations", "Invitations", "projet"),
    "ftbquests.chapter.a.quest1.task.1.title": ("x", "Villageois Pêcheur invité", "projet"),
    "ftbquests.loot_table.1.title": ("Villager Home - Shepherd", "Maison de villageois - Berger", "projet"),
    "block.x.carrots": ("x", "SUPPRIMÉ ! Acheter des graines de carotte au Marché !", "projet"),
    "ftbquests.chapter.a.quest2.title": ("x", "Invite le Marchand exotique", "projet"),
    "ftbquests.chapter.a.quest3.title": ("x", "Invite le Marchand Exotique", "projet"),
    "ftbquests.chapter.a.quest4.title": ("x", "Un pêcheur au Marché", "projet"),
    "item.x.crown": ("Crown of the Raider Master", "Couronne du Maître Pillard", "projet"),
    "block.betterarcheology.chicken_fossil": ("Chicken Fossil", "Fossile de Poulet", "jar"),
    "ftbquests.chapter.a.quest5.description1": ("x", "Achète des graines au Marché, puis parle au Marchand.", "projet"),
    "ftbquests.chapter.a.quest6.description1": ("x", "Le Maître brasseur passe par le Marché.", "projet"),
    # une boutique n'est pas un nom d'objet : son nom ne désigne pas l'objet « Invitation du charpentier »
    "ftbquests.chapter.a.quest7.description1": ("x", "Fabrique une Invitation du charpentier.", "projet"),
}

# Décision du 29/09/2026 (STYLE §2) : « Slime » et « Slimes », déclarés dans majuscules.json que casse lit seul, gardent
# leur majuscule partout, comme une personne. Les autres créatures restent en minuscules ; la minuscule des noms de
# Mojang (« Boule de slime ») n'est ni relevée ni imposée ailleurs.
SLIMES = {
    "entity.minecraft.slime": ("Slime", "Slime", "vanilla"),
    "item.minecraft.slime_ball": ("Slimeball", "Boule de slime", "vanilla"),
    "ftbquests.chapter.slimes.quest1.subtitle": ("x", "Coeur de Slime fabricable", "projet"),
    "ftbquests.chapter.slimes.quest2.title": ("x", "Collection de Slimes terminée !", "projet"),
    "item.quark.slime_in_a_bucket": ("Slime in a Bucket", "Seau de Slime", "jar"),
    "item.x.slime_candy": ("Slime Candy", "Bonbon de slime", "projet"),
    "block.betterarcheology.chicken_fossil": ("Chicken Fossil", "Fossile de Poulet", "jar"),
    "ftbquests.chapter.slimes.quest3.description1": ("x", "Tu peux nourrir les Slimes avec une boule de slime.",
                                                     "projet"),
}

# Précision du 29/09/2026 (STYLE §2) : dans un nom d'objet, un métier ou une boutique placé juste après « de », « du »,
# « des » ou « d' » est un nom commun (« Chapeau de sorcière », « Pain du fermier »). Ailleurs (un titre, un texte, un
# nom d'objet à une autre place : « au Marché »), il garde sa majuscule ; Slime la garde partout (« Seau de Slime »),
# et un nom de PNJ reste un nom propre (« Panneau du Chêne sage »).
METIERS_APRES_DE = {
    "entity.minecraft.villager.cleric": ("Witch", "Sorcière", "projet"),
    "entity.minecraft.villager.farmer": ("Farmer", "Fermier", "projet"),
    "entity.minecraft.villager.armorer": ("Armorer", "Armurier", "vanilla"),
    "entity.minecraft.villager.fisherman": ("Fisherman", "Pêcheur", "projet"),
    "shop.society_trading.market": ("Market", "Marché", "projet"),
    "shop.society_trading.wise_oak": ("Wise Oak", "Chêne sage", "projet"),
    "dialog.npc.wise_oak.name": ("Wise Oak", "Chêne sage", "projet"),
    "item.herbalbrews.witch_hat": ("Witch Hat", "Chapeau de Sorcière", "jar"),
    "block.farm_and_charm.farmers_bread_block": ("Farmer's Bread", "Pain du Fermier", "jar"),
    "item.x.armorer_helmet": ("Armorer's Helmet", "Casque d'Armurier", "projet"),
    "block.x.carrots": ("x", "SUPPRIMÉ ! Acheter des graines de carotte au Marché !", "projet"),
    "item.quark.slime_in_a_bucket": ("Slime in a Bucket", "Seau de Slime", "jar"),
    "block.x.oak_sign": ("Wise Oak Sign", "Panneau du Chêne sage", "projet"),
    "ftbquests.chapter.a.quest1.task.1.title": ("x", "Villageois Pêcheur invité", "projet"),
    "ftbquests.chapter.a.quest2.title": ("x", "Tenue de Fermier", "projet"),
    "ftbquests.chapter.a.quest2.description1": ("x", "Achète une tenue de Fermier au Marché.", "projet"),
}

# Décision du 29/09/2026 (STYLE §2), règle en attente (casse_textes) : en corps de phrase, un nom d'objet mis en valeur
# par un code couleur garde sa majuscule. Le passage va d'un code couleur (§x ou &x, x de 0 à 9 ou de a à f) jusqu'à §r,
# &r ou le code couleur suivant, et le nom y figure en entier ; un code de format (&l) n'ouvre ni ne ferme de passage.
# Sans mise en valeur, la minuscule reste de règle ; une majuscule interne que le nom n'a pas reste relevée.
MISES_EN_VALEUR = {
    "item.society.geode": ("Geode", "Géode", "projet"),
    "item.x.golden_hoe": ("Golden Hoe", "Houe dorée", "projet"),
    "item.x.watering_can": ("Watering Can", "Arrosoir", "projet"),
    "item.x.pine_tar": ("Pine Tar", "Goudron de pin", "projet"),
    "item.x.magic_bulb": ("Magic Bulb", "Ampoule magique", "projet"),
    "quest.x.geode": ("x", "Tu as trouvé une &6Géode&r ! Prends-la en main secondaire.", "projet"),
    "quest.x.houe": ("x", "Utilise ta houe dorée pour labourer la terre, puis remplis ton Arrosoir.", "projet"),
    "tooltip.x.goudron": ("x", "Chance de trouver du §6Goudron de pin§7 en récoltant.", "projet"),
    "quest.x.ampoule": ("x", "L'&dAmpoule magique&r canalise le soleil.", "projet"),
    "quest.x.gras": ("x", "Cette &6&lGéode&r brille.", "projet"),
    "quest.x.interne": ("x", "Prends la &6Houe Dorée&r.", "projet"),
    "quest.x.apres": ("x", "Une &6Géode&r, puis une Géode.", "projet"),
    "quest.x.format": ("x", "Une &lGéode&r brille.", "projet"),
    "quest.x.suivant": ("x", "Prends la &6Houe&7 dorée.", "projet"),
}


class TestCasse(unittest.TestCase):

    def test_toponyme_en_corps_de_phrase(self):
        """Règle en attente (casse_textes) : le terme générique d'un toponyme (Grotte, Lac, Mont, Forêt, Île,
        Océan…) reste en minuscule devant « de/du/des » et un nom propre, en corps de phrase (« les grottes de
        Camuy », « la mer du Nord ») ; pas en début de phrase ou d'élément de liste, ni dans un nom propre déclaré
        (« Caverne du Crâne », « Océan de Roche ») ou un nom du registre (« Forêt de Cendre »)."""
        propres = {"Caverne du Crâne": "lieu", "Océan de Roche": "clin d'oeil à Stone Ocean"}

        def toponymes(options):
            c = Corpus()
            for cle, (en, fr, origine) in TOPONYMES.items():
                c.en[cle], c.fr[cle], c.origine_fr[cle] = en, fr, origine
            config = Config(espace=Path("."), noms_propres=propres, provenance={"cles": {}, "glossaire": []})
            return [x for x in CONTROLES["casse"](c, Registre(c, config), config, options) if x.objet == "toponyme"]

        self.assertEqual(toponymes(Options()), [])
        trouves = {x.cle: x for x in toponymes(Options(toutes_regles=True))}
        self.assertEqual(sorted(trouves), ["dialog.npc.trader.a", "dialog.npc.trader.c"])
        self.assertEqual(trouves["dialog.npc.trader.a"].attendu, "Je parie que tu adorerais les grottes de Camuy !")
        self.assertEqual(trouves["dialog.npc.trader.c"].detail,
                         "terme générique d'un toponyme capitalisé en corps de phrase : « Mer »")

    def test_nom_propre_de_plusieurs_mots_en_corps_de_phrase(self):
        """En corps de phrase aussi (casse_textes), un nom propre de plusieurs mots n'exempte ses mots que là où il
        figure en entier : « Océan de Roche » déclaré laisse relever « l'Océan » et « la Roche » seuls, pas
        « l'Océan de Roche ». Un mot seul déclaré (« Aegis ») l'est partout."""
        textes = {"biome.minecraft.ocean": ("Ocean", "Océan", "vanilla"),
                  "block.minecraft.stone": ("Stone", "Roche", "vanilla"),
                  "item.society.aegis_wine": ("Aegis Wine", "Vin Aegis", "projet"),
                  "dialog.npc.market.ocean": ("x", "Je suis allée à l'Océan récemment.", "projet"),
                  "tooltip.x.roche": ("x", "Mine la Roche avec une pioche.", "projet"),
                  "tooltip.x.stone_ocean": ("x", "Elle vit dans une sorte d'Océan de Roche... ?", "projet"),
                  "tooltip.x.vin": ("x", "Un verre de vin Aegis", "projet")}
        c = constats(Options(toutes_regles=True), textes=textes,
                     noms_propres={"Océan de Roche": "clin d'oeil à Stone Ocean", "Aegis": "vin de Vinery"})
        self.assertEqual(sorted(c), ["dialog.npc.market.ocean", "tooltip.x.roche"])
        self.assertEqual(c["dialog.npc.market.ocean"].detail, "nom d'objet capitalisé en corps de phrase : « Océan »")

    def test_nom_propre_lie_par_un_trait_d_union_ou_au_pluriel(self):
        """Là où il figure en entier, un nom déclaré de plusieurs mots garde ses majuscules en corps de phrase,
        même lié par un trait d'union (« Tri-bull ») ou au pluriel (« Splendid Slimes » pour « Splendid Slime »)."""
        textes = {"entity.minecraft.slime": ("Slime", "Slime", "vanilla"),
                  "entity.farmlife.domestic_tribull": ("Domestic Tri-bull", "Tri-bull domestique", "projet"),
                  "subtitles.farmlife.death": ("x", "Mort d'un Tri-bull domestique", "projet"),
                  "quest.x.slimes": ("x", "Les &6Splendid Slimes&r sont adorables.", "projet")}
        c = constats(Options(toutes_regles=True), textes=textes,
                     noms_propres={"Tri-bull": "créature de Farmlife", "Splendid Slime": "nom des slimes du mod"})
        self.assertEqual(sorted(c), [])

    def test_titre_d_oeuvre(self):
        c = constats(textes=LIVRES, noms_propres={"sparkstone": "matière inventée du pack, employée en nom commun"})
        self.assertEqual(sorted(c), ["item.society.phenomenology_of_treasure"])
        self.assertEqual(c["item.society.phenomenology_of_treasure"].attendu, "La Phénoménologie du trésor")

    def test_nom_propre_declare_garde_ses_majuscules(self):
        """Un nom propre de plusieurs mots déclaré (« Foire aux livres ») s'écrit partout avec ses majuscules."""
        textes = {"society_tips.tip.book_fair": ("x", "La foire aux livres peut être appelée par téléphone.", "projet"),
                  "tooltip.x.fair": ("x", "Va à la Foire aux livres.", "projet"),
                  "tooltip.x.cave": ("x", "Au fond de la caverne du Crâne", "projet")}
        c = constats(textes=textes, noms_propres={"Foire aux livres": "évènement", "Caverne du Crâne": "lieu"})
        self.assertEqual(sorted(c), ["society_tips.tip.book_fair", "tooltip.x.cave"])
        self.assertEqual(c["society_tips.tip.book_fair"].attendu,
                         "La Foire aux livres peut être appelée par téléphone.")

    def test_majuscules_internes_des_noms(self):
        c = constats()
        self.assertEqual(sorted(c), ["block.betterarcheology.chicken_fossil", "block.x.cauliflower_seeds",
                                     "ftbquests.chapter.a.quest2.title"])
        self.assertEqual(c["block.betterarcheology.chicken_fossil"].attendu, "Fossile de poulet")
        self.assertEqual(c["block.x.cauliflower_seeds"].attendu, "Graines de chou-fleur")
        self.assertEqual(c["block.betterarcheology.chicken_fossil"].statut, BLOQUANT)

    def test_corps_de_phrase_quand_la_regle_est_active(self):
        c = constats(Options(toutes_regles=True))
        self.assertIn("« Plans »", c["ftbquests.chapter.a.quest1.description1"].detail)
        self.assertNotIn("Caroline", c["ftbquests.chapter.a.quest1.description1"].detail)
        self.assertIn("block.society.auto_grabber.description.fuel", c)
        self.assertEqual(c["tooltip.x.liste"].detail.count("«"), 2)  # Sparkstone et le second Plans
        self.assertNotIn("tooltip.x.vin", c)                              # « Aegis » : capitalisé par le nom
        self.assertIn("« Copier »", c["tooltip.x.gadget"].detail)
        self.assertNotIn("ftbquests.chapter.a.quest3.description1", c)    # un métier garde sa majuscule (29/09/2026)

    def test_majuscule_qui_ouvre_une_phrase_une_citation_ou_un_segment(self):
        c = constats(textes=OUVERTURES)
        self.assertEqual(sorted(c), ["block.x.carrots", "ftbquests.chapter.x.quest1.subtitle",
                                     "item.x.infinity_upgrade", "item.x.iron_brush"])
        self.assertEqual(c["block.x.carrots"].detail, "majuscule interne : « Marché »")
        self.assertEqual(c["ftbquests.chapter.x.quest1.subtitle"].attendu,
                         "Récompense : hameçon infusé au neptunium")

    def test_tiret_espace_apres_une_numerotation_ou_un_intitule_seulement(self):
        c = constats(textes=TIRETS)
        self.assertEqual(sorted(c), ["ftbquests.loot_table.1.title"])
        self.assertEqual(c["ftbquests.loot_table.1.title"].detail, "majuscule interne : « Forgeron »")

    def test_maitrise_nom_de_talent(self):
        c = constats(textes=MAITRISES)
        self.assertEqual(sorted(c), ["item.x.mastery_book"])
        self.assertEqual(c["item.x.mastery_book"].detail, "majuscule interne : « Maîtrise »")

    def test_nom_propre_de_plusieurs_mots(self):
        c = constats(textes=EXPRESSIONS, noms_propres={"Aegis": "vin de Vinery", "Caverne du Crâne": "lieu",
                                                      "Tri-bull": "créature de Farmlife"})
        self.assertEqual(sorted(c), ["biome.x.skull_caves", "block.x.oak_planks", "item.x.cavern_map"])
        self.assertEqual(c["biome.x.skull_caves"].detail, "majuscule interne : « Crâne »")
        self.assertEqual(c["block.x.oak_planks"].detail, "majuscule interne : « Chêne »")

    def test_metiers_et_boutiques_tires_des_donnees(self):
        """Les noms affichés des clés entity.minecraft.villager.<id> et entity.minecraft.villager.<mod>.<id>, et ceux
        des clés shop.society_trading.<id> : ni le villageois lui-même, ni une description, ni une maison à bâtir."""
        self.assertEqual(casse.metiers_et_boutiques(corpus_de(METIERS)),
                         sorted(["Pêcheur", "Berger", "Armurier", "Marchand exotique", "Maître brasseur", "Marché",
                                 "Marchand", "Invitations"]))

    def test_metiers_et_boutiques_gardent_leur_majuscule(self):
        """Dans un nom, un titre ou une phrase ; un nom de plusieurs mots là seulement où il figure en entier et tel
        qu'il s'écrit (« Marchand Exotique » reste relevé, « Maître » seul aussi) ; la minuscule n'est pas imposée.
        Les autres créatures restent en minuscules (« Fossile de poulet »)."""
        attendus = ["block.betterarcheology.chicken_fossil", "ftbquests.chapter.a.quest3.title", "item.x.crown"]
        c = constats(textes=METIERS)
        self.assertEqual(sorted(c), attendus)
        self.assertEqual(c["ftbquests.chapter.a.quest3.title"].detail, "majuscule interne : « Exotique »")
        self.assertEqual(c["item.x.crown"].detail, "majuscule interne : « Maître », « Pillard »")
        self.assertEqual(sorted(constats(Options(toutes_regles=True), textes=METIERS)), attendus)

    def test_slime_garde_sa_majuscule(self):
        """Dans un nom, un titre ou une phrase, parce que majuscules.json le déclare ; sans lui, la majuscule
        interne reste relevée comme pour toute créature."""
        majuscules = {"Slime": "décision du 29/09/2026 (STYLE §2)", "Slimes": "décision du 29/09/2026 (STYLE §2)"}
        attendus = ["block.betterarcheology.chicken_fossil"]
        self.assertEqual(sorted(constats(textes=SLIMES, majuscules=majuscules)), attendus)
        self.assertEqual(sorted(constats(Options(toutes_regles=True), textes=SLIMES, majuscules=majuscules)), attendus)
        self.assertIn("ftbquests.chapter.slimes.quest1.subtitle", constats(textes=SLIMES))

    def test_metier_apres_de_dans_un_nom_d_objet(self):
        """« Chapeau de Sorcière », « Pain du Fermier », « Casque d'Armurier » sont relevés ; « Villageois Pêcheur
        invité » (titre), « … au Marché », « Tenue de Fermier » (titre ou texte), « Seau de Slime » et « Panneau du
        Chêne sage » (nom de PNJ) ne le sont pas."""
        majuscules = {"Slime": "décision du 29/09/2026 (STYLE §2)"}
        attendus = ["block.farm_and_charm.farmers_bread_block", "item.herbalbrews.witch_hat", "item.x.armorer_helmet"]
        c = constats(textes=METIERS_APRES_DE, majuscules=majuscules)
        self.assertEqual(sorted(c), attendus)
        self.assertEqual(c["item.herbalbrews.witch_hat"].attendu, "Chapeau de sorcière")
        self.assertEqual(c["block.farm_and_charm.farmers_bread_block"].detail, "majuscule interne : « Fermier »")
        self.assertEqual(c["item.x.armorer_helmet"].detail, "majuscule interne : « Armurier »")
        self.assertEqual(sorted(constats(Options(toutes_regles=True), textes=METIERS_APRES_DE, majuscules=majuscules)),
                         attendus)

    def test_nom_d_objet_mis_en_valeur_en_corps_de_phrase(self):
        """« Tu as trouvé une &6Géode&r ! » garde sa majuscule ; « remplis ton Arrosoir » la perd. Hors du passage (après
        &r), dans un passage que coupe le code couleur suivant, ou derrière un simple code de format, la majuscule reste
        relevée, comme la majuscule interne d'un nom mis en valeur (« &6Houe Dorée&r »)."""
        self.assertEqual(constats(textes=MISES_EN_VALEUR), {})  # règle en attente de décision
        c = constats(Options(toutes_regles=True), textes=MISES_EN_VALEUR)
        self.assertEqual(sorted(c), ["quest.x.apres", "quest.x.format", "quest.x.houe", "quest.x.interne",
                                     "quest.x.suivant"])
        self.assertEqual(c["quest.x.houe"].detail, "nom d'objet capitalisé en corps de phrase : « Arrosoir »")
        self.assertEqual(c["quest.x.interne"].detail, "nom d'objet capitalisé en corps de phrase : « Dorée »")
        self.assertEqual(c["quest.x.apres"].detail, "nom d'objet capitalisé en corps de phrase : « Géode »")
        self.assertEqual(c["quest.x.suivant"].detail, "nom d'objet capitalisé en corps de phrase : « Houe »")

    def test_nom_qui_commence_par_un_article(self):
        """Un nom qui commence par un article (« La boîte ») ne s'apparie pas à l'article qui ouvre la phrase, ni à un
        article écrit en minuscule : dans « La &6Boîte à chenilles&r ! » et « via la &6Boîte de pêche&r », « Boîte »
        ouvre le nom mis en valeur, ce n'est pas une majuscule interne. Cité avec sa majuscule en corps de phrase, le
        nom s'apparie encore (« lis La boîte ») ; sans son article aussi (« tomber dans le Vide » cite « Le vide »)."""
        textes = {"block.kata.adv_the_box": ("The Box", "La boîte", "projet"),
                  "item.x.caterpillar_box": ("Caterpillar Box", "Boîte à chenilles", "projet"),
                  "item.x.tackle_box": ("Tackle Box", "Boîte de pêche", "projet"),
                  "quest.x.boite": ("x", "La &6Boîte à chenilles&r !", "projet"),
                  "quest.x.peche": ("x", "Les appâts s'installent via la &6Boîte de pêche&r.", "projet"),
                  "quest.x.titre": ("x", "Ouvre ensuite La Boîte.", "projet"),
                  "biome.minecraft.the_void": ("The Void", "Le vide", "vanilla"),
                  "quest.x.vide": ("x", "Le nuage l'empêche de tomber dans le Vide.", "projet")}
        c = constats(Options(toutes_regles=True), textes=textes)
        self.assertEqual(sorted(c), ["quest.x.titre", "quest.x.vide"])
        self.assertEqual(c["quest.x.vide"].detail, "nom d'objet capitalisé en corps de phrase : « Vide »")
        self.assertEqual(c["quest.x.titre"].detail, "nom d'objet capitalisé en corps de phrase : « La », « Boîte »")


if __name__ == "__main__":
    unittest.main()
