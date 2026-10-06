"""Signalements, avis et verdicts (spec 3 §4 et §5).

Un signalement naît d'un écart de F1 ou d'une accroche de F2. Deux relecteurs indépendants rendent chacun un avis
(classe, raison, correction, preuves, question éventuelle). Même classe : le verdict est pris (« accord ») ; classes
différentes : un troisième tranche (« tiers »). Quand les deux relecteurs s'accordent sur un défaut mais pas sur sa
correction, le verdict garde celle du premier et propose l'autre en « variante », que l'auteur du lot départage.
Un avis qui pose une question en fait une question pour l'utilisateur : le texte attend sa réponse."""
from __future__ import annotations

from .paquets import DEFAUTS


def signalements(comparaison: dict, lecture: dict) -> list:
    """[{id, filets, notes}] : les textes que F1 (écart) ou F2 (accroche) signalent, triés."""
    resultat = {}
    for filet, rendus, drapeau in (("F1", comparaison, "ecart"), ("F2", lecture, "accroche")):
        for i, x in rendus.items():
            if x.get(drapeau):
                s = resultat.setdefault(i, {"id": i, "filets": [], "notes": {}})
                s["filets"].append(filet)
                s["notes"][filet] = x.get("note", "")
    return [resultat[i] for i in sorted(resultat)]


def desaccords(avis_a: dict, avis_b: dict) -> list:
    """Les ids où les deux avis n'ont pas la même classe ; refuse deux avis qui ne portent pas sur les mêmes textes."""
    if set(avis_a) != set(avis_b):
        raise ValueError(f"les deux avis ne portent pas sur les mêmes textes : {len(set(avis_a) ^ set(avis_b))} écart(s)")
    return sorted(i for i in avis_a if avis_a[i]["classe"] != avis_b[i]["classe"])


def _verdict(i, avis, source, autre=None, fr=None, plus=()) -> dict:
    v = {"id": i, "classe": avis["classe"], "raison": avis["raison"], "correction": avis.get("correction", ""),
         "preuves": list(avis.get("preuves", [])), "source": source}
    if fr is not None:
        v["fr"] = fr  # le texte que les relecteurs ont lu : le lot refuse de corriger un texte qui a changé depuis
    if autre is not None and v["classe"] in DEFAUTS and autre.get("correction") and autre["correction"] != v["correction"]:
        v["variante"] = autre["correction"]
    questions = [a["question"] for a in ([avis] + ([autre] if autre else []) + list(plus)) if a.get("question")]
    if questions:
        v["question"] = " / ".join(dict.fromkeys(questions))
    return v


def verdicts(avis_a: dict, avis_b: dict, avis_c: dict = None, vus: dict = None) -> dict:
    """{id : verdict}. Sans avis du tiers pour un désaccord, le verdict est « en_attente ». `vus` : {id : français
    lu par les relecteurs}, gardé dans chaque verdict."""
    avis_c, vus = avis_c or {}, vus or {}
    resultat = {}
    a_trancher = set(desaccords(avis_a, avis_b))
    for i in sorted(avis_a):
        if i not in a_trancher:
            resultat[i] = _verdict(i, avis_a[i], "accord", avis_b[i], vus.get(i))
        elif i in avis_c:
            resultat[i] = _verdict(i, avis_c[i], "tiers", fr=vus.get(i), plus=(avis_a[i], avis_b[i]))
        else:
            resultat[i] = {"id": i, "classe": "en_attente", "source": "desaccord"}
    return resultat


def bilan(verdicts_: dict) -> dict:
    """Comptes par classe, questions et désaccords non tranchés."""
    compte = {}
    for v in verdicts_.values():
        compte[v["classe"]] = compte.get(v["classe"], 0) + 1
    compte["questions"] = sum(1 for v in verdicts_.values() if v.get("question"))
    return compte
