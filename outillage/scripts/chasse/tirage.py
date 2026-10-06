"""Les tirages de la mesure (spec 3 §4, phases 1 et 3) : stratifiés par zone, au moins MINIMUM textes par zone, le
reste réparti à proportion de ce qui reste dans chaque zone, avec une graine écrite."""
from __future__ import annotations

import random

MINIMUM = 5


def quotas(tailles: dict, n: int, minimum: int = MINIMUM) -> dict:
    """{zone : textes à tirer}. Chaque zone reçoit min(minimum, sa taille) ; le reste se répartit à proportion de la
    place restante de chaque zone (plus forts restes, égalités départagées par l'identifiant de zone)."""
    total = sum(tailles.values())
    if not 0 < n <= total:
        raise ValueError(f"tirer {n} textes sur {total} : impossible")
    base = {z: min(minimum, t) for z, t in tailles.items()}
    reste = n - sum(base.values())
    if reste < 0:
        raise ValueError(f"{n} textes ne suffisent pas à en tirer {minimum} par zone ({sum(base.values())} requis)")
    place = {z: tailles[z] - base[z] for z in tailles}
    total_place = sum(place.values())
    parts = {z: (reste * place[z] / total_place if total_place else 0.0) for z in tailles}
    resultat = {z: base[z] + int(parts[z]) for z in tailles}
    manque = n - sum(resultat.values())
    for z in sorted(tailles, key=lambda z: (-(parts[z] - int(parts[z])), z))[:manque]:
        resultat[z] += 1
    return resultat


def tirer(zones: list, n: int, graine: str, minimum: int = MINIMUM) -> list:
    """[{id, zone}] : le tirage, reproductible par la graine (zones dans l'ordre de zones.json, textes triés)."""
    q = quotas({z["id"]: len(z["textes"]) for z in zones}, n, minimum)
    rng = random.Random(graine)
    tirage = []
    for z in zones:
        for t in sorted(rng.sample(sorted(z["textes"]), q[z["id"]])):
            tirage.append({"id": t, "zone": z["id"]})
    return tirage
