"""L'échantillon d'un sous-lot pour la page de relecture, et la lecture des verdicts (spec 2 §9)."""
from __future__ import annotations

import json
import random
from pathlib import Path

TAILLE = 30


def echantillonner(actions, lot_id, taille=TAILLE) -> list:
    """Les indices de `taille` actions tirées au hasard, graine = identifiant du sous-lot, pour qu'on puisse
    reproduire le tirage ; toutes si le sous-lot en compte moins."""
    indices = list(range(len(actions)))
    if len(indices) <= taille:
        return indices
    return sorted(random.Random(lot_id).sample(indices, taille))


def element(n, action, anglais_de, texte_de) -> dict:
    """Une action telle que la page la montre : clé, anglais, avant, après, type, motif."""
    type_ = action["type"]
    cle = action.get("cle") or action.get("mot", "")
    if type_ == "mot_generique":
        anglais, avant, apres = "", "", ""
    elif type_ == "correction":
        anglais, avant, apres = anglais_de(cle) or "", action["avant"] or "", action["apres"]
    elif type_ == "trace":
        anglais, avant, apres = anglais_de(cle) or "", action["fr"], action["fr"]
    else:  # exception, retrait, renvoi : le texte reste tel quel
        anglais, avant, apres = anglais_de(cle) or "", texte_de(cle) or "", ""
    entree = {"n": n, "cle": cle, "anglais": anglais, "avant": avant, "apres": apres, "type": type_,
              "motif": action["motif"]}
    if "controle" in action:
        entree["controle"] = action["controle"]
    return entree


def document(lot, titre, resume, dette_avant, dette_apres, attend_verdict, anglais_de, texte_de) -> dict:
    """Le document `lots/<id>` de la page de relecture."""
    actions = lot["actions"]
    return {
        "id": lot["lot"],
        "titre": titre,
        "nature": lot["nature"],
        "statut": "echantillon",
        "attend_verdict": bool(attend_verdict),
        "dette_avant": dette_avant,
        "dette_apres": dette_apres,
        "resume": resume,
        "actions": len(actions),
        "exceptions": [{"cle": a["cle"], "controle": a["controle"], "motif": a["motif"],
                        **({"question": a["question"]} if a.get("question") else {})}
                       for a in actions if a["type"] == "exception"],
        "echantillon": [element(n, actions[i], anglais_de, texte_de)
                        for n, i in enumerate(echantillonner(actions, lot["lot"]), start=1)],
    }


def lire_verdicts(dossier, page) -> dict:
    """Les verdicts téléchargés (outil ArtifactData, collection verdicts : un fichier <lot>-<n>.json par action,
    dans <dossier>/verdicts/) face à l'échantillon de la page : {lot, complet, verdicts, refus}.
    Un élément sans verdict est bon (la page ne pose plus de bouton « Bon ») : seul « refus » est à traiter,
    donc `complet` vaut True dès que le lot est publié."""
    lot_id = page["id"]
    verdicts = {}
    for chemin in sorted(Path(dossier).glob(f"verdicts/{lot_id}-*.json")):
        n = chemin.stem[len(lot_id) + 1:]
        if n.isdigit():
            verdicts[int(n)] = json.loads(chemin.read_text(encoding="utf-8"))
    numeros = [e["n"] for e in page["echantillon"]]
    refus = [dict(e, commentaire=verdicts[e["n"]].get("commentaire", "")) for e in page["echantillon"]
             if verdicts.get(e["n"], {}).get("verdict") == "refus"]
    return {"lot": lot_id,
            "complet": True,
            "verdicts": {str(n): verdicts[n] for n in sorted(verdicts) if n in numeros},
            "refus": refus}
