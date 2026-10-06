"""Le critère de la spec 3 (§1) : borne haute unilatérale à 95 % de Clopper-Pearson, exacte, sans dépendance."""
from __future__ import annotations

import math

SEUIL = 0.005  # spec 3 §1 : borne haute du taux de défauts majeurs sous 0,5 %


def repartition(k: int, n: int, p: float) -> float:
    """P(X <= k) pour X ~ Binomiale(n, p), somme exacte des termes."""
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 1.0 if k >= n else 0.0
    return min(1.0, sum(math.comb(n, i) * p ** i * (1.0 - p) ** (n - i) for i in range(k + 1)))


def borne_haute(k: int, n: int, confiance: float = 0.95) -> float:
    """La borne haute unilatérale de Clopper-Pearson : le p tel que P(X <= k | n, p) = 1 - confiance.
    k = n rend 1 ; k = 0 rend 1 - (1 - confiance) ** (1 / n). Dichotomie à 1e-12 près."""
    if n <= 0 or not 0 <= k <= n:
        raise ValueError(f"k = {k}, n = {n} : il faut 0 <= k <= n et n > 0")
    if k == n:
        return 1.0
    alpha = 1.0 - confiance
    bas, haut = k / n, 1.0
    while haut - bas > 1e-12:
        milieu = (bas + haut) / 2
        if repartition(k, n, milieu) > alpha:
            bas = milieu
        else:
            haut = milieu
    return haut


def critere_tenu(k: int, n: int) -> bool:
    """Spec 3 §1 : la borne haute à 95 % est sous 0,5 %."""
    return borne_haute(k, n) < SEUIL


def en_pourcent(p: float) -> str:
    """« 0,473 % » : trois décimales, virgule française, espace insécable ordinaire."""
    return f"{100 * p:.3f}".replace(".", ",") + " %"
