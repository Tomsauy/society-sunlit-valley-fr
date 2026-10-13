"""Le glossaire : la liste `glossaire` de provenance.json fait foi ; GLOSSAIRE.md et KEEP-ENGLISH.md en sont la
lecture, régénérée à chaque changement, jamais éditée à la main. Le contrôle `glossaire` du vérificateur confronte la liste à la
traduction."""
from __future__ import annotations

import json
import re
from pathlib import Path

# Origine d'une entrée → section de GLOSSAIRE.md, dans l'ordre des sections. Une origine inconnue va aux arbitrages.
SECTIONS = (
    ("Minecraft vanilla (officiel Mojang)", "Minecraft (traduction officielle de Mojang)"),
    ("traduction officielle du mod", "Traductions officielles des mods"),
    ("terminologie Stardew Valley FR", "Stardew Valley (terminologie officielle française)"),
    ("décision de l'utilisateur", "Décisions de l'utilisateur"),
    ("arbitrage de traduction", "Arbitrages de traduction"),
    ("contrainte d'affichage", "Formes courtes imposées par la largeur d'affichage"),
    ("identique en français", "Mots qui s'écrivent comme en anglais"),
    ("placeholder technique", "Placeholders techniques"),
)
ORIGINES = {origine for origine, _ in SECTIONS}
DECISION = "décision de l'utilisateur"
LEGENDE = ("Dans les raisons, « jar » désigne la traduction française qu'un mod embarque dans son fichier .jar "
           "(« jar Quark » : celle de Quark) ; « vanilla » ou « vanilla_fr », le français de Minecraft par Mojang ; "
           "« coréen », « ko », « chinois », les traductions du pack qui servent de témoins.")

# Renvois aux lots, fiches et réponses datées : la trace en reste dans provenance.json, pas dans la lecture.
TRACES = (
    re.compile(r"^fiche du sous-projet \d+ ?: ?[\w-]+(?:, garder)?(?: \(option [^)]*\))?(?: ?[;,:] ?|$)"),
    re.compile(r"^fiche du \d\d/\d\d(?:, question [\w-]+)? ?: ?(?:[\w-]+$)?"),
    re.compile(r"^réponse (?:de l'utilisateur )?du \d\d/\d\d(?: à la question [\w-]+)?(?: ?\([\w-]+\))? ?:? ?"
               r"(?:[\w-]+-[\w-]+, )?"),
    re.compile(r"^lot [\w-]+(?:, verdict [^:]*)? ?: ?", re.I),
    re.compile(r" ?;? ?lot [\w-]+$"),
    re.compile(r" ?;? ?(?:par la )?fiche du sous-projet \d+ ?: ?[\w-]+"),
    re.compile(r" ?\((?:fiche|réponse|lot) [^)]*\)"),
)


def entrees(espace) -> list:
    """Les entrées du glossaire, telles que provenance.json les porte."""
    provenance = json.loads((Path(espace) / "provenance.json").read_text(encoding="utf-8"))
    return provenance.get("glossaire", [])


def termes_gardes(espace) -> set:
    """Les anglais que le glossaire garde tels quels."""
    return {e["en"] for e in entrees(espace) if e.get("garde_anglais")}


def raison_lisible(raison: str) -> str:
    """La raison sans ses renvois aux lots et aux fiches ; vide si elle n'était qu'un renvoi."""
    texte = raison or ""
    for motif in TRACES:
        texte = motif.sub("", texte)
    texte = texte.strip(" ;,:")
    return texte[:1].upper() + texte[1:] if texte else ""


def _cellule(texte: str) -> str:
    return texte.replace("|", "\\|").replace("\n", " ")


def ecrire_md(espace) -> int:
    """Régénère GLOSSAIRE.md depuis provenance.json ; rend le nombre d'entrées écrites."""
    espace = Path(espace)
    glossaire = json.loads((espace / "provenance.json").read_text(encoding="utf-8")).get("glossaire", [])
    def garde(e):
        return e.get("garde_anglais") and e.get("origine") != "placeholder technique"

    gardes = [e for e in glossaire if garde(e)]
    par_section = {titre: [] for _, titre in SECTIONS}
    titres = dict(SECTIONS)
    for e in glossaire:
        if not garde(e):
            par_section[titres.get(e.get("origine"), titres["arbitrage de traduction"])].append(e)
    lignes = ["# Glossaire FR — Society: Sunlit Valley", "",
              "Généré par `python3 fr-workspace/scripts/glossaire.py --md` depuis la liste `glossaire` de "
              "`provenance.json`, qui fait foi : ne pas éditer ce fichier à la main. Un même anglais peut avoir "
              "plusieurs entrées, une par sens.", "",
              "Ce que le vérificateur garantit (contrôle `glossaire`) : quand l'anglais d'une entrée est aussi "
              "l'anglais entier d'un texte de notre traduction, l'une des entrées de cet anglais est le français "
              "d'au moins un de ces textes, au pluriel près ; aucune entrée n'écrit la ligature « œ » ; deux entrées "
              "de même anglais et de même sens ne se contredisent pas. Un terme qui n'apparaît qu'à l'intérieur de "
              "textes plus longs (« Copper » dans « Copper Door ») n'est pas confronté mot à mot.", "", LEGENDE, "",
              f"{len(glossaire)} entrées.", ""]

    def tableau(titre, entrees, colonnes):
        lignes.extend([f"## {titre} — {len(entrees)}", "", "| " + " | ".join(colonnes) + " |",
                       "|" + "---|" * len(colonnes)])
        for e in sorted(entrees, key=lambda e: (e["en"].lower(), e.get("sens", ""))):
            note = " ; ".join(x for x in (f"sens : {e['sens']}" if e.get("sens") else "",
                                         raison_lisible(e.get("raison", ""))) if x)
            cellules = [e["en"], e["fr"], note] if len(colonnes) == 3 else [e["en"], note]
            lignes.append("| " + " | ".join(_cellule(c) for c in cellules) + " |")
        lignes.append("")

    tableau("Termes gardés en anglais", gardes, ("Anglais", "Pourquoi"))
    lignes[-1:] = ["", "Détail et emplacements : KEEP-ENGLISH.md.", ""]
    for titre, entrees in par_section.items():
        if entrees:
            tableau(titre, entrees, ("Anglais", "Français", "Sens, raison"))
    (espace / "GLOSSAIRE.md").write_text("\n".join(lignes).rstrip("\n") + "\n", encoding="utf-8")
    _ecrire_keep_english(espace, gardes, [e for e in glossaire if e.get("origine") == "placeholder technique"])
    return len(glossaire)


def _ecrire_keep_english(espace: Path, gardes: list, placeholders: list) -> None:
    """KEEP-ENGLISH.md : les termes que le glossaire garde en anglais, en gras (le vérificateur les lit ainsi,
    coherence/config.py), puis les placeholders techniques."""
    lignes = ["# Termes gardés en anglais", "",
              "Généré par `python3 fr-workspace/scripts/glossaire.py --md` depuis les entrées du glossaire de "
              "`provenance.json` marquées `garde_anglais` : ne pas éditer ce fichier à la main. Les contrôles `casse` "
              "et `anglais_residuel` du vérificateur ne relèvent pas ces termes.", "", LEGENDE, "",
              f"## Termes — {len(gardes)}", "", "| Terme | Pourquoi |", "|---|---|"]
    for e in sorted(gardes, key=lambda e: e["en"].lower()):
        pourquoi = " ; ".join(x for x in (f"sens : {e['sens']}" if e.get("sens") else "",
                                          raison_lisible(e.get("raison", ""))) if x)
        lignes.append(f"| **{_cellule(e['en'])}** | {_cellule(pourquoi)} |")
    lignes += ["", f"## Placeholders techniques, sans texte à traduire — {len(placeholders)}", "", "| Valeur |", "|---|"]
    lignes += [f"| `{e['en']}` |" for e in sorted(placeholders, key=lambda e: e["en"])]
    (espace / "KEEP-ENGLISH.md").write_text("\n".join(lignes) + "\n", encoding="utf-8")


def fixer(espace, en, fr, raison, sens="", garde_anglais=None) -> str:
    """Donne à `en`, dans le sens `sens` (aucun par défaut), la traduction `fr`, puis régénère GLOSSAIRE.md.
    Remplace les entrées de même anglais et de même sens (casse exacte : « ADD » et « Add » sont deux termes) ou en
    ajoute une ; une entrée qui ne diffère que par la casse est signalée en avertissement, jamais écrasée.
    `garde_anglais` n'est changé que s'il est donné. Rend ce qui a été fait."""
    espace = Path(espace)
    chemin = espace / "provenance.json"
    provenance = json.loads(chemin.read_text(encoding="utf-8"))
    glossaire = provenance.setdefault("glossaire", [])
    entrees = [e for e in glossaire if e.get("en") == en and e.get("sens", "") == sens]
    proches = sorted({e["en"] for e in glossaire if e.get("en", "") != en and e.get("en", "").lower() == en.lower()})
    for e in entrees:
        e.update(fr=fr, origine=DECISION, raison=raison)
        if garde_anglais is not None:
            e["garde_anglais"] = garde_anglais
    if not entrees:
        nouvelle = {"en": en, "fr": fr, "garde_anglais": bool(garde_anglais), "origine": DECISION, "raison": raison}
        glossaire.append(dict(nouvelle, sens=sens) if sens else nouvelle)
    chemin.write_text(json.dumps(provenance, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    ecrire_md(espace)
    rendu = f"provenance.json : {len(entrees) or 'une nouvelle'} entrée(s) ; GLOSSAIRE.md régénéré"
    if proches:
        rendu += f"\nAvertissement : entrée proche, ne différant que par la casse, laissée intacte : {', '.join(proches)}"
    return rendu
