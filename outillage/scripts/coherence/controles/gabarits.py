"""Contrôle gabarits : rien de genré ni d'élidé devant un %s qui reçoit un nom d'objet, ni « en »
ou « au » devant une saison. Le type de chaque argument vient des scripts (corpus.arguments) ou de
gabarits.json, qui prime ; un déterminant devant un %s de type inconnu est signalé.
"""
from __future__ import annotations

import re

from ..modele import BLOQUANT, SIGNALE, Constat

NOM = "gabarits"
MARQUE = re.compile(r"%%|%(?:(\d+)\$)?s")
DETERMINANT = re.compile(r"(?i)(?:^|\W)(le|la|les|un|une|du|des|au|aux|ce|cet|cette|ces|mon|ma|mes|ton|ta|tes"
                         r"|son|sa|ses|notre|votre|leur|leurs|de la|l'|d')\s*$")
GENRES = {"le", "la", "un", "une", "du", "au", "ce", "cet", "cette", "mon", "ma", "ton", "ta", "son", "sa",
          "de la", "l'", "d'"}
DEVANT_SAISON = re.compile(r"(?i)\b(en|au)\s+$")


def verifier(corpus, registre, config, options) -> list:
    constats = []
    for cle, fr in corpus.textes_projet():
        types = config.gabarits.get(cle, corpus.arguments.get(cle))
        suivant = 0
        for m in MARQUE.finditer(fr):
            if m.group(0) == "%%":
                continue
            if m.group(1):
                rang = int(m.group(1)) - 1
            else:
                rang, suivant = suivant, suivant + 1
            avant = fr[:m.start()]
            genres = set(types[rang]) if types and rang < len(types) else set()
            det = DETERMINANT.search(avant)
            mot = det.group(1).lower() if det else ""
            if mot in GENRES and "nom_objet" in genres:
                constats.append(Constat(NOM, cle, BLOQUANT, actuel=fr,
                                        detail=f"« {det.group(1)} » devant un %s qui reçoit un nom d'objet : "
                                               "son genre et son initiale varient"))
            elif DEVANT_SAISON.search(avant) and "saison" in genres:
                constats.append(Constat(NOM, cle, BLOQUANT, actuel=fr,
                                        detail="« en » ou « au » devant une saison : « en été » mais « au printemps »"))
            elif mot and types is None:
                constats.append(Constat(NOM, cle, SIGNALE, actuel=fr,
                                        detail=f"« {det.group(1)} » devant un %s dont l'argument est inconnu : "
                                               "le déclarer dans gabarits.json"))
    return constats
