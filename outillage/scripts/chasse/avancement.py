"""L'avancement de la chasse pour la page de relecture (spec 3 §7) : document etat/chasse.

Chaque zone a un dossier fr-workspace/chasse/zones/<zone>/ dès qu'on l'entame, et un `bilan.json` quand elle est
faite ({signalements, majeurs, mineurs, corriges, lots}). Les mesures viennent de mesure-depart/ et mesure-finale/
(`resultat.json`)."""
from __future__ import annotations

import datetime
import json
from pathlib import Path


def _lire(chemin: Path):
    return json.loads(chemin.read_text(encoding="utf-8")) if chemin.is_file() else None


def etat(zones: list, dossier) -> dict:
    dossier = Path(dossier)
    lignes = []
    for z in zones:
        rep = dossier / "zones" / z["id"]
        bilan = _lire(rep / "bilan.json")
        statut = "faite" if bilan else "en_cours" if rep.is_dir() else "a_faire"
        bilan = bilan or {}
        lignes.append({"id": z["id"], "textes": len(z["textes"]), "statut": statut,
                       **{k: bilan.get(k, 0) for k in ("signalements", "majeurs", "mineurs", "corriges")}})
    mesures = {}
    for cle, nom in (("depart", "mesure-depart"), ("finale", "mesure-finale")):
        r = _lire(dossier / nom / "resultat.json")
        if r:
            mesures[cle] = {"n": r["n"], "majeurs": r["majeurs"], "borne": r["borne_texte"], "critere": r["critere"]}
    return {"maj": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "mesures": mesures,
            "zones": lignes}
