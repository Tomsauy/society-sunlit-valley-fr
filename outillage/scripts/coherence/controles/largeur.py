"""Contrôle largeur : un nom vendu en boutique tient en deux lignes de 102 px ; un libellé de largeurs.json tient sous
sa limite. Mesure dans la police du jeu (coherence/police.py).

largeurs.json porte deux sortes d'entrées (coherence/LISEZMOI.md) :
- l'ancienne entrée manuelle {cle, limite, motif}, où motif est la justification : toujours active, bloquante dès
  que le français dépasse ;
- les contraintes recensées dans le bytecode des mods {cle?, cles?, motif?, limite, lignes?, comportement, mod,
  preuve}, où motif est une expression sur la clé : lues sous la règle en attente largeurs_mods (regles.json).
  L'anglais tient et le français dépasse : bloquant, que le texte vienne du projet ou du jar (un texte du jar se
  corrige par surcharge). L'anglais dépasse déjà : le mod est trop étroit pour sa propre langue, le français est
  signalé s'il est plus long que lui. Un texte qui défile reste lisible : signalé seulement."""
from __future__ import annotations

import re

from ..config import contrainte_de_mod
from ..modele import BLOQUANT, SIGNALE, Constat
from ..police import lignes, px

NOM = "largeur"
REGLE = "largeurs_mods"


def _cles_visees(entree, corpus) -> list:
    """L'union de cle, cles et motif, parmi les clés du français."""
    cles = {entree["cle"]} if entree.get("cle") else set()
    cles |= set(entree.get("cles", []))
    cles &= set(corpus.fr)
    if entree.get("motif"):
        motif = re.compile(entree["motif"])
        cles |= {cle for cle in corpus.fr if motif.search(cle)}
    return sorted(cles)


def _contrainte(entree, corpus) -> list:
    limite, n = entree["limite"], entree.get("lignes")
    mesure = (lambda t: lignes(t, limite)) if n else px
    seuil = n or limite
    defile = entree["comportement"].startswith("défile")
    preuve = f"{entree['mod']} : {entree['preuve']}"
    constats = []
    for cle in _cles_visees(entree, corpus):
        fr, en = corpus.fr[cle], corpus.anglais(cle)
        if not fr.strip() or mesure(fr) <= seuil:
            continue
        en_tient = mesure(en) <= seuil
        if not en_tient and mesure(fr) <= mesure(en):
            continue
        statut = BLOQUANT if en_tient and not defile else SIGNALE
        if n:
            detail = (f"{mesure(fr)} lignes de {limite} px pour {n} au plus ; l'anglais : {mesure(en)} ligne(s), "
                      f"{px(en)} px")
        else:
            detail = f"{px(fr)} px pour {limite} au plus ; l'anglais : {px(en)} px"
        detail += ("" if en_tient else " (l'anglais dépasse déjà, le français est plus long)") + \
                  (" ; le texte défile" if defile else "")
        constats.append(Constat(NOM, cle, statut, actuel=fr, detail=detail, preuve=preuve))
    return constats


def verifier(corpus, registre, config, options) -> list:
    constats = []
    for ident in sorted(corpus.vendus):
        ns, _, chemin = ident.partition(":")
        cle = next((c for c in (f"item.{ns}.{chemin}", f"block.{ns}.{chemin}") if corpus.fr.get(c)), None)
        if cle and lignes(corpus.fr[cle]) > 2:
            statut = BLOQUANT if corpus.origine_fr.get(cle) == "projet" else SIGNALE
            constats.append(Constat(NOM, cle, statut, actuel=corpus.fr[cle],
                                    detail=f"{lignes(corpus.fr[cle])} lignes dans la boîte de 102 px de la boutique, "
                                           "deux au plus"))
    mods = config.regle(REGLE, options)
    for entree in config.largeurs:
        if contrainte_de_mod(entree):
            if mods:
                constats += _contrainte(entree, corpus)
            continue
        fr = corpus.fr.get(entree["cle"], "")
        if px(fr) > entree["limite"]:
            constats.append(Constat(NOM, entree["cle"], BLOQUANT, actuel=fr, preuve=entree.get("motif", ""),
                                    detail=f"{px(fr)} px pour {entree['limite']} au plus"))
    # Une clé visée deux fois (boutique et contrainte, deux écrans) : un constat, le plus grave, le premier venu.
    retenus = {}
    for c in constats:
        if c.cle not in retenus or (c.statut == BLOQUANT and retenus[c.cle].statut != BLOQUANT):
            retenus[c.cle] = c
    return list(retenus.values())
