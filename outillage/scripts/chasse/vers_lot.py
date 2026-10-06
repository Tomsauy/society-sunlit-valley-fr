"""Des verdicts aux lots (spec 3 §6) : chaque défaut confirmé devient une correction d'un lot de l'applicateur du
sous-projet 2 (corrections/applicateur.py), nature « chasse », 150 actions au plus par lot."""
from __future__ import annotations

from coherence.corpus import CLE_JOURNAL
from corrections.lot import MAX_ACTIONS

from .paquets import DEFAUTS


def _remplacer_lignes(journal: str, lignes: dict) -> str:
    """Le journal avec ses lignes (numéro base 1 -> texte) remplacées ; le reste, sauts de ligne compris, intact."""
    morceaux = journal.split("\n")
    for numero, texte in lignes.items():
        if not 0 < numero <= len(morceaux):
            raise ValueError(f"ligne {numero} hors du journal ({len(morceaux)} lignes)")
        morceaux[numero - 1] = texte
    return "\n".join(morceaux)


def actions(verdicts: dict, textes: dict, journal_fr: str, source: str) -> tuple:
    """(actions, écartés). Une correction par défaut confirmé ; les lignes du journal se regroupent en une seule
    correction de la clé « journal » (l'applicateur refuse deux corrections d'une même clé). Écartés : questions,
    désaccords en attente, textes sortis de l'inventaire, textes changés depuis que les relecteurs les ont lus (leur
    correction partirait d'un texte périmé)."""
    resultat, ecartes, journal = [], [], {}
    lignes = journal_fr.split("\n")
    for i, v in sorted(verdicts.items()):
        if v["classe"] not in DEFAUTS:
            if v.get("question"):
                ecartes.append(i)  # une question posée ne se perd pas, même sur un texte jugé correct
            continue
        if v.get("question") or i not in textes or "fr" not in v or v["fr"] != textes[i].fr:
            ecartes.append(i)
            continue
        motif = f"[{source}] {v['classe']} : {v['raison']}"
        if i.startswith(CLE_JOURNAL + "#"):
            n = int(i.split("#", 1)[1])
            if not 0 < n <= len(lignes) or lignes[n - 1] != v["fr"]:
                ecartes.append(i)  # la ligne n'est plus celle que les relecteurs ont lue
                continue
            journal[n] = (v["correction"], motif, v.get("variante"))
            continue
        action = {"type": "correction", "cle": i, "avant": textes[i].fr, "apres": v["correction"], "motif": motif}
        if v.get("variante"):
            action["variante"] = v["variante"]
        resultat.append(action)
    if journal:
        action = {"type": "correction", "cle": CLE_JOURNAL, "avant": journal_fr,
                  "apres": _remplacer_lignes(journal_fr, {n: c for n, (c, _, _) in journal.items()}),
                  "motif": " ; ".join(f"ligne {n} : {m}" for n, (_, m, _) in sorted(journal.items()))}
        variantes = {n: w for n, (_, _, w) in sorted(journal.items()) if w}
        if variantes:
            action["variante"] = variantes  # le lot est refusé tant que l'auteur ne l'a pas départagée
        resultat.append(action)
    ecartes += [i for i, v in sorted(verdicts.items()) if v["classe"] == "en_attente"]
    return resultat, ecartes


def lots(base: str, liste: list, criteres: dict, taille: int = MAX_ACTIONS) -> list:
    """Les lots « <base>-01 », « <base>-02 »… de `taille` actions au plus, au format de corrections/lot.py."""
    return [{"lot": f"{base}-{n + 1:02d}", "nature": "chasse", "mesure": {"criteres": criteres},
             "perimetre": sorted({a["cle"] for a in liste[i:i + taille]}), "constats": [], "actions": liste[i:i + taille]}
            for n, i in enumerate(range(0, len(liste), taille))]
