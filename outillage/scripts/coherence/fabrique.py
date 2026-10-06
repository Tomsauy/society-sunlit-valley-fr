"""Petits packs et espaces de travail pour les tests : un dict {chemin: contenu} par arbre."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path


def ecrire(racine: Path, fichiers: dict) -> Path:
    """Écrit chaque fichier ; un dict ou une liste est sérialisé en JSON."""
    for chemin, contenu in fichiers.items():
        cible = racine / chemin
        cible.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(contenu, (dict, list)):
            contenu = json.dumps(contenu, ensure_ascii=False, indent=2)
        cible.write_text(contenu, encoding="utf-8")
    return racine


def donnees_vides() -> dict:
    """Chaque fichier de données que le vérificateur exige de l'espace de travail, avec sa valeur vide."""
    fichiers = {f"coherence/{nom}.json": vide for nom, vide in (
        ("exceptions", []), ("dette", []), ("familles", {"familles": [], "accords": {}}), ("gabarits", {}),
        ("largeurs", []), ("scripts_patches", {}), ("mots_generiques", {}), ("mods_retires", {}),
        ("formes_interdites", []), ("noms_propres", {}), ("majuscules", {}), ("termes_imposes", []),
        ("regles", {"casse_textes": False, "pourcentages": "", "nombres": False, "largeurs_mods": False,
                     "terminologie_interdits": False}), ("double_sens", []),
        ("homographes", {}), ("renvois", []))}
    fichiers.update({"accents/vocabulaire.json": {}, "provenance.json": {"cles": {}}, "KEEP-ENGLISH.md": "",
                     "references/mc_en_us.json": {}, "references/mc_fr_fr.json": {}, "society-corrected-en.json": {}})
    return fichiers


def pack_et_espace(pack: dict, espace: dict):
    """Un dossier temporaire avec pack/ et espace/ ; appeler .cleanup() sur le premier élément. L'espace reçoit
    chaque fichier de données requis, vide, sauf ceux que `espace` fournit."""
    dossier = tempfile.TemporaryDirectory()
    base = Path(dossier.name)
    ecrire(base / "pack", pack)
    ecrire(base / "espace", {"extracted/.garde": "", **donnees_vides(), **espace})
    return dossier, base / "pack", base / "espace"


PACK = {
    "pakku.json": {"version": "4.1.5"},
    "kubejs/assets/society/lang/en_us.json": {
        "item.society.cle_rouge": "",
        "item.society.bac": "Shipping Bin",
        "tooltip.society.bac": "Place your &6Shipping Bins&r here",
    },
    "kubejs/assets/society/lang/fr_fr.json": {
        "_comment": "Objets",
        "item.society.cle_rouge": "Clé rouge",
        "item.society.bac": "Bac d'expédition",
        "tooltip.society.bac": "Place tes &6bacs d'expédition&r ici",
        "block.furniture.sofa": "Canapé",
    },
    "kubejs/assets/society/lang/ko_kr.json": {"item.society.cle_rouge": "빨간 열쇠", "item.society.oubliee": "잊힌"},
    "kubejs/assets/furniture/lang/fr_fr.json": {"_comment": "Meubles", "block.furniture.sofa": "Sofa"},
}

ESPACE = {
    "references/mc_en_us.json": {"block.minecraft.stone": "Stone"},
    "references/mc_fr_fr.json": {"block.minecraft.stone": "Roche"},
    "extracted/furniture-1.0/furniture/en_us.json": {"block.furniture.sofa": "Sofa", "block.furniture.table": "Table"},
    "extracted/furniture-1.0/furniture/fr_fr.json": {"block.furniture.table": "Table"},
    "society-corrected-en.json": {"item.society.cle_rouge": "Red Key"},
}

QUETE_SNBT = """{
	id: "5F2C"
	quests: [
		{
			id: "086A3F527E1A973E"
			icon: "constructionwand:core_angel"
			title: "{ftbquests.chapter.tools.quest86A3F527E1A973E.title}"
			description: ["{ftbquests.chapter.tools.quest86A3F527E1A973E.description1}", ""]
			tasks: [{
				id: "7F0933DA244DC98F"
				item: { Count: 1, id: "itemfilters:or", tag: { items: [ { Count: 1b, id: "constructionwand:core_destruction" } ] } }
				title: "{ftbquests.chapter.tools.quest86A3F527E1A973E.task.9153904729612208527.title}"
				type: "item"
			}]
		}
	]
}"""

PACK_COMPLET = {
    **PACK,
    "patchouli_books/almanac/en_us/entries/animals/goat.json": {
        "name": "Goat", "category": "patchouli:animals", "icon": "society:large_goat_milk",
        "pages": [{"type": "patchouli:text", "text": "Goats give $(item)milk$()."},
                  {"type": "patchouli:entity", "entity": "minecraft:goat{Age:0}", "text": "A goat."}],
    },
    "patchouli_books/almanac/fr_fr/entries/animals/goat.json": {
        "name": "Chèvre", "category": "patchouli:animals", "icon": "society:large_goat_milk",
        "pages": [{"type": "patchouli:text", "text": "Les chèvres donnent du $(item)lait$()."},
                  {"type": "patchouli:entity", "entity": "minecraft:goat{Age:0}", "text": "Une chèvre."}],
    },
    "config/fancymenu/assets/changelog_en_us.markdown": "^^^\n## 4.1.5\n^^^\n---\n- Added a thing\n",
    "config/fancymenu/assets/changelog_fr_fr.markdown": "^^^\n## 4.1.5\n^^^\n---\n- Ajout d'une chose\n",
    "config/ftbquests/quests/chapters/tools.snbt": QUETE_SNBT,
    "kubejs/data/society_trading/shops/banker.json": {"shop_id": "banker", "trades": [
        {"offer": {"item": "society:pig_race_ticket", "count": 1}},
        {"offer": {"item": "society:cheque", "count": 1, "nbt": "{v:1}"}},
    ]},
    "config/everycomp-entries.toml": (
        "[types]\n\t[types.leaves_type]\n\t\t[types.leaves_type.autumnity]\n\t\t\tmaple = true\n"
        "\t\t\tred_maple = false\n\t[types.wood_type]\n\t\t[types.wood_type.atmospheric]\n"
        "\t\t\trosewood = true\n[entries]\n\tfoo = true\n"
    ),
}
