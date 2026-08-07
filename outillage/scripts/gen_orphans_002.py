#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere fr-workspace/out/orphans-002.json a partir du lot batches/tr-orphans-002.json.

Rappel des regles appliquees :
  - cles item./block./entity. a EXACTEMENT 3 segments -> valeurs SANS accents (recherche EMI)
  - tout le reste -> francais correctement accentue
  - glossaire du lot respecte ; noms vanilla repris de references/mc_fr_fr.json
  - traductions deja presentes dans fr-workspace/out reutilisees telles quelles
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../fr-workspace

T = {
    # ------------------------------------------------------------------ quark
    "item.quark.red_rune": "Rune rouge",
    "item.quark.soul_compass": "Boussole des ames",
    "item.quark.white_rune": "Rune blanche",
    "item.quark.yellow_rune": "Rune jaune",
    "quark.gui.config.social.reddit": "/r/QuarkMod sur Reddit",
    "quark.jei.hint.preamble": "[Quark]\n",
    "quark.misc.mod_disabled": "Désactivé. Installer %s pour l'activer.",
    "quark.subtitles.frog_die": "Grenouille qui meurt",
    "quark.subtitles.frog_hurt": "Grenouille blessée",
    "quark.subtitles.frog_idle": "Coassement de grenouille",
    "quark.subtitles.frog_jump": "Grenouille qui saute",

    # --------------------------------------------------------- rottencreatures
    "effect.rottencreatures.channelled": "Canalisé",
    "effect.rottencreatures.channelled.description": "Attire naturellement la foudre sur les joueurs",

    # ------------------------------------------------------------ shippingbin
    "block.shippingbin.basic_shipping_bin": "Bac d'expedition classique",
    "block.shippingbin.smart_shipping_bin": "Bac d'expedition intelligent",

    # ------------------------------------------------------------ snowyspirit
    "item.snowyspirit.sled_bamboo": "Luge en bambou",
    "item.snowyspirit.sled_cherry": "Luge en cerisier",
    "item.snowyspirit.sled_mangrove": "Luge en paletuvier",

    # ---------------------------------------------------- society : cultures &
    # arroseurs (blocs de culture : meme nom que la recolte, comme en vanilla)
    "block.society.ancient_fruit": "Fruit ancien",
    "block.society.blueberry": "Myrtille",
    "block.society.carrot": "Carotte",
    "block.society.cranberry": "Canneberge",
    "block.society.diamond_sprinkler": "Arroseur en diamant",
    "block.society.eggplant": "Aubergine",
    "block.society.gold_sprinkler": "Arroseur en or",
    "block.society.iron_sprinkler": "Arroseur en fer",
    "block.society.netherite_sprinkler": "Arroseur en iridium",
    "block.society.onion": "Oignon",
    "block.society.peanut": "Cacahuete",
    "block.society.potato": "Pomme de terre",
    "block.society.sparkpod": "Sparkpod",
    "block.society.sweet_potato": "Patate douce",
    "block.society.tubabacco_leaf": "Feuille de tubabac",
    "block.veggiesdelight.garlic": "Ail",

    # ------------------------------------------------------ society : divers
    "info.society.villager_unlock_condition.wise_oak": "Chêne sage",
    "item.society.architects_digest": "§f♧ §rRevue de l'architecte",
    "item.society.architects_digest.description":
        "Nécessaire pour fabriquer les meubles ♧ §fmodernes§r",
    "item.society.bank_meter": "Compteur bancaire",
    "item.society.fantasy_dust": "§f♡ §rPoudre fantasy",
    "item.society.fantasy_dust.description":
        "Nécessaire pour fabriquer les meubles ♡ §efantasy§r",
    "item.society.farm_building_supplies": "Materiaux de construction de ferme",
    "item.society.tanuki_leaf": "§f♤ §rFeuille de tanuki",
    "item.society.tanuki_leaf.description":
        "Nécessaire pour fabriquer les meubles ♤ §atanuki§r",
    "item.society.village_building_supplies": "Materiaux de construction de village",
    "jei.society.category.furniture_catalog": "Catalogue de meubles",
    "society.furniture_catalog.give_me_coin": "Clic droit avec %s %s pour acheter %s %s",
    "tooltip.society.adventuring_mastery": "Récompense de maîtrise en aventure",
    "tooltip.society.adventuring_mastery.required": "🏹 §6Récompense de maîtrise en aventure",
    "tooltip.society.farming_mastery": "Récompense de maîtrise en agriculture",
    "tooltip.society.farming_mastery.required": "🏹 §6Récompense de maîtrise en agriculture",
    "tooltip.society.fishing_mastery": "Récompense de maîtrise en pêche",
    "tooltip.society.fishing_mastery.required": "🏹 §6Récompense de maîtrise en pêche",
    "tooltip.society.furniture_catalog":
        "Clic droit avec %s %s\npour acheter 1 %s.\nMaj + clic droit pour acheter en gros",
    "tooltip.society.husbandry_mastery": "Récompense de maîtrise en élevage",
    "tooltip.society.husbandry_mastery.required": "🏹 §6Récompense de maîtrise en élevage",
    "tooltip.society.liltractor":
        "Maj + clic droit pour ouvrir l'inventaire\n"
        "Espace une fois en selle pour changer de mode\n"
        "Peut être teint",
    "tooltip.society.mining_mastery": "Récompense de maîtrise en minage",
    "tooltip.society.mining_mastery.required": "🏹 §6Récompense de maîtrise en minage",

    # ---------------------------------------------------------- society trading
    "jei.society_trading.master_culitvator_unlocked": "Nécessite le maître cultivateur",
    "shop.society_trading.cleric": "Prêtre",
    "shop.society_trading.cleric.description":
        "Vend des baguettes et des cristaux de regret pour réinitialiser les arbres de compétences.",
    "shop.society_trading.exotic_trader": "Marchand exotique",
    "shop.society_trading.exotic_trader.description":
        "Troque des améliorations de machines artisanales et d'autres objets utiles.",

    # ------------------------------------------------------------------ species
    "item.species.spectralibur.desc.action.2": "+3 dégâts magiques",

    # ---------------------------------------------------------- splendid slimes
    "info.splendid_slimes.slime_vac":
        "Tire l'objet de la main secondaire. Accroupi, aspire les slimes et les objets.",
    "item.splendid_slimes.slime_feeder": "Mangeoire a slimes",

    # ---------------------------------------------------------- stardew fishing
    "attribute.name.stardew_fishing.bar_size": "Taille de la barre de pêche",
    "attribute.name.stardew_fishing.exp_multiplier": "Expérience de pêche",
    "attribute.name.stardew_fishing.line_strength": "Force du fil de pêche",
    "attribute.name.stardew_fishing.treasure_chance_bonus": "Chance de trouver un trésor",

    # ------------------------------------------------------------------ divers
    "key.trashslot.toggleLock": "Verrouiller/Déverrouiller TrashSlot",
    "itemGroup.twigs.item_group": "Twigs",

    # ------------------------------------------------------------ unusual fish
    "entity.unusualfishmod.blind_sailfin": "Poisson-voile aveugle",
    "entity.unusualfishmod.root": "Boule de racines",
    "entity.unusualfishmod.snowflake_tail_fish": "Nageoire givree",
    "entity.unusualfishmod.tiger_jungle_shark": "Requin-tigre de la jungle",

    # --------------------------------------- vanillabackport (noms vanilla FR)
    "biome.vanillabackport.pale_garden": "Jardin pâle",
    "block.vanillabackport.chiseled_resin_bricks": "Briques de resine sculptees",
    "block.vanillabackport.closed_eyeblossom": "Oeilchidee fermee",
    "block.vanillabackport.creaking_heart": "Coeur de grinceur",
    "block.vanillabackport.dried_ghast": "Ghast desseche",
    "block.vanillabackport.open_eyeblossom": "Oeilchidee ouverte",
    "block.vanillabackport.pale_hanging_moss": "Mousse pale suspendue",
    "block.vanillabackport.pale_moss_block": "Bloc de mousse pale",
    "block.vanillabackport.pale_moss_carpet": "Tapis de mousse pale",
    "block.vanillabackport.pale_oak_button": "Bouton en chene pale",
    "block.vanillabackport.pale_oak_door": "Porte en chene pale",
    "block.vanillabackport.pale_oak_fence": "Barriere en chene pale",
    "block.vanillabackport.pale_oak_fence_gate": "Portillon en chene pale",
    "block.vanillabackport.pale_oak_hanging_sign": "Pancarte suspendue en chene pale",
    "block.vanillabackport.pale_oak_leaves": "Feuilles de chene pale",
    "block.vanillabackport.pale_oak_log": "Buche de chene pale",
    "block.vanillabackport.pale_oak_planks": "Planches de chene pale",
    "block.vanillabackport.pale_oak_pressure_plate": "Plaque de pression en chene pale",
    "block.vanillabackport.pale_oak_sapling": "Pousse de chene pale",
    "block.vanillabackport.pale_oak_sign": "Pancarte en chene pale",
    "block.vanillabackport.pale_oak_slab": "Dalle en chene pale",
    "block.vanillabackport.pale_oak_stairs": "Escalier en chene pale",
    "block.vanillabackport.pale_oak_trapdoor": "Trappe en chene pale",
    "block.vanillabackport.pale_oak_wall_hanging_sign": "Pancarte suspendue murale en chene pale",
    "block.vanillabackport.pale_oak_wall_sign": "Pancarte murale en chene pale",
    "block.vanillabackport.pale_oak_wood": "Bois de chene pale",
    "block.vanillabackport.potted_closed_eyeblossom": "Oeilchidee fermee en pot",
    "block.vanillabackport.potted_open_eyeblossom": "Oeilchidee ouverte en pot",
    "block.vanillabackport.potted_pale_oak_sapling": "Pousse de chene pale en pot",
    "block.vanillabackport.resin_block": "Bloc de resine",
    "block.vanillabackport.resin_brick_slab": "Dalle de briques de resine",
    "block.vanillabackport.resin_brick_stairs": "Escalier en briques de resine",
    "block.vanillabackport.resin_brick_wall": "Muret de briques de resine",
    "block.vanillabackport.resin_bricks": "Briques de resine",
    "block.vanillabackport.resin_clump": "Amas de resine",
    "block.vanillabackport.stripped_pale_oak_log": "Buche de chene pale ecorcee",
    "block.vanillabackport.stripped_pale_oak_wood": "Bois de chene pale ecorce",
    "entity.vanillabackport.creaking": "Grinceur",
    "entity.vanillabackport.happy_ghast": "Ghast joyeux",
    "entity.vanillabackport.pale_oak_boat": "Bateau en chene pale",
    "entity.vanillabackport.pale_oak_chest_boat": "Bateau de stockage en chene pale",
    "item.vanillabackport.black_harness": "Harnais noir",
    "item.vanillabackport.blue_harness": "Harnais bleu",
    "item.vanillabackport.brown_harness": "Harnais marron",
    "item.vanillabackport.creaking_spawn_egg": "Oeuf d'apparition de grinceur",
    "item.vanillabackport.cyan_harness": "Harnais cyan",
    "item.vanillabackport.gray_harness": "Harnais gris",
    "item.vanillabackport.green_harness": "Harnais vert",
    "item.vanillabackport.happy_ghast_spawn_egg": "Oeuf d'apparition de Ghast joyeux",
    "item.vanillabackport.light_blue_harness": "Harnais bleu clair",
    "item.vanillabackport.light_gray_harness": "Harnais gris clair",
    "item.vanillabackport.lime_harness": "Harnais vert clair",
    "item.vanillabackport.magenta_harness": "Harnais magenta",
    "item.vanillabackport.music_disc_lava_chicken": "Disque",
    "item.vanillabackport.music_disc_lava_chicken.desc": "Hyper Potions - Lava Chicken",
    "item.vanillabackport.music_disc_tears": "Disque",
    "item.vanillabackport.music_disc_tears.desc": "Amos Roddy - Tears",
    "item.vanillabackport.orange_harness": "Harnais orange",
    "item.vanillabackport.pale_oak_boat": "Bateau en chene pale",
    "item.vanillabackport.pale_oak_chest_boat": "Bateau de stockage en chene pale",
    "item.vanillabackport.pink_harness": "Harnais rose",
    "item.vanillabackport.purple_harness": "Harnais violet",
    "item.vanillabackport.red_harness": "Harnais rouge",
    "item.vanillabackport.resin_brick": "Brique de resine",
    "item.vanillabackport.white_harness": "Harnais blanc",
    "item.vanillabackport.yellow_harness": "Harnais jaune",
    "jukebox_song.vanillabackport.lava_chicken": "Hyper Potions - Lava Chicken",
    "jukebox_song.vanillabackport.tears": "Amos Roddy - Tears",
    "painting.vanillabackport.dennis.author": "Sarah Boeving",
    "painting.vanillabackport.dennis.title": "Dennis",
    "trim_material.vanillabackport.resin": "Matériau en résine",

    # ---------------------------------------------------------- veggiesdelight
    "block.veggiesdelight.bellpepper_crop": "Poivron",
    "block.veggiesdelight.broccoli_crop": "Brocoli",
    "block.veggiesdelight.cauliflower_crop": "Chou-fleur",
    "block.veggiesdelight.cucumber_crop": "Concombre",
    "block.veggiesdelight.garlic_crop": "Ail",
    "block.veggiesdelight.ghost_pepper_crop": "Piment fantome",
    "block.veggiesdelight.turnip_crop": "Navet",
    "block.veggiesdelight.zucchini_crop": "Courgette",
    "item.veggiesdelight.cauliflower_burger": "Burger au chou-fleur",
    "item.veggiesdelight.cauliflower_patty": "Galette de chou-fleur crue",
    "item.veggiesdelight.cooked_cauliflower_patty": "Galette de chou-fleur cuite",

    # ------------------------------------------------------------ verdantvibes
    "block.verdantvibes.cattails.info": "Typha latifolia",
}

batch = json.load(open(os.path.join(ROOT, "batches", "tr-orphans-002.json"), encoding="utf-8"))
keys = list(batch["en"].keys())
missing = [k for k in keys if k not in T]
extra = [k for k in T if k not in batch["en"]]
assert not missing, "MANQUANTES (%d): %s" % (len(missing), missing)
assert not extra, "EN TROP (%d): %s" % (len(extra), extra)

out = {"translations": {k: T[k] for k in keys}}
path = os.path.join(os.path.dirname(ROOT), batch["out"])
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
    f.write("\n")
print("ok", path, len(out["translations"]))
