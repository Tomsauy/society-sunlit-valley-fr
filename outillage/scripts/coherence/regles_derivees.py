"""Les familles dérivées : un nom qui se déduit d'un autre par un gabarit.

Dans un gabarit, {source} est le nom de la source avec une minuscule initiale (sauf nom propre),
{Source} avec une majuscule, {sources} son pluriel (« Conserve de tomates »), {e} et {s} l'accord
avec la source (« Carangue fumée »). Genre, nombre et pluriel se saisissent dans les accords. « de »
s'élide devant voyelle ou h muet. Les familles en chaîne se rendent de proche en proche : les
oeufs vieillis partent du nom attendu des oeufs, pas de leur valeur actuelle.
"""
from __future__ import annotations

import re

from compare_accents import plier

H_ASPIRES = tuple(plier(h) for h in (
    "hache", "haddock", "hamster", "hanneton", "hareng", "haricot", "hérisson", "hêtre", "hibou",
    "homard", "houblon"))
DE_SUIVI = re.compile(r"\b([Dd])e (\S+)")


def elide(mot: str) -> bool:
    """« de » s'élide-t-il devant ce mot ? Devant voyelle ou h muet ; pas devant y ni h aspiré."""
    p = plier(mot)
    if not p:
        return False
    if p[0] == "h":
        return not p.startswith(H_ASPIRES)
    return p[0] in "aeiou"


def rendre(gabarit: str, source: str, genre: str = "", nombre: str = "", propre: bool = False,
           pluriel: str = "") -> str:
    nom = source if propre else source[:1].lower() + source[1:]
    noms = pluriel if propre else pluriel[:1].lower() + pluriel[1:]
    texte = (gabarit.replace("{sources}", noms).replace("{source}", nom)
             .replace("{Source}", source[:1].upper() + source[1:])
             .replace("{e}", "e" if genre == "f" else "").replace("{s}", "s" if nombre == "p" else ""))
    texte = DE_SUIVI.sub(lambda m: f"{m.group(1)}'{m.group(2)}" if elide(m.group(2)) else m.group(0), texte)
    return texte[:1].upper() + texte[1:]


def _motif(modele: str):
    return re.compile("^" + "(?P<id>[a-z0-9_]+)".join(re.escape(m) for m in modele.split("{id}")) + "$")


def _accorde(gabarit: str) -> bool:
    return "{e}" in gabarit or "{s}" in gabarit


class Familles:
    """Rattache chaque clé à sa famille, la plus spécifique d'abord, et calcule son nom attendu."""

    def __init__(self, corpus, config):
        self.corpus = corpus
        self.familles = [(f, _motif(f["motif"])) for f in config.familles.get("familles", [])]
        self.accords = config.familles.get("accords", {})
        self.membres = {}
        candidates = set(corpus.fr) | set(corpus.reconstitue) | {c for c in corpus.en if corpus.anglais(c)}
        for cle in sorted(candidates):
            for famille, motif in self.familles:
                m = motif.match(cle)
                if m:
                    self.membres[cle] = (famille, m.group("id"))
                    break
        self.problemes = {}
        self._rendus = {}

    def source(self, cle):
        """(nom français de la source, accord) ; (None, {}) si la source manque."""
        famille, ident = self.membres[cle]
        litteral = famille.get("noms_source", {}).get(ident)
        if litteral is not None:
            return litteral["nom"], litteral
        modeles = ([famille["cles_source"][ident]] if ident in famille.get("cles_source", {})
                   else [m.format(id=ident) for m in famille.get("source", [])])
        cle_source = next((c for c in modeles if c in self.membres or self.corpus.fr.get(c)), None)
        if cle_source is None:
            self.problemes[cle] = "source inconnue : aucune clé parmi " + ", ".join(modeles)
            return None, {}
        if cle_source in self.membres:
            nom = self.attendu(cle_source)
            if nom is None:
                self.problemes[cle] = f"la source {cle_source} n'a pas de nom attendu"
            return nom, {"chaine": True}
        return self.corpus.fr[cle_source], dict(self.accords.get(cle_source, {}), cle=cle_source)

    def attendu(self, cle):
        """Le nom attendu, ou None ; la raison est alors dans self.problemes."""
        if cle in self._rendus:
            return self._rendus[cle]
        self._rendus[cle] = None  # garde contre les cycles
        famille, ident = self.membres[cle]
        nom, accord = self.source(cle)
        if nom is None:
            return None
        gabarit = famille["gabarit"]
        if (_accorde(gabarit) or "{sources}" in gabarit) and accord.get("chaine"):
            self.problemes[cle] = "gabarit en chaîne avec accord ou pluriel : l'écrire en dur dans le gabarit"
            return None
        if _accorde(gabarit) and accord.get("genre") not in ("m", "f"):
            self.problemes[cle] = (f"genre inconnu pour {accord.get('cle', ident)} : "
                                   "le saisir dans les accords de familles.json")
            return None
        if "{sources}" in gabarit and not accord.get("pluriel"):
            self.problemes[cle] = (f"pluriel inconnu pour {accord.get('cle', ident)} : "
                                   "le saisir dans les accords de familles.json")
            return None
        self._rendus[cle] = rendre(gabarit, nom, accord.get("genre", ""), accord.get("nombre", "s"),
                                   bool(accord.get("propre")), accord.get("pluriel", ""))
        return self._rendus[cle]
