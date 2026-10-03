"""Le rapport : ce qui bloque, ce qui est signalé, ce que couvrent les exceptions et la dette."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, replace

from .modele import BLOQUANT


def empreinte(valeur: str) -> str:
    return hashlib.sha1((valeur or "").encode("utf-8")).hexdigest()[:12]


def empreinte_du_constat(constat, valeur_de) -> str:
    """L'empreinte que la dette photographie : le français de la clé ; pour un constat du contrôle homonymes, ce
    français et les variantes du groupe (constat.actuel), qu'un membre modifié change aussi."""
    valeur = valeur_de(constat.cle) or ""
    if constat.controle == "homonymes":
        valeur += "\n" + constat.actuel
    return empreinte(valeur)


def objet_de(valeur):
    """L'objet d'un constat ou d'une entrée, comparable : une liste (les clés d'un groupe d'homonymes, lues du JSON)
    devient un tuple."""
    return tuple(valeur) if isinstance(valeur, (list, tuple)) else (valeur or "")


def triplet(entree) -> tuple:
    """(contrôle, clé, objet) : ce qui identifie une entrée de dette."""
    return entree.get("controle"), entree.get("cle"), objet_de(entree.get("objet"))


def dette_en_hausse(dette, base) -> list:
    """Les entrées de `dette` absentes de la dette de référence `base` : la dette ne fait que décroître (spec §10)."""
    connus = {triplet(e) for e in base}
    return [e for e in dette if triplet(e) not in connus]


def dette_modifiee(dette, base) -> list:
    """Les entrées de `dette` dont le triplet est dans `base` mais avec une empreinte différente : qui touche une
    clé la corrige (spec §10), réécrire l'empreinte sans corriger le défaut ne doit pas blanchir l'entrée. Une
    entrée retirée de `dette` reste permise : elle n'est plus là pour être comparée."""
    empreintes = {}
    for e in base:
        empreintes.setdefault(triplet(e), set()).add(e.get("empreinte"))
    return [e for e in dette if triplet(e) in empreintes and e.get("empreinte") not in empreintes[triplet(e)]]


@dataclass
class Resultat:
    bloquants: list = field(default_factory=list)
    signales: list = field(default_factory=list)
    en_dette: list = field(default_factory=list)
    couverts: list = field(default_factory=list)
    orphelines: list = field(default_factory=list)
    sans_motif: list = field(default_factory=list)
    dette_resolue: list = field(default_factory=list)
    provisoires: list = field(default_factory=list)       # exceptions en attente d'une question (spec 2 §7)
    renvoyees: list = field(default_factory=list)         # renvois appariés à une entrée de dette
    renvois_orphelins: list = field(default_factory=list)  # renvois sans entrée de dette

    @property
    def code(self) -> int:
        return 1 if self.bloquants or self.sans_motif else 0


def _couvre(exc, constat, valeur_de) -> bool:
    """Une exception couvre les constats de son contrôle sur sa clé, restreints à son objet si elle en a un ; avec une
    empreinte (spec 2 §7), tant que le texte de la clé n'a pas changé."""
    if objet_de(exc.get("objet")) not in ("", objet_de(constat.objet)):
        return False
    return not exc.get("empreinte") or exc["empreinte"] == empreinte(valeur_de(constat.cle) or "")


def appliquer(constats, exceptions, dette, valeur_de, controles_lances, renvois=()) -> Resultat:
    """Range chaque constat ; une exception sans motif ne couvre rien et fait échouer. Une entrée de dette ne vaut que
    pour le constat qu'elle a photographié, même contrôle, même clé, même objet : couvert si la valeur n'a pas changé,
    bloquant sinon ; tout autre constat de la clé reste ce qu'il est, et seule l'entrée appariée est utile."""
    r = Resultat()
    lances = set(controles_lances)
    exceptions_par_cle = {}
    valides = []
    for exc in exceptions:
        if not str(exc.get("motif", "")).strip():
            r.sans_motif.append(exc)
            continue
        if exc.get("epingle"):
            continue
        valides.append(exc)
        exceptions_par_cle.setdefault((exc.get("controle"), exc.get("cle")), []).append(exc)
    dette_par_triplet = {}
    for i, entree in enumerate(dette):
        dette_par_triplet.setdefault(triplet(entree), []).append(i)
    exceptions_utiles, dette_utile = set(), set()
    for c in constats:
        exc = next((e for e in exceptions_par_cle.get((c.controle, c.cle), ()) if _couvre(e, c, valeur_de)), None)
        if exc is not None:
            exceptions_utiles.add(id(exc))
            r.couverts.append((c, exc))
            continue
        indices = dette_par_triplet.get((c.controle, c.cle, objet_de(c.objet)), [])
        if indices:
            dette_utile.update(indices)
            actuelle = empreinte_du_constat(c, valeur_de)
            if any(dette[i].get("empreinte") == actuelle for i in indices):
                r.en_dette.append(c)
                continue
            c = replace(c, statut=BLOQUANT,
                        detail=f"{c.detail} — valeur modifiée depuis la dette : corriger le défaut")
        (r.bloquants if c.statut == BLOQUANT else r.signales).append(c)
    r.orphelines = [e for e in valides if id(e) not in exceptions_utiles and e.get("controle") in lances]
    r.dette_resolue = [e for i, e in enumerate(dette) if i not in dette_utile and e.get("controle") in lances]
    r.provisoires = [e for e in valides if e.get("question")]
    connues = {triplet(e) for e in dette}
    for renvoi in renvois:
        (r.renvoyees if triplet(renvoi) in connues else r.renvois_orphelins).append(renvoi)
    return r


def obstacles_a_la_cloture(r, dette, renvois) -> list:
    """Ce qui empêche de clore le sous-projet 2 (spec 2 §13, critère 1) ; une liste vide quand rien."""
    renvoyes = {triplet(e) for e in renvois}
    obstacles = []
    if r.bloquants or r.sans_motif:
        obstacles.append(f"{len(r.bloquants)} bloquant(s) et {len(r.sans_motif)} exception(s) sans motif")
    restantes = [e for e in dette if triplet(e) not in renvoyes]
    if restantes:
        obstacles.append(f"{len(restantes)} entrée(s) de dette sans renvoi au sous-projet 3")
    if r.provisoires:
        obstacles.append(f"{len(r.provisoires)} exception(s) provisoire(s) : des questions attendent leur réponse")
    if r.orphelines:
        obstacles.append(f"{len(r.orphelines)} exception(s) orpheline(s), à retirer")
    if r.renvois_orphelins:
        obstacles.append(f"{len(r.renvois_orphelins)} renvoi(s) orphelin(s), à retirer")
    if r.signales:
        obstacles.append(f"{len(r.signales)} signalement(s) sans suite : corriger, ou déclarer voulu par une exception")
    return obstacles
