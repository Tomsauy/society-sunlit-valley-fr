"""Contrôle nombres (spec 3 §5) : les nombres de l'anglais — entiers, décimaux, pourcentages, durées — se retrouvent
dans le français, dans le même ordre quand il y en a plusieurs.

Ne comptent pas : les chiffres des codes (%1$s, §6, &6, $(…), {0}, ${…}), des identifiants (minecraft:stone_2) et
des références entre accolades ({ftbquests.…}). Un nombre écrit en lettres dans le français (« trois », « zéro »,
« cinquième ») vaut son chiffre ; un nombre en plus dans le français n'est pas un défaut. Règle en attente de
décision (regles.json : nombres), activée une fois ses constats corrigés dans les zones de la chasse."""
from __future__ import annotations

import re
from collections import Counter

from validate_translation import TOKEN

from ..modele import BLOQUANT, Constat
from ..texte import sans_codes

NOM = "nombres"
ACCOLADES = re.compile(r"\{[^{}]*\}")
NOMBRE = re.compile(r"\d+(?:[.,]\d+)*")
MILLIERS_EN = re.compile(r"^\d{1,3}(?:,\d{3})+$")
MILLIERS_FR = re.compile(r"(?<=\d)[   ](?=\d{3}(?!\d))")
POINTS_FR = re.compile(r"^\d{1,3}(?:\.\d{3})+$")  # « 65.536 » : en français, le point ne sépare que des milliers
EN_LETTRES = {"zéro": "0", "deux": "2", "trois": "3", "quatre": "4", "cinq": "5", "six": "6", "sept": "7",
              "huit": "8", "neuf": "9", "dix": "10", "onze": "11", "douze": "12", "quinze": "15", "vingt": "20",
              "trente": "30", "cent": "100", "mille": "1000", "premier": "1", "première": "1", "deuxième": "2",
              "troisième": "3", "quatrième": "4", "cinquième": "5", "sixième": "6", "septième": "7",
              "huitième": "8", "neuvième": "9", "dixième": "10"}
EN_LETTRES.update({"un": "1", "une": "1", "seul": "1", "seule": "1", "second": "2", "seconde": "2"})
# « double », « doublent », « doubler » valent 2 ; « triple », « triplent », « tripler » valent 3
RACINES = {"doubl": "2", "tripl": "3"}
MOT_NOMBRE = re.compile(r"(?i)\b(" + "|".join(sorted(EN_LETTRES, key=len, reverse=True)) + r"|doubl\w*|tripl\w*)\b")
INFOBULLE = re.compile(r"\$\(t:([^)]*)\)")  # le texte d'une infobulle Patchouli est affiché : ses nombres comptent
NON_AFFICHE = re.compile(r"<remove_size>.*?</remove_size>", re.S)
MILLIERS_ANGLAIS = re.compile(r"(?<![\d,])\d{1,3}(?:,\d{3})+(?![\d,])")


def _nettoyer(texte: str) -> str:
    texte = INFOBULLE.sub(r" \1 ", NON_AFFICHE.sub(" ", texte or ""))
    return sans_codes(ACCOLADES.sub(" ", TOKEN.sub(" ", texte)))


def _normaliser(nombre: str) -> str:
    """« 1.50 » -> « 1.5 », « 2.0 » -> « 2 » ; une version (« 1.20.1 ») reste telle quelle."""
    if nombre.count(".") == 1:
        entier, decimales = nombre.split(".")
        decimales = decimales.rstrip("0")
        return f"{entier}.{decimales}" if decimales else entier
    return nombre


def nombres_en(texte: str) -> list:
    """Les nombres d'un texte anglais, dans l'ordre : « 1,000 » vaut 1000, « 1.5 » vaut 1.5."""
    resultat = []
    for m in NOMBRE.finditer(_nettoyer(texte)):
        n = m.group(0)
        resultat.append(_normaliser(n.replace(",", "") if MILLIERS_EN.match(n) else n))
    return resultat


def nombres_fr(texte: str) -> list:
    """Les nombres d'un texte français, dans l'ordre : « 1 000 » et « 1.000 » valent 1000, « 1,5 » vaut 1.5,
    « trois » et « troisième » valent 3."""
    propre = MILLIERS_FR.sub("", _nettoyer(texte))
    trouves = []
    for m in NOMBRE.finditer(propre):
        n = m.group(0)
        if n.count(",") >= 2:  # une liste (« 1,3,4 »), laissée telle quelle comme côté anglais
            trouves.append((m.start(), n))
        else:
            trouves.append((m.start(), _normaliser(n.replace(".", "") if POINTS_FR.match(n) else n.replace(",", "."))))
    trouves += [(m.start(), _lettres(m.group(1).lower())) for m in MOT_NOMBRE.finditer(propre)]
    return [n for _, n in sorted(trouves)]


def _lettres(mot: str) -> str:
    return EN_LETTRES.get(mot) or RACINES[mot[:5]]


def _sous_suite(courte: list, longue: list) -> bool:
    reste = iter(longue)
    return all(any(x == y for y in reste) for x in courte)


def ecart(en: str, fr: str) -> str:
    """Les nombres perdus, ou l'ordre changé, en clair ; vide si le français garde les nombres de l'anglais."""
    a, b = nombres_en(en), nombres_fr(fr)
    propre = _nettoyer(fr)
    a = [n for n in a if "," not in n or n not in propre]  # « 1,3 » écrit pareil des deux côtés : une liste
    perdus = Counter(a) - Counter(b)
    if perdus:
        anglais = [m.group(0) for m in MILLIERS_ANGLAIS.finditer(propre) if m.group(0).replace(",", "") in perdus]
        if anglais:
            return "séparateur anglais : " + " ".join(anglais)
        return "nombres perdus : " + " ".join(sorted(perdus.elements()))
    if not _sous_suite(a, b):
        return f"ordre différent : {' '.join(a)} en anglais, {' '.join(b)} en français"
    return ""


def verifier(corpus, registre, config, options) -> list:
    if not config.regle(NOM, options):
        return []
    constats = []
    for cle in sorted(corpus.fr):
        fr, en = corpus.fr[cle], corpus.anglais(cle)
        if corpus.origine_fr.get(cle) == "vanilla" or cle.startswith("_") or not fr.strip() or not en.strip():
            continue
        d = ecart(en, fr)
        if d:
            constats.append(Constat(NOM, cle, BLOQUANT, actuel=fr, attendu=en, detail=d))
    for champ in corpus.livres:
        d = ecart(champ.en, champ.fr) if champ.fr.strip() else ""
        if d:
            constats.append(Constat(NOM, champ.cle, BLOQUANT, actuel=champ.fr, attendu=champ.en, detail=d))
    return constats
