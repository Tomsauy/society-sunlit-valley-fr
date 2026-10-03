"""Le vocabulaire commun des contrôles : un constat et ses statuts, et les options d'un passage (LanguageTool,
règles en attente de décision que les tests activent)."""
from __future__ import annotations

from dataclasses import asdict, dataclass

BLOQUANT = "bloquant"
SIGNALE = "signale"


@dataclass(frozen=True)
class Constat:
    controle: str
    cle: str
    statut: str
    actuel: str = ""
    attendu: str = ""
    detail: str = ""
    preuve: str = ""
    objet: object = ""  # ce que vise le constat : une clé, une règle, une forme ; un groupe d'homonymes : ses clés (tuple)

    def en_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Options:
    languagetool: bool = False
    url_languagetool: str = "http://localhost:8081/v2/check"
    toutes_regles: bool = False  # active les règles en attente de décision (tests seulement)
