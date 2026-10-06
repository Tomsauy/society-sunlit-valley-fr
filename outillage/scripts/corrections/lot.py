"""Le fichier de lot (spec 2 §8) : le périmètre mesuré et les actions proposées, que l'applicateur contrôle puis
écrit tout entier ou pas du tout."""
from __future__ import annotations

import json
from pathlib import Path

TYPES = ("correction", "exception", "retrait", "mot_generique", "trace", "renvoi")
NATURES = ("decisions", "mecanique", "references", "casse", "langue", "retouches", "chasse")
MAX_ACTIONS = 150  # spec 2 §4 : un sous-lot compte au plus 150 actions


class LotInvalide(Exception):
    pass


def charger_lot(chemin) -> dict:
    chemin = Path(chemin)
    try:
        lot = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise LotInvalide(f"{chemin} : illisible ({e})") from e
    valider_lot(lot, str(chemin))
    return lot


def _texte(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


def _objet(v) -> bool:
    return isinstance(v, str) or (isinstance(v, list) and all(isinstance(x, str) for x in v))


def valider_lot(lot, origine="lot") -> None:
    """Refuse (LotInvalide) un lot mal formé, en nommant le champ ; les champs en plus (mesure, constats) sont
    permis."""
    def exiger(condition, probleme):
        if not condition:
            raise LotInvalide(f"{origine} : {probleme}")

    exiger(isinstance(lot, dict), "un objet est attendu")
    exiger(_texte(lot.get("lot")), "« lot » : l'identifiant du sous-lot manque")
    exiger(lot.get("nature") in NATURES, f"« nature » : l'une de {', '.join(NATURES)}")
    exiger(isinstance(lot.get("perimetre"), list) and all(isinstance(c, str) for c in lot["perimetre"]),
           "« perimetre » : une liste de clés")
    actions = lot.get("actions")
    exiger(isinstance(actions, list), "« actions » : une liste")
    exiger(len(actions) <= MAX_ACTIONS, f"{len(actions)} actions : un sous-lot en compte {MAX_ACTIONS} au plus")
    for i, a in enumerate(actions):
        ou = f"action {i}"
        exiger(isinstance(a, dict) and a.get("type") in TYPES, f"{ou} : « type » parmi {', '.join(TYPES)}")
        exiger(_texte(a.get("motif")), f"{ou} : « motif » manque")
        for champ in ("question", "espace"):
            exiger(champ not in a or _texte(a[champ]), f"{ou} : « {champ} » doit être une chaîne non vide")
        exiger("objet" not in a or _objet(a["objet"]), f"{ou} : « objet » : une clé ou une liste de clés")
        exiger("variante" not in a,
               f"{ou} : « variante » : départager les deux corrections proposées, puis retirer le champ")
        if a["type"] == "mot_generique":
            exiger(_texte(a.get("mot")), f"{ou} : « mot » manque")
            continue
        exiger(_texte(a.get("cle")), f"{ou} : « cle » manque")
        if a["type"] == "correction":
            exiger("avant" in a and (a["avant"] is None or isinstance(a["avant"], str)),
                   f"{ou} : « avant » : le texte actuel, ou null pour une clé absente")
            exiger(isinstance(a.get("apres"), str), f"{ou} : « apres » manque")
            exiger(a["avant"] is not None or "espace" in a, f"{ou} : une clé absente demande « espace »")
        elif a["type"] == "trace":
            exiger(isinstance(a.get("fr"), str), f"{ou} : « fr » manque")
        else:  # exception, retrait, renvoi
            exiger(_texte(a.get("controle")), f"{ou} : « controle » manque")
