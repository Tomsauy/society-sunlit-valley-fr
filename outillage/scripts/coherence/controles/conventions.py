"""Contrôle conventions (STYLE §1, §4, §7) : apostrophe droite, ni « œ » ni espace insécable,
tutoiement dans society*, les dialogues, les quêtes et les livres, guillemets droits dans les textes
d'interface, « Escalier en X », « Dalle en X » pour le bois et « Dalle de X » pour la pierre (fiche du 30/09),
« Muret de X », et la forme des bandes de danger de Railways retenue par la contre-analyse
(« Chevron X sur noir ») : « sur noir », forme majoritaire de la famille, et « Chevron » au singulier de
l'anglais, bien que minoritaire. Règle en attente de décision
(regles.json : pourcentages) : « 25 % » ou « 25% ».
"""
from __future__ import annotations

import re

from ..corpus import CLE_JOURNAL
from ..modele import BLOQUANT, Constat

NOM = "conventions"
VOUVOIEMENT = re.compile(r"(?i)\b(?:vous|votre|vos)\b|\b(?!(?:chez|assez|nez|rez|lez)\b)[a-zàâçéèêëîïôûùüÿ]+ez\b")
RENDEZ_VOUS = re.compile(r"(?i)\brendez-vous\b")
NARRATIFS = {"dialog", "ftbquestlocalizer", "livre", "journal"}
FAMILLES_DE_BLOCS = (
    (re.compile(r"^block\.[^.]+\.[a-z0-9_]*stairs$"), re.compile(r"^Escalier en "),
     "« Escalier en X », au singulier (STYLE §7)"),
    (re.compile(r"^block\.[^.]+\.(?![a-z0-9_]*sconce)[a-z0-9_]*_wall$"), re.compile(r"^Muret (?:de |d')"),
     "« Muret de X » (STYLE §7)"),
    # Bandes de danger de Railways : « sur noir », « sur blanc » comme 92 des 124 noms de la famille (32 disent
    # « sur fond ») ; « Chevron » au singulier de l'anglais, choix de la contre-analyse (ligne 656) bien que
    # minoritaire : 30 « Chevron » contre 32 « Chevrons » sur les 62 chevrons. Le préfixe de couleur est facultatif :
    # les blocs de locométal (« hazard_stripes_chevron_on_black ») suivent la même forme (relecture de 2-05).
    (re.compile(r"^block\.railways\.(?:[a-z0-9_]+_)?hazard_stripes_chevron_on_black$"),
     re.compile(r"^Chevron \S.* sur noir$"),
     "« Chevron X sur noir » : singulier de l'anglais, « sur noir » de la famille"),
    (re.compile(r"^block\.railways\.(?:[a-z0-9_]+_)?hazard_stripes_chevron_on_white$"),
     re.compile(r"^Chevron \S.* sur blanc$"),
     "« Chevron X sur blanc » : singulier de l'anglais, « sur blanc » de la famille"),
    (re.compile(r"^block\.railways\.(?:[a-z0-9_]+_)?hazard_stripes_diagonal_on_black$"),
     re.compile(r"^Bandes de danger \S.* sur noir$"), "« Bandes de danger X sur noir », comme leur famille"),
    (re.compile(r"^block\.railways\.(?:[a-z0-9_]+_)?hazard_stripes_diagonal_on_white$"),
     re.compile(r"^Bandes de danger \S.* sur blanc$"), "« Bandes de danger X sur blanc », comme leur famille"),
)
POURCENT = re.compile(r"%%|%(?![sd]|\d+\$|\.\d)")
# Une variable (%s, %1$s, %d, %.1f) vaut un nombre devant le signe : « +%s %% » comme « 25 % » (fiche du 30/09).
VARIABLE = re.compile(r"%%|%(?:\d+\$)?(?:\.\d+)?[sdf]")
DALLE = re.compile(r"^block\.([^.]+)\.([a-z0-9_]+?)(_vertical)?_slab$")
PLANCHES = re.compile(r"^block\.([^.]+)\.([a-z0-9_]+)_planks$")
# Fiche du 30/09/2026 (dalles) : comme chez Mojang, une dalle de bois est « en » son bois (« Dalle en chêne ») ou prend
# l'adjectif des bois du Nether (« Dalle carmin », « Dalle biscornue ») ; une dalle de pierre est « de » (STYLE §7).
DALLE_DE_BOIS = re.compile(r"^Dalle (?:verticale )?(?:en |(?:carmin|biscornue)\b)")
DALLE_DE_PIERRE = re.compile(r"^Dalle (?:verticale )?(?:de |d')")


def bois(corpus) -> set:
    """Les (espace de noms, base) des blocs de planches : une dalle de même base est une dalle de bois."""
    return {m.groups() for cle in set(corpus.en) | set(corpus.fr) if (m := PLANCHES.match(cle))}


def verifier(corpus, registre, config, options) -> list:
    pourcentages = config.regle("pourcentages", options)
    planches = bois(corpus)
    constats = []
    for cle, fr, ns in _textes(corpus):
        def signaler(regle, detail, attendu=""):
            constats.append(Constat(NOM, cle, BLOQUANT, actuel=fr, attendu=attendu, objet=regle, detail=detail))

        if "’" in fr:
            signaler("apostrophe", "apostrophe courbe : l'apostrophe droite", fr.replace("’", "'"))
        if re.search("[œŒ]", fr):
            signaler("ligature", "« oe », jamais la ligature", re.sub("Œ(?=[a-zé])", "Oe", fr)
                     .replace("Œ", "OE").replace("œ", "oe"))
        if re.search("[  ]", fr):
            signaler("insecable", "espace insécable : Minecraft l'affiche mal", re.sub("[  ]", " ", fr))
        if ns.startswith("society") or ns in NARRATIFS - {"journal"}:
            m = VOUVOIEMENT.search(RENDEZ_VOUS.sub(" ", fr))
            if m:
                signaler("vouvoiement", f"« {m.group(0)} » : ici, le pack tutoie")
        if ns not in NARRATIFS and re.search("[«»]", fr):
            signaler("guillemets", "guillemets français dans un texte d'interface : guillemets droits",
                     re.sub(r"«\s*|\s*»", '"', fr))
        for motif_cle, forme, regle in FAMILLES_DE_BLOCS:
            if ns not in NARRATIFS and motif_cle.match(cle) and not forme.match(fr):
                signaler("nommage", regle)
        dalle = DALLE.match(cle)
        if ns not in NARRATIFS and dalle:
            de_bois = (dalle.group(1), dalle.group(2)) in planches or ("minecraft", dalle.group(2)) in planches
            if de_bois and not DALLE_DE_BOIS.match(fr):
                signaler("nommage", "« Dalle en X » pour une dalle de bois, comme Mojang (fiche du 30/09 : dalles)")
            elif not de_bois and not DALLE_DE_PIERRE.match(fr):
                signaler("nommage", "« Dalle de X » pour une dalle de pierre (STYLE §7)")
        if pourcentages:
            marque = POURCENT.sub("\x00", VARIABLE.sub(lambda m: m.group() if m.group() == "%%" else "0", fr))
            faute = re.search(r"\d\x00" if pourcentages == "espace" else r"\d \x00", marque)
            if faute:
                signaler("pourcentage", "« 25 % », espace avant le signe" if pourcentages == "espace"
                         else "« 25% », signe collé au nombre")
    return constats


def _textes(corpus):
    for cle, fr in corpus.textes_projet():
        yield cle, fr, corpus.ns_projet.get(cle, "")
    for champ in corpus.livres:
        if champ.fr:
            yield champ.cle, champ.fr, "livre"
    if corpus.journal_fr:
        yield CLE_JOURNAL, corpus.journal_fr, "journal"
