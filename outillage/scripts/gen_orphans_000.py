#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Génère fr-workspace/out/orphans-000.json (lot orphans-000)."""
import json, os

ROOT = "/Users/thomas/IAPersoProjects/SunlitValley"
BATCH = os.path.join(ROOT, "fr-workspace/batches/tr-orphans-000.json")

T = {
    # --- ali (Advanced Loot Info) : interface, FR accentué, style Minecraft impersonnel ---
    "ali.enum.group_type.normalize": "Normaliser",
    "ali.property.branch.bees": "Abeilles :",
    "ali.property.branch.effects": "Effets :",
    "ali.property.value.chance": "Probabilité : %s",
    "ali.property.value.detail_not_available": "Détails non disponibles",
    "ali.property.value.null": "%s",
    "ali.type.condition.config_enabled": "Doit être activé dans la configuration",
    "ali.type.condition.essence_only_spawn": "Apparition d'essence uniquement",
    "ali.type.condition.optional_property": "Propriété optionnelle",
    "ali.type.function.bluprintz": "Easter egg Bluprintz",
    "ali.type.function.conveyor_cover": "Appliquer un couvercle de convoyeur",
    "ali.type.function.curse_loot": "Maudire le butin",
    "ali.type.function.double_drops": "Doubler les objets lâchés",
    "ali.type.function.drop_container_items": "Lâcher les objets du conteneur",
    "ali.type.function.honey_compass_locate_structure": "Boussole de miel : structure",
    "ali.type.function.modified_item": "Modifié dynamiquement !",
    "ali.type.function.property_count": "Obtenir le compte depuis une propriété",
    "ali.type.function.random_arrow": "Flèche aléatoire",
    "ali.type.function.retexture_block_entity": "Changer la texture de l'entité de bloc",
    "ali.type.function.revolver_perk": "Bonus de revolver",
    "ali.type.function.set_fluid": "Définir le fluide",
    "ali.type.function.set_painting_variant": "Définir la variante du tableau",
    "ali.type.function.spawn_tnt": "Faire apparaître de la TNT",
    "ali.type.function.spawn_xp": "Faire apparaître de l'expérience",
    "ali.type.function.tag_item_removals": "Retirer les objets d'un tag",
    "ali.type.function.uniquify_if_has_items": "Rendre unique si des objets sont présents",
    "ali.type.function.whirlwind_spawn_entity": "Tourbillon : faire apparaître une entité",
    "ali.type.function.windmill": "Définir les voiles du moulin à vent",
    "ali.util.advanced_loot_info.key_value": "%s : %s",
    "ali.util.advanced_loot_info.missing": "Non implémenté : %s",
    "ali.util.advanced_loot_info.two_values": "%s%s",
    "ali.util.advanced_loot_info.two_values_with_space": "%s %s",

    # --- brewery : blocs / objets (préfixes 3 segments -> SANS accents) ---
    "block.brewery.barley_crop": "Pousse d'Orge",
    "block.brewery.corn_crop": "Pousse de Mais",
    "block.brewery.hop_trellis": "Houblon",
    "block.brewery.silo_copper": "Silo en cuivre",
    "block.brewery.silo_wood": "Silo en bois",
    "item.brewery.barley": "Orge",
    "item.brewery.corn": "Mais",
    "item.brewery.hop_trellis_seed": "Graines de houblon",

    # --- brewery : conteneur / sons (sous-titres, FR accentué) ---
    "brewery.container.cabinet": "Armoire",
    "brewery.sound.beer_elemental_ambient": "L'élémentaire de bière respire",
    "brewery.sound.beer_elemental_attack": "L'élémentaire de bière attaque",
    "brewery.sound.beer_elemental_death": "L'élémentaire de bière meurt",
    "brewery.sound.beer_elemental_hurt": "L'élémentaire de bière est blessé",
    "brewery.sound.breath": "Souffle",
    "brewery.sound.brewstation_ambient": "Bourdonnement de la station de brassage",
    "brewery.sound.brewstation_kettle": "Bouillonnement de la cuve",
    "brewery.sound.brewstation_oven": "Crépitement du four",
    "brewery.sound.brewstation_timer": "Tic-tac du minuteur",
    "brewery.sound.brewstation_whistle": "Sifflement de la vapeur",
    "brewery.sound.cabinet_close": "Fermeture de l'armoire",
    "brewery.sound.cabinet_open": "Ouverture de l'armoire",
    "brewery.sound.drawer_close": "Fermeture du tiroir",
    "brewery.sound.drawer_open": "Ouverture du tiroir",
    "brewery.sound.timer_ticking": "Tic-tac du minuteur",

    # --- brewery : effets (clés à 4 segments -> FR accentué) ---
    "effect.brewery.blackout.description": "(Complètement dans les vapes.)",
    "effect.brewery.combustion.description": "Enflamme les ennemis à proximité.",
    "effect.brewery.drunk.description": "Ouuuh... ça tourne !",
    "effect.brewery.explosion.description": "Faible chance de lancer une boule de feu lors d'une attaque.",
    "effect.brewery.haley.description": "Permet de voler pendant toute la durée de l'effet.",
    "effect.brewery.healingtouch.description": "Soigne la cible attaquée.",
    "effect.brewery.lightning_strike.description": "Faible chance de faire tomber la foudre lors d'une attaque.",
    "effect.brewery.mining.description": "Plus la profondeur est grande, plus le minage est rapide.",
    "effect.brewery.pacify.description": "Croiser le regard d'un Enderman ne le provoque plus, et les ennemis abandonnent la poursuite plus vite.",
    "effect.brewery.partystarter.description": "Tire une fusée de feu d'artifice sur la cible attaquée et lui inflige de légers dégâts.",
    "effect.brewery.pintcharisma.description": "Offre 10 % de réduction lors des échanges avec les villageois. Ça n'a pas l'air de marcher par ici, cela dit...",
    "effect.brewery.protectivetouch.description": "Confère l'effet Absorption II à la cible attaquée",
    "effect.brewery.renewingtouch.description": "Confère l'effet Régénération II à la cible attaquée",
    "effect.brewery.repulsion.description": "Repousse légèrement les ennemis à proximité.",
    "effect.brewery.saturated": "Saturation",
    "effect.brewery.snowwhite.description": "Les animaux te suivent.",
    "effect.brewery.toxictouch.description": "Confère l'effet Poison III à la cible attaquée",
    "entity.brewery.beer_elemental.description": "Bibine",

    # --- brewery : REI + tooltips ---
    "rei.brewery.silo_category": "Silo de séchage",
    "tooltip.brewery.canbeplaced": "Peut être placé",
    "tooltip.brewery.canbeplacedwalls": "Peut être placé sur les murs",
    "tooltip.brewery.cantbeplacedhere": "Ce bloc ne peut pas être placé ici. Il faut un espace de 2x2x2",
    "tooltip.brewery.crafting": "Ingrédient de fabrication",
    "tooltip.brewery.expandable": "Extensible",
    "tooltip.brewery.flowerpot": "Peut servir de pot de fleurs",
    "tooltip.brewery.ingredient": "Ingrédient de recette",
    "tooltip.brewery.rope": "Peut être attaché aux barrières ou aux crochets de détente",
    "tooltip.brewery.rope_2": "Treillis à houblon",
    "tooltip.brewery.stuffed.duration.block.brewery.dumplings": "Rassasié (5:00)",
    "tooltip.brewery.stuffed.duration.block.brewery.fried_chicken": "Rassasié (5:00)",
    "tooltip.brewery.stuffed.duration.block.brewery.half_chicken": "Rassasié (3:20)",
    "tooltip.brewery.stuffed.duration.block.brewery.mashed_potatoes": "Rassasié (3:20)",
    "tooltip.brewery.stuffed.duration.block.brewery.pork_knuckle": "Rassasié (3:20)",
    "tooltip.brewery.stuffed.duration.block.brewery.potato_salad": "Rassasié (5:00)",
    "tooltip.brewery.stuffed.duration.item.brewery.pretzel": "Rassasié (1:40)",
    "tooltip.brewery.stuffed.duration.item.brewery.sausage": "Rassasié (5:00)",
    "tooltip.brewery.workstation": "Poste de travail de villageois",
    "tooltip.brewfest.brewfest_effect": "Superbe tenue ! Ton équipement est complet et tu es immunisé contre l'ivresse",
    "tooltip.brewfest.brewfest_seteffect": "Bonus de panoplie :",
    "tooltip.brewfest.brewfestdrop": "Vendu par le villageois brasseur",

    # --- cluttered ---
    "cluttered.支架.tooltip": "Peut être placé sur les barrières",

    # --- dialogue PNJ (tutoiement chaleureux) ---
    "dialog.npc.carpenter.unique_need_to_buy.line_0": "Tu as besoin d'acheter quelque chose ?",

    # --- dramaticdoors (block.<ns>.<x> = 3 segments -> SANS accents) ---
    "block.dramaticdoors.short_rubber_tree_plank_treated_door": "Petite porte en planches d'hevea traitees",
    "block.dramaticdoors.tall_rubber_tree_plank_treated_door": "Grande porte en planches d'hevea traitees",

    # --- everycomp : types de feuilles (noms naturels, capitalisation FR) ---
    "leaves_type.atmospheric.aspen": "Tremble",
    "leaves_type.atmospheric.currant": "Groseillier",
    "leaves_type.atmospheric.dry_laurel": "Laurier sec",
    "leaves_type.atmospheric.flowering_morado": "Morado en fleurs",
    "leaves_type.atmospheric.green_aspen": "Tremble vert",
    "leaves_type.atmospheric.grimwood": "Grimwood",
    "leaves_type.atmospheric.kousa": "Cornouiller kousa",
    "leaves_type.atmospheric.laurel": "Laurier",
    "leaves_type.atmospheric.morado": "Morado",
    "leaves_type.atmospheric.rosewood": "Palissandre",
    "leaves_type.atmospheric.yucca": "Yucca",
    "leaves_type.autumnity.maple": "Érable",
    "leaves_type.autumnity.orange_maple": "Érable orange",
    "leaves_type.autumnity.red_maple": "Érable rouge",
    "leaves_type.autumnity.yellow_maple": "Érable jaune",
    "leaves_type.beachparty.palm": "Palmier",
    "leaves_type.cluttered.flowering_fluorescent_maple": "Érable fluorescent en fleurs",
    "leaves_type.cluttered.poplar": "Peuplier",
    "leaves_type.cluttered.sycamore": "Platane",
    "leaves_type.cluttered.willow": "Saule",
    "leaves_type.minecraft.pale_oak": "Chêne pâle",
    "leaves_type.vanillabackport.pale_oak": "Chêne pâle",
    "leaves_type.vinery.apple": "Pommier",
    "leaves_type.vinery.dark_cherry": "Cerisier sombre",
    "leaves_type.vinery.grapevine": "Vigne",
    "leaves_type.windswept.chestnut": "Châtaignier",
    "leaves_type.windswept.flowering_acacia": "Acacia en fleurs",
    "leaves_type.windswept.holly": "Houx",
    "leaves_type.windswept.pine": "Pin",

    # --- everycomp : types de bois ---
    "wood_type.atmospheric.aspen": "Tremble",
    "wood_type.atmospheric.grimwood": "Grimwood",
    "wood_type.atmospheric.kousa": "Cornouiller kousa",
    "wood_type.atmospheric.laurel": "Laurier",
    "wood_type.atmospheric.morado": "Morado",
    "wood_type.atmospheric.rosewood": "Palissandre",
    "wood_type.atmospheric.yucca": "Yucca",
    "wood_type.autumnity.maple": "Érable",
    "wood_type.beachparty.palm": "Palmier",
    "wood_type.betterarcheology.rotten": "Pourri",
    "wood_type.botania.dreamwood": "Bois de rêve",
}

# pad.1..pad.20 : chaînes d'indentation pures (2*N espaces + "->"), identiques dans toutes les langues
for n in range(1, 21):
    T["ali.util.advanced_loot_info.pad.%d" % n] = " " * (2 * n) + "->"

batch = json.load(open(BATCH, encoding="utf-8"))
en = batch["en"]
out_path = os.path.join(ROOT, batch["out"])

missing = [k for k in en if k not in T]
extra = [k for k in T if k not in en]
assert not missing, "MANQUANTES: %r" % missing[:20]
assert not extra, "INVENTEES: %r" % extra[:20]

# Contrôle règle accents : item./block./entity. avec EXACTEMENT 3 segments -> pas d'accents ni oe
ACC = "àâäçéèêëîïôöùûüÿœÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸŒ"
bad = []
for k, v in T.items():
    seg = k.split(".")
    if len(seg) == 3 and seg[0] in ("item", "block", "entity"):
        if any(c in ACC for c in v):
            bad.append((k, v))
assert not bad, "ACCENTS INTERDITS: %r" % bad

# Contrôle placeholders %s vs témoin/EN
for k, v in T.items():
    assert "’" not in v, "apostrophe typographique dans %s" % k

ordered = {k: T[k] for k in en}
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({"translations": ordered}, f, ensure_ascii=False, indent=1)
    f.write("\n")

print("OK", out_path, len(ordered))
