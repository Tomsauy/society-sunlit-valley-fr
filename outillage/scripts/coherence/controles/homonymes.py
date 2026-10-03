"""Contrôle homonymes : un même anglais porté par plusieurs objets aux français différents ; un même intitulé
des fiches de livres (« Sapling Price: ») traduit de plusieurs façons.

Le constat d'un groupe porte la clé de tête et, pour objet, les clés du groupe, triées : une distinction déclarée
pour deux objets ne couvre pas un troisième venu porter le même anglais."""
from __future__ import annotations

import re
from collections import Counter

from ..modele import BLOQUANT, Constat

NOM = "homonymes"
# L'intitulé d'une ligne de fiche : « $(li)Sapling Price: », « $(li)Prix de la pousse : ».
INTITULE_EN = re.compile(r"\$\((?:li|br2?|l)\)\s*(?:§.)*([A-Z][A-Za-z' -]{2,30}?)\s*:")
INTITULE_FR = re.compile(r"\$\((?:li|br2?|l)\)\s*(?:§.)*([A-ZÀ-Ý][^:$()]{2,40}?)\s*:")


def verifier(corpus, registre, config, options) -> list:
    constats = []
    for groupe in registre.groupes_homonymes():
        variantes = sorted({n.fr for n in groupe})
        constats.append(Constat(
            NOM, groupe[0].cle, BLOQUANT, actuel=" | ".join(variantes), objet=tuple(n.cle for n in groupe),
            detail=f"« {groupe[0].en} » a {len(variantes)} traductions : à unifier ou à déclarer distinctes",
            preuve=" ; ".join(f"{n.cle} = {n.fr}" for n in groupe)))
    return constats + _intitules(corpus)


def _intitules(corpus) -> list:
    """Un même intitulé des fiches de livres se traduit partout de la même façon : sa traduction la plus fréquente
    fait foi, chaque fiche qui s'en écarte est relevée (sans majorité, rien n'est tranché)."""
    releves = {}
    for champ in corpus.livres:
        en, fr = INTITULE_EN.findall(champ.en), INTITULE_FR.findall(champ.fr)
        if en and len(en) == len(fr):
            for anglais, francais in zip(en, fr):
                releves.setdefault(anglais.strip(), []).append((champ.cle, francais.strip()))
    constats = []
    for anglais, occurrences in sorted(releves.items()):
        compte = Counter(francais for _, francais in occurrences).most_common()
        if len(compte) < 2 or compte[0][1] == compte[1][1]:
            continue
        juste, n = compte[0]
        for cle, francais in occurrences:
            if francais != juste:
                constats.append(Constat(NOM, cle, BLOQUANT, actuel=francais, attendu=juste, objet=anglais,
                                        detail=f"l'intitulé « {anglais} » se traduit « {juste} » dans {n} fiches, "
                                               f"« {francais} » ici"))
    return constats
