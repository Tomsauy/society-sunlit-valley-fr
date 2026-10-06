"""La mesure (spec 3 §1, §4) : le taux de défauts majeurs d'un tirage relu en double, sa borne haute, par zone et en
tout ; et le banc des filets (phase 1) : précision et rappel de F1, de F2 et des deux réunis."""
from __future__ import annotations

import random

from .stats import borne_haute, critere_tenu, en_pourcent

# Règles de décision du banc (phase 1), écrites avant de le lancer. Chiffres de l'essai du 28/09 (spec 1 §16) : F1
# 4 défauts sur 10, 0 fausse alerte sur 40 ; F2 8 sur 10, 18 fausses alertes sur 40 ; réunis 9 sur 10.
RAPPEL_MIN_F2 = 0.60        # F2 est le filet large : moins de 60 % des défauts majeurs du banc, sa consigne est revue
GAIN_MIN_F1 = 0.05          # F1 coûte deux passes : gardé s'il ajoute 5 points de rappel à F2, ou un majeur que F2 manque
FAUSSES_ALERTES_MAX = 0.15  # au-delà, ~7 600 signalements sur 50 600 textes, donc ~15 000 avis : la consigne est resserrée


def pourcent(x: float) -> str:
    """« 45 % » : arrondi à l'unité, espace avant le signe."""
    return f"{100 * x:.0f} %"


MORTE = "jamais affiché :"


def est_morte(verdict: dict) -> bool:
    """Une clé morte : jugée `correct` avec une raison qui commence par « jamais affiché : » (spec 3 §3). Elle sort de
    la mesure et va dans mortes.json."""
    return str(verdict.get("raison", "")).strip().startswith(MORTE)


def resultat(tirage: list, verdicts: dict) -> dict:
    """{n, majeurs, mineurs, corrects, borne, borne_texte, critere, par_zone}. Refuse un tirage dont un texte n'a pas
    de verdict tranché."""
    manquants = [t["id"] for t in tirage if verdicts.get(t["id"], {}).get("classe") not in ("majeur", "mineur", "correct")]
    if manquants:
        raise ValueError(f"{len(manquants)} texte(s) sans verdict tranché, dont {manquants[0]}")
    def compter(ids):
        mortes = [i for i in ids if est_morte(verdicts[i])]
        ids = [i for i in ids if i not in set(mortes)]
        classes = [verdicts[i]["classe"] for i in ids]
        n, k = len(classes), classes.count("majeur")
        borne = borne_haute(k, n)
        return {"n": n, "majeurs": k, "mineurs": classes.count("mineur"), "corrects": classes.count("correct"),
                "borne": borne, "borne_texte": en_pourcent(borne), "critere": critere_tenu(k, n),
                "mortes": len(mortes), "ids_mortes": sorted(mortes)}
    par_zone = {}
    for t in tirage:
        par_zone.setdefault(t["zone"], []).append(t["id"])
    tout = compter([t["id"] for t in tirage])
    tout["par_zone"] = {z: compter(ids) for z, ids in sorted(par_zone.items())}
    return tout


def choisir_banc(verdicts: dict, graine: str) -> dict:
    """Les textes du banc : tous les défauts (majeurs et mineurs) de la mesure, et autant de textes corrects tirés avec
    la graine. Refuse un banc impossible (plus de défauts que de textes corrects)."""
    defauts = sorted(i for i, v in verdicts.items() if v["classe"] in ("majeur", "mineur"))
    corrects = sorted(i for i, v in verdicts.items() if v["classe"] == "correct" and not est_morte(v))
    if len(defauts) > len(corrects):
        raise ValueError(f"{len(defauts)} défauts pour {len(corrects)} textes corrects : banc impossible")
    return {"graine": graine, "defauts": defauts, "majeurs": sorted(i for i in defauts if verdicts[i]["classe"] == "majeur"),
            "corrects": sorted(random.Random(graine).sample(corrects, len(defauts)))}


def rendement(signales: set, banc: dict) -> dict:
    """Précision, rappel (tous défauts et majeurs) et taux de fausses alertes d'un filet sur le banc."""
    defauts, majeurs, corrects = set(banc["defauts"]), set(banc["majeurs"]), set(banc["corrects"])
    signales = set(signales) & (defauts | corrects)
    vrais = signales & defauts
    part = lambda a, b: a / b if b else 0.0  # noqa: E731
    return {"signales": len(signales), "vrais": len(vrais), "precision": part(len(vrais), len(signales)),
            "rappel": part(len(vrais), len(defauts)), "rappel_majeurs": part(len(signales & majeurs), len(majeurs)),
            "fausses_alertes": part(len(signales & corrects), len(corrects)), "majeurs_vus": sorted(signales & majeurs)}


def decider(f1: dict, f2: dict, reunis: dict) -> dict:
    """{filet : (décision, raison)} selon les règles écrites plus haut. Décisions : garder, resserrer (consigne revue,
    banc relancé une fois), retirer."""
    decisions = {}
    if f2["rappel_majeurs"] < RAPPEL_MIN_F2:
        decisions["F2"] = ("resserrer", f"rappel des majeurs {pourcent(f2['rappel_majeurs'])} < {pourcent(RAPPEL_MIN_F2)}")
    elif f2["fausses_alertes"] > FAUSSES_ALERTES_MAX:
        decisions["F2"] = ("resserrer", f"fausses alertes {pourcent(f2['fausses_alertes'])} > {pourcent(FAUSSES_ALERTES_MAX)}")
    else:
        decisions["F2"] = ("garder", f"rappel des majeurs {pourcent(f2['rappel_majeurs'])}, "
                                     f"fausses alertes {pourcent(f2['fausses_alertes'])}")
    gain = reunis["rappel"] - f2["rappel"]
    propres = sorted(set(f1["majeurs_vus"]) - set(f2["majeurs_vus"]))
    if gain < GAIN_MIN_F1 and not propres:
        decisions["F1"] = ("retirer", f"gain de rappel {pourcent(gain)} < {pourcent(GAIN_MIN_F1)}, aucun majeur que F2 manque")
    elif f1["fausses_alertes"] > FAUSSES_ALERTES_MAX:
        decisions["F1"] = ("resserrer", f"fausses alertes {pourcent(f1['fausses_alertes'])} > {pourcent(FAUSSES_ALERTES_MAX)}")
    else:
        decisions["F1"] = ("garder", f"gain de rappel {pourcent(gain)}, {len(propres)} majeur(s) que F2 manque")
    return decisions


def rendement_pack(signalements: list, verdicts: dict) -> dict:
    """Sur tout le pack (phase 2) : pour F1, F2 et les deux réunis, signalements, défauts confirmés, majeurs et
    précision. `signalements` et `verdicts` : ceux de toutes les zones réunis."""
    resultat = {}
    for nom, garder in (("F1", lambda f: "F1" in f), ("F2", lambda f: "F2" in f), ("F1 + F2", lambda f: True)):
        ids = [s["id"] for s in signalements if garder(s["filets"])]
        classes = [verdicts.get(i, {}).get("classe") for i in ids]
        confirmes = sum(c in ("majeur", "mineur") for c in classes)
        resultat[nom] = {"signales": len(ids), "confirmes": confirmes, "majeurs": classes.count("majeur"),
                         "precision": confirmes / len(ids) if ids else 0.0}
    return resultat


def projection(r: dict, textes: int, taux_defauts: float) -> int:
    """Signalements attendus sur tout le pack : fausses alertes sur les textes corrects, plus les défauts vus."""
    return round(r["fausses_alertes"] * textes * (1 - taux_defauts) + r["rappel"] * textes * taux_defauts)
