"""Le registre des noms : chaque objet et chaque nom propre du pack, son anglais, son français."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .texte import mots

CLE_OBJET = re.compile(r"^(item|block|entity|biome|effect|enchantment|fluid|fluid_type|wood_type|leaves_type)"
                       r"\.([a-z0-9_]+)\.([a-z0-9_/]+)$")
# Titres de chapitres de quêtes, noms de PNJ, boutiques, talents.
CLE_NOM_PROPRE = re.compile(r"^(?:ftbquests\.chapter\.[a-z0-9_]+\.title|dialog\.npc\.[a-z_]+\.name"
                            r"|shop\.society_trading\.[a-z_]+|society[._]skills\.[a-z_]+\.[a-z_]+)$")
CHIFFRE = re.compile(r"\d")


def est_nom(cle: str) -> bool:
    return bool(CLE_OBJET.match(cle) or CLE_NOM_PROPRE.match(cle))


@dataclass(frozen=True)
class Nom:
    cle: str
    en: str
    fr: str
    origine: str

    @property
    def identifiant(self) -> str:
        m = CLE_OBJET.match(self.cle)
        return f"{m.group(2)}:{m.group(3)}" if m else ""


class Registre:
    """Reconstruit à chaque exécution depuis le corpus ; jamais écrit à la main."""

    def __init__(self, corpus, config):
        self.generiques = {mots(expression) for expression in config.mots_generiques}
        self.noms = {}
        for cle in sorted(set(corpus.fr) | set(corpus.reconstitue)):
            if not est_nom(cle):
                continue
            en, fr = corpus.anglais(cle), corpus.valeur(cle)
            if en.strip() and fr.strip():
                self.noms[cle] = Nom(cle, en, fr, corpus.origine_fr.get(cle, ""))
        self.par_anglais, self.homographes, self.par_identifiant = {}, {}, {}
        for nom in self.noms.values():
            motif = tuple(mots(nom.en))
            self.homographes.setdefault(motif, []).append(nom)
            if self.citable(nom):
                self.par_anglais.setdefault(motif, []).append(nom)
            if nom.identifiant:
                self.par_identifiant.setdefault(nom.identifiant, []).append(nom)

    def citable(self, nom: Nom) -> bool:
        """Deux mots ou plus, ou un seul d'au moins cinq lettres. Jamais cités : les noms à chiffre ou à
        gabarit (« Falling %s »), les essences (wood_type, leaves_type : des matériaux, que le contrôle
        everycomp suit) et les expressions de mots_generiques.json (« Display », « The End »)."""
        if CHIFFRE.search(nom.en) or "%" in nom.en or nom.cle.startswith(("wood_type.", "leaves_type.")):
            return False
        m = mots(nom.en)
        if m in self.generiques:
            return False
        return len(m) >= 2 or (len(m) == 1 and len(m[0]) >= 5)

    def noms_de_pnj(self) -> list:
        """Les noms français des PNJ (dialog.npc.<pnj>.name), que casse et anglais_residuel exemptent."""
        return [n.fr for n in self.noms.values() if n.cle.startswith("dialog.npc.")]

    def groupes_homonymes(self) -> list:
        """Les noms de même anglais dont les français diffèrent, casse, accents et pluriels mis à part."""
        groupes = [sorted(noms, key=lambda n: n.cle) for motif, noms in self.homographes.items()
                   if motif and len({tuple(mots(n.fr)) for n in noms}) > 1]
        return sorted(groupes, key=lambda g: g[0].cle)
