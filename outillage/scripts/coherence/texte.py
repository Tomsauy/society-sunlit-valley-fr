"""Le texte ramené à ce qui se compare : sans codes, plié, découpé en mots."""
from __future__ import annotations

import re
from functools import lru_cache

from compare_accents import plier

# Tout ce qui n'est pas du texte : couleurs Minecraft (§a) et FTB (&6), macros Patchouli
# ($(item), $(l:chemin), $()), balises <ltcolor…>, gabarits printf (%s, %1$s, %.1f, %%),
# gabarits de construction (${…}) et émojis Emojiful (:coin:).
CODES = re.compile(
    r"§[0-9a-fk-orA-FK-OR]|&[0-9a-fk-or]|\$\([^)]*\)|</?lt\w+[^>]*>"
    r"|%(?:\d+\$)?(?:\.\d+)?[sdf]|%%|\$\{[^}]*\}|:[a-z_]+:"
)
MOT = re.compile(r"[0-9a-z]+")


SAUTS = re.compile(r"\$\((?:br2?|li|p)\)")
ID_DE_RESSOURCE = re.compile(r"(?<![\w#])[a-z0-9_.-]+:[a-z0-9_/.-]+")


def sans_codes(texte: str) -> str:
    """Le texte sans ses codes ni identifiants (minecraft:the_nether) ; les sauts de ligne Patchouli
    et les « \\n » écrits deviennent de vrais sauts de ligne."""
    texte = SAUTS.sub("\n", (texte or "").replace("\\n", "\n"))
    return ID_DE_RESSOURCE.sub(" ", CODES.sub(" ", texte))


def racine(mot: str) -> str:
    """Neutralise les pluriels réguliers : -eaux → -eau, -s et -x finals ; -al, -au, -ail et -aux mènent à un même
    radical (cheval et chevaux, tuyau et tuyaux, corail et coraux, émail et émaux). Le mot est déjà plié."""
    if len(mot) > 4 and mot.endswith("eaux"):
        return mot[:-1]
    if len(mot) > 4 and mot.endswith("aux"):
        return mot[:-3] + "al"
    if len(mot) > 3 and mot[-1] in "sx":
        mot = mot[:-1]
    if len(mot) > 3 and mot.endswith("au") and not mot.endswith("eau"):
        return mot[:-2] + "al"
    if len(mot) > 4 and mot.endswith("ail"):
        return mot[:-3] + "al"
    return mot


JETON = re.compile(r"[^\W_]+")
LIMITE_DE_PHRASE = re.compile(r"[.!?\n]")


@lru_cache(maxsize=None)
def jetons(texte: str) -> tuple:
    """(mot, forme écrite, début de phrase) pour chaque mot : mots() avec ce que le pliage efface."""
    propre = sans_codes(texte)
    resultat, fin = [], 0
    for m in JETON.finditer(propre):
        debut = not resultat or bool(LIMITE_DE_PHRASE.search(propre[fin:m.start()]))
        for morceau in MOT.findall(plier(m.group(0))):
            resultat.append((racine(morceau), m.group(0), debut))
            debut = False
        fin = m.end()
    return tuple(resultat)


@lru_cache(maxsize=None)
def mots(texte: str) -> tuple:
    """Les mots du texte, sans codes, pliés et ramenés à leur racine. Mis en cache : les contrôles
    découpent souvent les mêmes textes ; le tuple rendu est immuable, donc partageable."""
    return tuple(m for m, _, _ in jetons(texte))


def contient(texte: str, nom: str) -> bool:
    """Le nom figure-t-il dans le texte, aux pluriels, accents, casse et élisions près ?"""
    return contient_mots(mots(texte), mots(nom))


def contient_mots(mots_texte: tuple, mots_nom: tuple) -> bool:
    n = len(mots_nom)
    return n == 0 or any(mots_texte[i:i + n] == mots_nom for i in range(len(mots_texte) - n + 1))


def meme_casse(modele: str, mot: str) -> str:
    """`mot` avec la casse de `modele` : tout en capitales, initiale capitale, ou tel quel."""
    if len(modele) > 1 and modele.isupper():
        return mot.upper()
    if modele[:1].isupper():
        return mot[:1].upper() + mot[1:]
    return mot
