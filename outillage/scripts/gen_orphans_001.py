#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère fr-workspace/out/orphans-001.json (lot orphans-001)."""
import json
import os
import unicodedata

ROOT = "/Users/thomas/IAPersoProjects/SunlitValley"
BATCH = os.path.join(ROOT, "fr-workspace/batches/tr-orphans-001.json")

TR = {
    # --- everycomp : types de bois (clé wood_type.* -> accents complets) ---
    "wood_type.botania.livingwood": "Bois vivant",
    "wood_type.cluttered.blue_mushroom": "Champignon bleu",
    "wood_type.cluttered.crabapple": "Pommier sauvage",
    "wood_type.cluttered.flowering_crabapple": "Pommier sauvage fleuri",
    "wood_type.cluttered.flowering_poplar": "Peuplier fleuri",
    "wood_type.cluttered.flowering_willow": "Saule mystique fleuri",
    "wood_type.cluttered.fluorescent_maple": "Érable fluorescent",
    "wood_type.cluttered.poplar": "Peuplier",
    "wood_type.cluttered.red_mushroom": "Champignon rouge",
    "wood_type.cluttered.sycamore": "Sycomore",
    "wood_type.cluttered.willow": "Saule mystique",
    "wood_type.meadow.pine": "Alpin",
    "wood_type.minecraft.acacia": "Acacia",
    "wood_type.minecraft.bamboo": "Bambou",
    "wood_type.minecraft.birch": "Bouleau",
    "wood_type.minecraft.cherry": "Cerisier",
    "wood_type.minecraft.crimson": "Écarlate",
    "wood_type.minecraft.dark_oak": "Chêne noir",
    "wood_type.minecraft.jungle": "Acajou",
    "wood_type.minecraft.mangrove": "Palétuvier",
    "wood_type.minecraft.oak": "Chêne",
    "wood_type.minecraft.pale_oak": "Chêne pâle",
    "wood_type.minecraft.spruce": "Sapin",
    "wood_type.minecraft.warped": "Biscornu",
    "wood_type.quark.azalea": "Azalée",
    "wood_type.vanillabackport.pale_oak": "Chêne pâle",
    "wood_type.vinery.dark_cherry": "Cerisier noir",
    "wood_type.windswept.chestnut": "Châtaignier",
    "wood_type.windswept.holly": "Houx",
    "wood_type.windswept.pine": "Pin",

    # --- farm_and_charm (3 segments -> sans accents) ---
    "block.farm_and_charm.strawberry": "Fraisier",
    "item.farm_and_charm.strawberry_seed": "Graines de fraise",

    # --- farmersdelight : progrès (accents complets, tutoiement) ---
    "farmersdelight.advancement.harvest_ropelogged_tomate.desc":
        "Accroche une corde au-dessus d'un plant de tomate pour le faire pousser plus haut.",

    # --- ftbquests : libellés d'éditeur (style Minecraft FR impersonnel) ---
    "ftbquests.chapter.always_invisible": "Toujours invisible",
    "ftbquests.chapter.default_hide_dependency_lines":
        "'Masquer les lignes de dépendance' par défaut",
    "ftbquests.chapter.default_min_width":
        "Largeur minimale par défaut de la fenêtre de quête ouverte",
    "ftbquests.chapter.default_quest_shape": "Forme de quête par défaut",
    "ftbquests.chapter.hide_quest_details_until_startable":
        "Masquer les détails des quêtes tant qu'elles ne peuvent pas être commencées",
    "ftbquests.chapter.hide_quest_until_deps_visible":
        "Masquer les quêtes tant que les dépendances ne sont pas visibles",
    "ftbquests.chapter.progression_mode": "Mode de progression",
    "ftbquests.quest.can_repeat": "Quête répétable",
    "ftbquests.quest.dependency_requirement": "Condition de dépendance",
    "ftbquests.quest.disable_jei": "Désactiver la recette JEI",
    "ftbquests.quest.guide_page": "Page du guide",
    "ftbquests.quest.hide":
        "Masquer la quête tant que les dépendances ne sont pas visibles",
    "ftbquests.quest.hide_dependency_lines": "Masquer les lignes de dépendance",
    "ftbquests.quest.hide_dependent_lines": "Masquer les lignes des quêtes dépendantes",
    "ftbquests.quest.hide_dependent_lines.tooltip":
        "Contrôle l'affichage des lignes de dépendance vers les quêtes débloquées par celle-ci",
    "ftbquests.quest.hide_details_until_startable":
        "Masquer les détails tant que la quête ne peut pas être commencée",
    "ftbquests.quest.hide_details_until_startable.tooltip":
        "Si activé, les détails de la quête (texte et objectifs) ne sont pas consultables "
        "tant qu'elle ne peut pas être commencée",
    "ftbquests.quest.hide_text_until_complete":
        "Masquer le texte tant que la quête n'est pas terminée",
    "ftbquests.quest.ignore_reward_blocking": "Ignorer le blocage des récompenses",
    "ftbquests.quest.ignore_reward_blocking.tooltip":
        "Propose la ou les récompenses de la quête même si les récompenses sont bloquées "
        "pour l'équipe par la commande '/ftbquests block_rewards'",
    "ftbquests.quest.invisible": "Invisible",
    "ftbquests.quest.invisible.tooltip":
        "La quête reste invisible pour les joueurs tant qu'elle n'est pas terminée",
    "ftbquests.quest.invisible_until_tasks":
        "Invisible tant que X tâches ne sont pas complétées",
    "ftbquests.quest.invisible_until_tasks.tooltip":
        "Ne s'applique que si 'Invisible' est activé.\n"
        "Si la valeur est supérieure à 0, la quête apparaît une fois X tâches ou plus complétées",
    "ftbquests.quest.min_required_dependencies": "Dépendances minimales requises",
    "ftbquests.quest.min_width": "Largeur minimale de la fenêtre de quête ouverte",
    "ftbquests.quest.optional": "Quête optionnelle",
    "ftbquests.quest.progression_mode": "Mode de progression",
    "ftbquests.quest.shape": "Forme",
    "ftbquests.quest.size": "Taille",
    "ftbquests.quest.x": "X",
    "ftbquests.quest.y": "Y",
    "ftbquests.reward.ftbquests.command.player": "Exécuter en tant que joueur",

    # --- gamediscs ---
    "gamediscs.pong_game": "Pong",

    # --- longwings ---
    "block.longwings.*": "Bol",
    "effect.longwings.grace_of_the_butterflies.description":
        "Confère un peu d'absorption, porte la hauteur de saut à 5 blocs et réduit "
        "fortement les dégâts de chute. S'obtient en buvant de l'eau sucrée là où les "
        "papillons sont nombreux. La durée augmente avec le nombre de papillons alentour.",
    "effect.longwings.seed_sniffer.description":
        "Donne une chance d'obtenir les graines que le renifleur sait dénicher en cassant "
        "de la terre ou des blocs d'herbe. S'obtient en buvant de l'eau sucrée là où les "
        "papillons de nuit sont nombreux. La durée augmente avec le nombre de papillons "
        "de nuit alentour.",

    # --- loot_journal : messages de ramassage ---
    "pickup.loot_journal.experience_multiple": "Expérience (%s)",
    "pickup.loot_journal.experience_single": "Expérience",
    "pickup.loot_journal.grouped_items_multiple": "%s objets supplémentaires",
    "pickup.loot_journal.grouped_items_single": "%s objet supplémentaire",
    "pickup.loot_journal.item_multiple": "%s x%s",
    "pickup.loot_journal.item_single": "%s",

    # --- loot_journal : écran de configuration (autoconfig) ---
    "text.autoconfig.obscuria/loot_journal-client.option.display":
        "Paramètres d'affichage",
    "text.autoconfig.obscuria/loot_journal-client.option.display.aggregatedEntry":
        "Entrée groupée",
    "text.autoconfig.obscuria/loot_journal-client.option.display.aggregatedEntry.color":
        "Couleur du texte",
    "text.autoconfig.obscuria/loot_journal-client.option.display.aggregatedEntry.display":
        "Afficher les entrées groupées",
    "text.autoconfig.obscuria/loot_journal-client.option.display.aggregatedEntry.italic":
        "Texte en italique",
    "text.autoconfig.obscuria/loot_journal-client.option.display.experienceEntry":
        "Entrée d'expérience",
    "text.autoconfig.obscuria/loot_journal-client.option.display.experienceEntry.color":
        "Couleur du texte",
    "text.autoconfig.obscuria/loot_journal-client.option.display.experienceEntry.display":
        "Afficher les gains d'expérience",
    "text.autoconfig.obscuria/loot_journal-client.option.display.experienceEntry.italic":
        "Texte en italique",
    "text.autoconfig.obscuria/loot_journal-client.option.display.itemEntry":
        "Entrée d'objet",
    "text.autoconfig.obscuria/loot_journal-client.option.display.itemEntry.color":
        "Couleur du texte",
    "text.autoconfig.obscuria/loot_journal-client.option.display.itemEntry.display":
        "Afficher les objets ramassés",
    "text.autoconfig.obscuria/loot_journal-client.option.display.itemEntry.displayTotalAmount":
        "Afficher la quantité totale d'objets",
    "text.autoconfig.obscuria/loot_journal-client.option.display.itemEntry.italic":
        "Texte en italique",
    "text.autoconfig.obscuria/loot_journal-client.option.display.itemEntry.useItemFormatting":
        "Utiliser la mise en forme Minecraft",
    "text.autoconfig.obscuria/loot_journal-client.option.display.style":
        "Style des messages",
    "text.autoconfig.obscuria/loot_journal-client.option.filter": "Options du filtre",
    "text.autoconfig.obscuria/loot_journal-client.option.filter.defaultItemPolicy":
        "Règle de filtre par défaut",
    "text.autoconfig.obscuria/loot_journal-client.option.filter.itemIdBlacklist":
        "Liste noire d'ID d'objets",
    "text.autoconfig.obscuria/loot_journal-client.option.filter.itemIdWhitelist":
        "Liste blanche d'ID d'objets",
    "text.autoconfig.obscuria/loot_journal-client.option.filter.modIdBlacklist":
        "Liste noire d'ID de mods",
    "text.autoconfig.obscuria/loot_journal-client.option.filter.modIdWhitelist":
        "Liste blanche d'ID de mods",
    "text.autoconfig.obscuria/loot_journal-client.option.layout": "Options de disposition",
    "text.autoconfig.obscuria/loot_journal-client.option.layout.anchor": "Ancre à l'écran",
    "text.autoconfig.obscuria/loot_journal-client.option.layout.anchorPercentOffset":
        "Décalage relatif de l'ancre (en pourcentage)",
    "text.autoconfig.obscuria/loot_journal-client.option.layout.anchorPixelOffset":
        "Décalage de l'ancre en pixels",
    "text.autoconfig.obscuria/loot_journal-client.option.layout.displayCapacity":
        "Capacité d'affichage",
    "text.autoconfig.obscuria/loot_journal-client.option.layout.lifetime":
        "Durée d'affichage des messages (s)",
    "text.autoconfig.obscuria/loot_journal-client.option.layout.queueCapacity":
        "Capacité de la file d'attente",
    "text.autoconfig.obscuria/loot_journal-client.option.layout.scale":
        "Échelle des messages (en pourcentage)",
    "text.autoconfig.obscuria/loot_journal-client.option.layout.separation":
        "Séparation des lignes",
    "text.autoconfig.obscuria/loot_journal-client.title": "Journal du butin",

    # --- meadow (3 segments -> sans accents) ---
    "item.meadow.bear_stew": "Ragout de buffle",

    # --- minecraft (3 segments -> sans accents) ---
    "block.minecraft.beetroots": "Betteraves",
    "block.minecraft.pitcher_crop": "Plant de sarracenie",
    "block.minecraft.torchflower_crop": "Plant de torche-fleur",
    "block.minecraft.wheat": "Ble",
    "item.minecraft.cod": "Morue",
    "item.minecraft.pitcher_pod": "Graine de sarracenie",
    "item.minecraft.salmon": "Saumon",
    "item.minecraft.smithing_template": "Modele de forge",

    # --- oreganized ---
    "item.oreganized.electrum_upgrade_smithing_template":
        "Modele de forge d'amelioration en electrum",
    "item.oreganized.smithing_template.electrum_upgrade.base_slot_description":
        "Ajouter une armure, une arme ou un outil en diamant",

    # --- portable_blueprints (accents complets) ---
    "portable_blueprints.worn_blueprint.banker_house": "Maison du banquier",
    "portable_blueprints.worn_blueprint.blacksmith_house": "Maison du forgeron",
    "portable_blueprints.worn_blueprint.carpenter_house": "Maison du charpentier",
    "portable_blueprints.worn_blueprint.deluxe_basic_barn": "Grange de luxe classique",
    "portable_blueprints.worn_blueprint.fisher_house": "Maison du pêcheur",
    "portable_blueprints.worn_blueprint.market_house": "Maison du marché",
    "portable_blueprints.worn_blueprint.shepherd_house": "Maison du berger",

    # --- quark : blocs et entités (3 segments -> sans accents) ---
    "block.quark.bamboo_block": "Bloc de bambou",
    "block.quark.cobbled_deepshale_vertical_slab":
        "Dalle verticale de pierres des abimes",
    "block.quark.deepshale_brick_vertical_slab":
        "Dalle verticale de briques d'ardoise des abimes",
    "block.quark.deepshale_tile_vertical_slab":
        "Dalle verticale de tuiles d'ardoise des abimes",
    "block.quark.pallet": "Palette",
    "block.quark.polished_deepshale_vertical_slab":
        "Dalle verticale d'ardoise des abimes polie",
    "block.quark.polished_marble": "Marbre poli",
    "block.quark.shallow_dirt": "Terre peu profonde",
    "entity.quark.chest_passenger": "Coffre de bateau",
    "entity.quark.frog": "Grenouille",

    # --- quark : potions (plus de 3 segments -> accents complets) ---
    "item.minecraft.lingering_potion.effect.quark.resistance":
        "Potion persistante de résistance",
    "item.minecraft.potion.effect.quark.resistance": "Potion de résistance",
    "item.minecraft.splash_potion.effect.quark.resistance": "Potion jetable de résistance",
    "item.minecraft.tipped_arrow.effect.quark.resistance": "Flèche de résistance",

    # --- quark : carte de biome (4 segments -> accents complets) ---
    "item.quark.biome_map.snowy_tundra": "Carte de la toundra enneigée",

    # --- quark : runes et grenouilles (3 segments -> sans accents) ---
    "item.quark.black_rune": "Rune noire",
    "item.quark.blank_rune": "Rune vierge",
    "item.quark.blue_rune": "Rune bleue",
    "item.quark.brown_rune": "Rune marron",
    "item.quark.cooked_frog_leg": "Cuisse de grenouille cuite",
    "item.quark.cyan_rune": "Rune cyan",
    "item.quark.frog_leg": "Cuisse de grenouille",
    "item.quark.frog_spawn_egg": "Oeuf d'apparition de grenouille",
    "item.quark.golden_frog_leg": "Cuisse de grenouille doree",
    "item.quark.gray_rune": "Rune grise",
    "item.quark.green_rune": "Rune verte",
    "item.quark.light_blue_rune": "Rune bleu clair",
    "item.quark.light_gray_rune": "Rune gris clair",
    "item.quark.lime_rune": "Rune vert clair",
    "item.quark.magenta_rune": "Rune magenta",
    "item.quark.orange_rune": "Rune orange",
    "item.quark.pink_rune": "Rune rose",
    "item.quark.purple_rune": "Rune violette",
    "item.quark.rainbow_rune": "Rune arc-en-ciel",
}

ACCENT_FREE_PREFIXES = ("item.", "block.", "entity.")


def main():
    batch = json.load(open(BATCH, encoding="utf-8"))
    en = batch["en"]
    out_path = os.path.join(ROOT, batch["out"])

    errors = []

    missing = sorted(set(en) - set(TR))
    extra = sorted(set(TR) - set(en))
    if missing:
        errors.append("CLES MANQUANTES (%d): %s" % (len(missing), missing))
    if extra:
        errors.append("CLES INVENTEES (%d): %s" % (len(extra), extra))

    # Règle accents : item./block./entity. + exactement 3 segments -> sans accents ni oe
    for k, v in TR.items():
        if k.startswith(ACCENT_FREE_PREFIXES) and k.count(".") == 2:
            bad = [c for c in v if unicodedata.combining(c)
                   or (unicodedata.decomposition(c) and c.isalpha())
                   or c in "œŒ"]
            if bad:
                errors.append("ACCENT INTERDIT %s -> %r (%s)" % (k, v, bad))
        if "’" in v:
            errors.append("APOSTROPHE TYPO %s -> %r" % (k, v))
        if not v.strip():
            errors.append("VIDE %s" % k)

    # Placeholders : cohérence avec le témoin quand il existe
    for e in batch["entries"]:
        k = e["key"]
        wit = e.get("witness") or {}
        if not wit:
            continue
        ref = max((w.count("%s") for w in wit.values()), default=0)
        got = TR[k].count("%s")
        if ref and got != ref:
            errors.append("PLACEHOLDER %s : temoin=%d fr=%d (%r)" % (k, ref, got, TR[k]))

    if errors:
        for e in errors:
            print("ERREUR:", e)
        raise SystemExit(1)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"translations": {k: TR[k] for k in en}}, f,
                  ensure_ascii=False, indent=1, sort_keys=False)
        f.write("\n")

    print("OK ->", out_path)
    print("cles ecrites :", len(en))


if __name__ == "__main__":
    main()
