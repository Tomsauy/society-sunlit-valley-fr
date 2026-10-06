"""Une entrée du glossaire, écrite aux deux endroits qui la portent : la liste `glossaire` de provenance.json et
GLOSSAIRE.md, tenu à la main (spec 2 §6)."""
from __future__ import annotations

import json
import re
from pathlib import Path

SECTION = "## Décisions de la fiche du 30/09/2026"


def fixer(espace, en, fr, raison) -> str:
    """Donne à `en` la traduction `fr`. Dans provenance.json, remplace les entrées de même anglais (casse exacte :
    « ADD » et « Add » sont deux termes) ou en ajoute une ; une entrée qui ne diffère que par la casse est signalée
    en avertissement, jamais écrasée ; dans GLOSSAIRE.md, remplace les lignes de tableau dont la première cellule est `en`, ou en
    ajoute une à la section des décisions de la fiche. Rend ce qui a été fait."""
    espace = Path(espace)
    chemin = espace / "provenance.json"
    provenance = json.loads(chemin.read_text(encoding="utf-8"))
    entrees = [e for e in provenance.get("glossaire", []) if e.get("en") == en]
    proches = [e["en"] for e in provenance.get("glossaire", []) if e.get("en", "") != en and e.get("en", "").lower() == en.lower()]
    for e in entrees:
        e.update(fr=fr, garde_anglais=False, origine="décision de la fiche", raison=raison)
    if not entrees:
        provenance.setdefault("glossaire", []).append({"en": en, "fr": fr, "garde_anglais": False,
                                                       "origine": "décision de la fiche", "raison": raison})
    chemin.write_text(json.dumps(provenance, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    md = espace / "GLOSSAIRE.md"
    texte = md.read_text(encoding="utf-8")
    ligne = re.compile(rf"^\| ({re.escape(en)}) \| [^|\n]* \| [^|\n]* \|$", re.M)
    texte, n = ligne.subn(lambda m: f"| {m.group(1)} | {fr} | {raison} |", texte)
    if not n:
        if SECTION not in texte:
            texte = texte.rstrip("\n") + f"\n\n{SECTION}\n\n| Anglais | Français | Décision |\n|---|---|---|\n"
        texte = texte.rstrip("\n") + f"\n| {en} | {fr} | {raison} |\n"
    md.write_text(texte, encoding="utf-8")
    rendu = f"provenance.json : {len(entrees) or 'une nouvelle'} entrée(s) ; GLOSSAIRE.md : {n or 'une nouvelle'} ligne(s)"
    if proches:
        rendu += f"\nAvertissement : entrée proche, ne différant que par la casse, laissée intacte : {', '.join(proches)}"
    return rendu
