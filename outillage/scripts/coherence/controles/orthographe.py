"""Contrôle orthographe : une faute déjà rencontrée ne revient pas, jars compris ; une passe
LanguageTool locale (--languagetool) en découvre d'autres, signalées pour relecture.

Une forme interdite (formes_interdites.json) est fautive dans tout contexte ; son constat a pour objet la forme,
comme celui de LanguageTool a pour objet sa règle. Une forme à « casse » ne vise que ce qu'elle écrit (« N'importe
le », pas « le village n'importe le sel ») et se remplace telle qu'écrite.

Serveur : java -cp languagetool-server.jar org.languagetool.server.HTTPServer --port 8081
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request

from ..corpus import CLE_JOURNAL, affichee
from ..modele import BLOQUANT, SIGNALE, Constat
from ..texte import meme_casse, sans_codes

NOM = "orthographe"
# Conventions du projet que LanguageTool prendrait pour des fautes : espaces fines, apostrophe
# droite, tirets, « oe », majuscule initiale des fragments.
REGLES_DESACTIVEES = ("FRENCH_WHITESPACE", "FRENCH_WHITESPACE_STRICT", "APOS_TYP", "UPPERCASE_SENTENCE_START",
                      "WHITESPACE_RULE", "TIRET", "TIRET_LONG_1", "TIRET_LONG_2", "OE")
TAILLE_DU_LOT = 20000


class LanguageToolIndisponible(Exception):
    pass


def verifier(corpus, registre, config, options) -> list:
    motifs = [(re.compile(rf"(?<!\w){re.escape(f['forme'])}(?!\w)", 0 if f.get("casse") else re.I), f)
              for f in config.formes_interdites]
    textes = list(_textes(corpus))
    constats = []
    for cle, fr in textes:
        for motif, forme in motifs:
            m = motif.search(fr)
            if m:
                # Une forme à « casse » ne vise que ce qu'elle écrit : sa forme juste s'écrit telle quelle.
                attendu = motif.sub(lambda t: forme["juste"] if forme.get("casse")
                                    else meme_casse(t.group(0), forme["juste"]), fr)
                constats.append(Constat(NOM, cle, BLOQUANT, actuel=fr, attendu=attendu, preuve=forme.get("source", ""),
                                        objet=forme["forme"], detail=f"« {m.group(0)} » → « {forme['juste']} »"))
    if options.languagetool:
        constats += languagetool(textes, options.url_languagetool)
    return constats


def _textes(corpus):
    """Le français effectif hors vanilla — jars compris —, les livres et le journal."""
    for cle, fr in sorted(corpus.fr.items()):
        if fr and affichee(cle) and corpus.origine_fr.get(cle) != "vanilla":
            yield cle, fr
    for champ in corpus.livres:
        if champ.fr:
            yield champ.cle, champ.fr
    if corpus.journal_fr:
        yield CLE_JOURNAL, corpus.journal_fr


def languagetool(textes, url) -> list:
    """Une passe, par lots d'environ 20 000 caractères ; chaque correspondance est un constat signalé."""
    constats, lot, taille = [], [], 0
    for cle, fr in textes:
        propre = re.sub(r"\s+", " ", sans_codes(fr)).strip()
        if propre:
            lot.append((cle, propre))
            taille += len(propre) + 2
        if taille >= TAILLE_DU_LOT:
            constats += _lot(lot, url)
            lot, taille = [], 0
    if lot:
        constats += _lot(lot, url)
    return constats


def _lot(lot, url) -> list:
    donnees = urllib.parse.urlencode({"text": "\n\n".join(t for _, t in lot), "language": "fr",
                                      "disabledRules": ",".join(REGLES_DESACTIVEES)}).encode()
    try:
        with urllib.request.urlopen(url, donnees, timeout=300) as reponse:
            resultat = json.load(reponse)
    except (OSError, ValueError) as e:
        raise LanguageToolIndisponible(f"LanguageTool injoignable à {url} ({e}) : lancer le serveur local") from e
    # LanguageTool (Java) compte ses décalages en unités UTF-16 : un émoji (🌼) en vaut deux.
    bornes, debut = [], 0
    for cle, texte in lot:
        bornes.append((debut, debut + _utf16(texte), cle, texte))
        debut += _utf16(texte) + 2
    constats = []
    for m in resultat.get("matches", []):
        for a, b, cle, texte in bornes:
            if a <= m["offset"] < b:
                extrait = _tranche_utf16(texte, m["offset"] - a, m["length"])
                constats.append(Constat(
                    NOM, cle, SIGNALE, actuel=texte, objet=m["rule"]["id"],
                    attendu=" | ".join(r["value"] for r in m.get("replacements", [])[:3]),
                    detail=f"LanguageTool {m['rule']['id']} : « {extrait} » — {m['message']}"))
                break
    return constats


def _utf16(texte: str) -> int:
    """La longueur du texte en unités UTF-16, celles des décalages de LanguageTool."""
    return len(texte.encode("utf-16-le")) // 2


def _tranche_utf16(texte: str, debut: int, longueur: int) -> str:
    """La tranche du texte qui va de `debut` sur `longueur` unités UTF-16."""
    return texte.encode("utf-16-le")[2 * debut:2 * (debut + longueur)].decode("utf-16-le", "replace")
