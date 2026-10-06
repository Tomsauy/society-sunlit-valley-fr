"""L'inventaire des textes de la chasse (spec 3 §3) : chaque valeur française affichée, hors Mojang, hors textes vides
et hors clés mortes, avec son anglais, son origine et l'unité de zone à laquelle elle appartient."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from coherence.corpus import CLE_JOURNAL, affichee, lire_json

# Lignes du journal qui portent du texte : titres et puces. La règle `codes` garantit que le français et l'anglais ont
# les mêmes lignes de structure dans le même ordre : le k-ième titre ou la k-ième puce de l'un répond à celle de l'autre.
LIGNE_DU_JOURNAL = re.compile(r"^(#+ |- )")
COMPOSEES = ("wood_type.", "leaves_type.", "block_type.")  # noms qu'Every Compat compose : vivants sans anglais
CHAPITRE = re.compile(r"^ftbquests\.chapter\.([a-z0-9_]+)\.")


@dataclass(frozen=True)
class Texte:
    id: str        # clé de langue, « <livre>/<fichier>#<pointeur> », ou « journal#<ligne> » (ligne du français, base 1)
    en: str
    fr: str
    origine: str   # projet, jar, livre, journal
    espace: str    # espace de noms du fichier qui l'affiche ; « livre:<livre> » ; « journal »
    unite: str     # unité de zone : espace de noms, « quetes:<chapitre> », « livre:<livre> », « journal »

    def en_dict(self) -> dict:
        return asdict(self)


def unite_de(cle: str, espace: str) -> str:
    """L'unité d'une clé de langue : le chapitre pour une quête, « everycomp » pour un nom composé, l'espace sinon."""
    m = CHAPITRE.match(cle)
    if m:
        return f"quetes:{m.group(1)}"
    if cle.startswith(COMPOSEES):
        return "everycomp"
    return espace


def lignes_du_journal(journal_en: str, journal_fr: str) -> list:
    """(numéro de ligne du français, anglais, français) pour chaque titre et chaque puce, appariés par rang."""
    anglaises = [l for l in journal_en.splitlines() if LIGNE_DU_JOURNAL.match(l)]
    paires = []
    rang = 0
    for numero, ligne in enumerate(journal_fr.splitlines(), start=1):
        if not LIGNE_DU_JOURNAL.match(ligne):
            continue
        paires.append((numero, anglaises[rang] if rang < len(anglaises) else "", ligne))
        rang += 1
    return paires


def inventaire(corpus, espaces_jars: dict, mortes=frozenset()) -> tuple:
    """(textes triés par id, exclus {raison: nombre}). `espaces_jars` : clé -> espace du jar qui la définit
    (corrections.applicateur.espaces_des_jars) ; `mortes` : clés écartées comme mortes (provenance.json)."""
    textes, exclus = [], {}

    def exclure(raison):
        exclus[raison] = exclus.get(raison, 0) + 1

    for cle in sorted(corpus.fr):
        fr, origine = corpus.fr[cle], corpus.origine_fr.get(cle, "")
        if origine == "vanilla":
            exclure("mojang")
        elif not affichee(cle):
            exclure("commentaire")
        elif not fr.strip():
            exclure("vide")
        elif cle in mortes:
            exclure("morte")
        elif not corpus.anglais(cle).strip() and not cle.startswith(COMPOSEES):
            exclure("sans anglais")
        else:
            espace = corpus.ns_projet.get(cle) or espaces_jars.get(cle) or cle.split(".")[1 if "." in cle else 0]
            textes.append(Texte(cle, corpus.anglais(cle), fr, origine, espace, unite_de(cle, espace)))
    for champ in corpus.livres:
        if not champ.fr.strip():
            exclure("vide")
            continue
        livre = champ.fichier.split("/", 1)[0]
        textes.append(Texte(champ.cle, champ.en, champ.fr, "livre", f"livre:{livre}", f"livre:{livre}"))
    for numero, en, fr in lignes_du_journal(corpus.journal_en, corpus.journal_fr):
        textes.append(Texte(f"{CLE_JOURNAL}#{numero}", en, fr, "journal", CLE_JOURNAL, CLE_JOURNAL))
    return sorted(textes, key=lambda t: t.id), exclus


LANGUES_TEMOINS = ("es_es", "de_de", "it_it", "pt_br")  # F3 (spec 3 §5) ; le coréen et le chinois viennent du corpus


def temoins(corpus, espace) -> dict:
    """Clé -> {langue : texte} : les traductions des jars extraits (extracted/<jar>/<ns>/<langue>.json) et les témoins
    du pack (coréen, chinois). Les livres et le journal n'en ont pas."""
    resultat = {}
    for (_, cle), langues in corpus.temoins.items():
        resultat.setdefault(cle, {}).update({l: v for l, v in langues.items() if isinstance(v, str) and v.strip()})
    extraits = Path(espace) / "extracted"
    for jar in sorted(p for p in extraits.iterdir() if p.is_dir()) if extraits.is_dir() else ():
        for ns in sorted(p for p in jar.iterdir() if p.is_dir()):
            for langue in LANGUES_TEMOINS:
                for cle, v in lire_json(ns / f"{langue}.json").items():
                    if isinstance(v, str) and v.strip():
                        resultat.setdefault(cle, {})[langue] = v
    return resultat
