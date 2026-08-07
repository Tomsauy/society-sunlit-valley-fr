#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genere rev-orph-out-05.json a partir du lot rev-orph-05.json + decisions de relecture."""
import json, io, unicodedata

BATCH = "/Users/thomas/IAPersoProjects/SunlitValley/fr-workspace/batches/rev-orph-05.json"
OUT = "/Users/thomas/IAPersoProjects/SunlitValley/fr-workspace/batches/rev-orph-out-05.json"

# key -> (fr | None pour "inchange", certitude, pourquoi)
D = {
 # --- vanillabackport : blocs Pale Garden / Resin (1.21.4) ---
 "block.vanillabackport.dried_ghast": (None, "sur", "Nom FR officiel confirme (fr_fr du jar, wiki FR) ; accents retires."),
 "block.vanillabackport.open_eyeblossom": (None, "sur", "Oeilchidee : nom FR officiel ; oe et accents retires (3 segments)."),
 "block.vanillabackport.pale_hanging_moss": (None, "sur", "Nom FR officiel « Mousse pale suspendue »."),
 "block.vanillabackport.pale_moss_block": (None, "sur", "Nom FR officiel « Bloc de mousse pale »."),
 "block.vanillabackport.pale_moss_carpet": (None, "sur", "Nom FR officiel « Tapis de mousse pale »."),
 "block.vanillabackport.pale_oak_button": (None, "sur", "Famille chene pale : nom FR officiel du jar, coherent."),
 "block.vanillabackport.pale_oak_door": (None, "sur", "Famille chene pale : nom FR officiel du jar, coherent."),
 "block.vanillabackport.pale_oak_fence": (None, "sur", "Famille chene pale : nom FR officiel du jar, coherent."),
 "block.vanillabackport.pale_oak_fence_gate": (None, "sur", "Portillon : terme vanilla pour fence gate ; conforme au jar."),
 "block.vanillabackport.pale_oak_hanging_sign": (None, "sur", "Pancarte suspendue : convention vanilla et pack, conforme au jar."),
 "block.vanillabackport.pale_oak_leaves": (None, "sur", "Famille chene pale : nom FR officiel du jar, coherent."),
 "block.vanillabackport.pale_oak_log": (None, "sur", "Buche : terme vanilla pour log ; conforme au jar."),
 "block.vanillabackport.pale_oak_planks": (None, "sur", "Famille chene pale : nom FR officiel du jar, coherent."),
 "block.vanillabackport.pale_oak_pressure_plate": (None, "sur", "Famille chene pale : nom FR officiel du jar, coherent."),
 "block.vanillabackport.pale_oak_sapling": (None, "sur", "Pousse : terme vanilla pour sapling ; conforme au jar."),
 "block.vanillabackport.pale_oak_sign": (None, "sur", "Pancarte : convention vanilla et pack ; conforme au jar."),
 "block.vanillabackport.pale_oak_slab": (None, "sur", "Dalle en chene pale : conforme au vanilla et au jar."),
 "block.vanillabackport.pale_oak_stairs": (None, "sur", "Escalier en chene pale : conforme au vanilla et au jar."),
 "block.vanillabackport.pale_oak_trapdoor": (None, "sur", "Trappe : terme vanilla pour trapdoor ; conforme au jar."),
 "block.vanillabackport.pale_oak_wall_hanging_sign": (None, "incertain", "Anglais du mod porte « Wall » ; le fr_fr du jar l'omet."),
 "block.vanillabackport.pale_oak_wall_sign": (None, "incertain", "Anglais du mod porte « Wall » ; le fr_fr du jar l'omet."),
 "block.vanillabackport.pale_oak_wood": (None, "sur", "Bois : terme vanilla pour wood ; conforme au jar."),
 "block.vanillabackport.potted_closed_eyeblossom": (None, "sur", "Oeilchidee fermee en pot : conforme au jar, accord feminin correct."),
 "block.vanillabackport.potted_open_eyeblossom": (None, "sur", "Oeilchidee ouverte en pot : conforme au jar, accord feminin correct."),
 "block.vanillabackport.potted_pale_oak_sapling": (None, "sur", "Tournure « en pot » du vanilla ; conforme au jar."),
 "block.vanillabackport.resin_block": (None, "sur", "Anglais « Block of Resin » ; « Bloc de resine » officiel."),
 "block.vanillabackport.resin_brick_slab": (None, "sur", "Nom FR officiel « Dalle de briques de resine » verifie."),
 "block.vanillabackport.resin_brick_stairs": (None, "sur", "Nom FR officiel « Escalier en briques de resine » verifie."),
 "block.vanillabackport.resin_brick_wall": (None, "sur", "Muret : terme vanilla pour wall ; nom officiel verifie."),
 "block.vanillabackport.resin_bricks": (None, "sur", "Nom FR officiel « Briques de resine »."),
 "block.vanillabackport.resin_clump": (None, "sur", "Amas de resine : nom FR officiel, conforme au jar."),
 "block.vanillabackport.stripped_pale_oak_log": (None, "sur", "Ecorcee : terme vanilla pour stripped ; accord correct."),
 "block.vanillabackport.stripped_pale_oak_wood": (None, "sur", "Ecorce : terme vanilla pour stripped ; accord masculin correct."),
 "entity.vanillabackport.creaking": (None, "sur", "Grinceur : nom FR officiel du mob (jar, wiki FR)."),
 "entity.vanillabackport.happy_ghast": (None, "sur", "Ghast joyeux : nom FR officiel (jar, wiki FR)."),
 "entity.vanillabackport.pale_oak_boat": (None, "sur", "Bateau en chene pale : conforme au vanilla et au jar."),
 "entity.vanillabackport.pale_oak_chest_boat": (None, "sur", "Anglais « Boat with Chest » ; glossaire impose « Bateau de stockage »."),
 "item.vanillabackport.creaking_spawn_egg": (None, "sur", "Formule vanilla « Oeuf d'apparition de » + grinceur ; conforme au jar."),
 "item.vanillabackport.happy_ghast_spawn_egg": (None, "sur", "Conforme au jar et au wiki FR, qui capitalisent Ghast joyeux."),
 "item.vanillabackport.music_disc_lava_chicken": (None, "sur", "Anglais « Music Disc » ; glossaire vanilla impose « Disque »."),
 "item.vanillabackport.music_disc_lava_chicken.desc": (None, "sur", "Artiste et titre du morceau : ne se traduisent pas."),
 "item.vanillabackport.music_disc_tears": (None, "sur", "Anglais « Music Disc » ; glossaire vanilla impose « Disque »."),
 "item.vanillabackport.music_disc_tears.desc": (None, "sur", "Artiste et titre du morceau : ne se traduisent pas."),
 "item.vanillabackport.pale_oak_boat": (None, "sur", "Bateau en chene pale : conforme au vanilla et au jar."),
 "item.vanillabackport.pale_oak_chest_boat": (None, "sur", "Anglais « Boat with Chest » ; glossaire impose « Bateau de stockage »."),
 "item.vanillabackport.resin_brick": (None, "sur", "Brique de resine au singulier : objet, conforme au jar."),
 "jukebox_song.vanillabackport.lava_chicken": (None, "sur", "Artiste et titre du morceau : ne se traduisent pas."),
 "jukebox_song.vanillabackport.tears": (None, "sur", "Artiste et titre du morceau : ne se traduisent pas."),
 "painting.vanillabackport.dennis.author": (None, "sur", "Nom propre de l'autrice : garde en anglais (glossaire)."),
 "painting.vanillabackport.dennis.title": (None, "sur", "Titre du tableau, nom propre : non traduit."),
 "trim_material.vanillabackport.resin": (None, "sur", "Aligne sur les voisines trim_material (« Materiau en carmin », « en glacons »)."),
 # --- veggiesdelight ---
 "block.veggiesdelight.bellpepper_crop": (None, "sur", "Nom du legume, conforme aux temoins et a l'objet voisin."),
 "block.veggiesdelight.broccoli_crop": (None, "sur", "Nom du legume, conforme aux temoins et a l'objet voisin."),
 "block.veggiesdelight.cauliflower_crop": (None, "sur", "Nom du legume, conforme aux temoins et a l'objet voisin."),
 "block.veggiesdelight.cucumber_crop": (None, "sur", "Concombre : temoin chinois univoque ; nom du legume suffit."),
 "block.veggiesdelight.garlic_crop": (None, "sur", "Ail : temoin chinois univoque ; conforme a l'objet voisin."),
 "block.veggiesdelight.ghost_pepper_crop": (None, "sur", "Piment fantome : nom francais courant du ghost pepper."),
 "block.veggiesdelight.turnip_crop": (None, "sur", "Nom du legume, conforme aux temoins et a l'objet voisin."),
 "block.veggiesdelight.zucchini_crop": (None, "sur", "Nom du legume, conforme aux temoins et a l'objet voisin."),
 "item.veggiesdelight.cauliflower_burger": (None, "sur", "Burger au chou-fleur : registre du mod, temoin coreen concordant."),
 "item.veggiesdelight.cauliflower_patty": ("Galette de chou-fleur", "sur", "Ni la cle ni le temoin coreen ne portent « raw »."),
 "item.veggiesdelight.cooked_cauliflower_patty": (None, "sur", "Paire « Galette de chou-fleur » / « cuite » : conforme au vanilla."),
 # --- verdantvibes ---
 "block.verdantvibes.cattails.info": (None, "sur", "Les cles .info du mod donnent le binome latin : inchange."),
}

# entrees sans mention explicite : famille harnais (couleurs vanilla)
HARNESS_WHY = "Couleur vanilla FR ; identique au fr_fr du jar VanillaBackport."

batch = json.load(open(BATCH, encoding="utf-8"))
entries = []
for e in batch:
    k = e["key"]
    cur = e["traduction_actuelle"]
    if k in D:
        fr, cert, why = D[k]
        fr = cur if fr is None else fr
    elif k.startswith("item.vanillabackport.") and k.endswith("_harness"):
        fr, cert, why = cur, "sur", HARNESS_WHY
    else:
        raise SystemExit("cle non traitee: " + k)
    assert len(why.split()) <= 15, (k, len(why.split()), why)
    entries.append({"key": k, "fr": fr, "change": fr != cur, "certitude": cert, "pourquoi": why})

# controle : regle accents (item./block./entity. a 3 segments -> sans accents ni oe)
for en in entries:
    k, fr = en["key"], en["fr"]
    if k.split(".")[0] in ("item", "block", "entity") and len(k.split(".")) == 3:
        bad = [c for c in fr if unicodedata.combining(c) or c in "œŒ" or
               (unicodedata.decomposition(c) and unicodedata.category(c).startswith("L") and c.isascii() is False)]
        if bad:
            raise SystemExit("accents interdits: %s -> %s (%s)" % (k, fr, bad))

json.dump({"entries": entries}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("total", len(entries), "changes", sum(1 for e in entries if e["change"]),
      "incertains", sum(1 for e in entries if e["certitude"] == "incertain"))
