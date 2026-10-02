"""Contrôle casse (STYLE §2) : seul le premier mot d'un nom prend la majuscule.

- Dans un nom d'objet et dans un titre (quête, sous-titre, tâche, entrée de livre), pas de
  majuscule interne : « Fossile de Poulet », « Planches Pourries ». Le premier mot se lit après
  les codes et symboles de tête (« :pick: Grottes », « ♧ Catalogue ») ; un mot qui ouvre une phrase, une
  citation, ou un segment après une numérotation ou un intitulé en capitales suivis d'un tiret espacé garde
  sa majuscule (« SUPPRIMÉ ! Acheter », « Panneau "Pas de démarchage !" », « I - Premiers pas »,
  « SUPPRIMÉ - Ne fonctionne plus ») ; après un nom commun, le mot qui suit le tiret reste vérifié (dans
  « Maison de villageois - Berger », c'est le métier qui garde sa majuscule, pas le tiret). Après deux-points, la
  minuscule reste de règle. « Maîtrise » suivie de son domaine est le nom propre d'un talent (STYLE §7 : « la
  Maîtrise de la pêche »). Le nom d'un livre de compétence est un titre d'œuvre : après l'article, le premier nom
  prend la majuscule (« La Qualité de la terre »), qu'il ne faut pas oublier (« La phénoménologie du trésor »).
- Partout, un nom propre de plusieurs mots déclaré dans noms_propres.json garde ses majuscules (« la foire aux
  livres » pour « Foire aux livres »).
- Partout, noms, titres et phrases, les métiers des villageois, les noms des boutiques et les mots de
  majuscules.json (« Slime », « Slimes ») se traitent comme des noms de personnes (STYLE §2, décision du
  29/09/2026) : leur majuscule est acceptée (« Villageois Pêcheur invité », « au Marché », « Coeur de Slime
  fabricable »), sans être imposée. Métiers et boutiques se lisent dans les données : noms affichés des clés
  entity.minecraft.villager.<id>, entity.minecraft.villager.<mod>.<id> et shop.society_trading.<id>. Seule
  exception (précision du 29/09/2026) : dans un nom d'objet, un métier ou une boutique placé juste après « de »,
  « du », « des » ou « d' » est un nom commun (« Chapeau de sorcière », « Pain du fermier ») ; Slime y garde sa
  majuscule (« Seau de Slime »), comme un nom propre ou un nom de PNJ.
- Règle en attente de décision (regles.json : casse_textes) : dans le corps d'un texte, un nom
  d'objet s'écrit en minuscules hors début de phrase : « remplis ton Arrosoir » ; mis en valeur par un code couleur,
  il garde sa majuscule (STYLE §2, décision du 29/09/2026 : « Tu as trouvé une &6Géode&r ! »). Le terme générique
  d'un toponyme aussi, devant « de/du/des » et un nom propre : « les grottes de Camuy », « la mer du Nord ».

Exemptés : noms_propres.json, KEEP-ENGLISH, termes que le glossaire garde en anglais, noms des PNJ, métiers,
boutiques et majuscules.json, sigles et chiffres romains (mots tout en capitales). Un mot seul l'est partout (un métier
ou une boutique, sauf après « de » dans un nom d'objet) ; un nom de plusieurs mots (« Caverne du Crâne », « Tri-bull »,
« Marchand exotique »), là seulement où il figure en entier. Le français de Mojang fait foi pour ses noms.
"""
from __future__ import annotations

import re

from ..modele import BLOQUANT, Constat
from ..registre import CLE_OBJET
from ..texte import CODES, jetons, mots, sans_codes

NOM = "casse"
MOT = re.compile(r"[^\W\d_]+")
# Avant le premier mot : espaces et symboles (« ♧ »), codes de couleur (§a, &6), émojis (:pick:), balise
# <ltcolor> et ses réglages (« c=AA0000;w=10; »).
DEBUT = re.compile(r"^(?:[§&][0-9a-fk-or]|:[a-z_]+:|<lt\w+>(?:\w+=[^;<>]*;)*|[^\w§&:<])*")
# Ce qui précède un mot qui ouvre une phrase, une citation, ou un segment après une numérotation (I, IV.II, 3)
# ou un intitulé en capitales (SUPPRIMÉ, FE) suivis d'un tiret espacé.
OUVERTURE = re.compile(r"(?:[.!?…][\"'»”)]*\s+"
                       r"|(?:^|\s)(?:[IVXLCDM]+(?:\.[IVXLCDM]+)*|\d+(?:\.\d+)*|[A-ZÀ-ÖØ-ÞŒ]{2,})\s[-–—]\s+"
                       r"|«\s*|“|(?:^|\s)[\"']|(?:\\n|\n)\s*)(?:[§&][0-9a-fk-or])*$")
# STYLE §7 : « Maîtrise » suivie de son domaine (« de la pêche », « du minage ») est le nom propre d'un talent.
MAITRISE = re.compile(r"Maîtrise(?= (?:de|du|des) )")
TITRE = re.compile(r"^ftbquests\..*\.(?:title|subtitle)$|#/(?:name|title)$")
# Terme générique d'un toponyme, capitalisé devant « de/du/des » (ou « d' ») et un nom propre : en toponymie, le
# générique reste en minuscule (« les grottes de Lascaux », « la mer du Nord », « le lac d'Annecy »).
GENERIQUE = re.compile(r"(?<!\w)(?:(?:Grotte|Caverne|Lac|Mont|Montagne|Forêt|Île|Océan|Mer|Rivière|Fleuve|Vallée|"
                       r"Colline|Désert|Plaine|Baie|Golfe|Pic|Col|Cap)s?|Marais)"
                       r"(?=\s+(?:de|du|des)\s+[A-ZÀ-ÖØ-ÞŒ]|\s+d['’][A-ZÀ-ÖØ-ÞŒ])")
# STYLE §2, décision du 29/09/2026 : les métiers des villageois (entity.minecraft.villager.<id> et
# entity.minecraft.villager.<mod>.<id>) et les boutiques (shop.society_trading.<id>, sans suffixe), lus dans les données
# pour qu'une version suivante soit couverte d'office.
METIER_OU_BOUTIQUE = re.compile(r"^(?:entity\.minecraft\.villager(?:\.[a-z0-9_]+){1,2}"
                                r"|shop\.society_trading\.[a-z0-9_]+)$")
# Précision du 29/09/2026 : ce qui précède, dans un nom d'objet, un métier ou une boutique devenu nom commun.
APRES_DE = re.compile(r"(?<!\w)(?:(?:de|du|des)\s+|d['’])(?:[§&][0-9a-fk-or])*$", re.I)
# STYLE §2, décision du 29/09/2026 : un passage mis en valeur va d'un code couleur (§x ou &x, x de 0 à 9 ou de a à f)
# jusqu'à §r, &r ou le code couleur suivant ; un code de format (§l, &o…) n'en ouvre ni n'en ferme.
COULEURS, FIN_DE_COULEUR = "0123456789abcdef", "r"


def verifier(corpus, registre, config, options) -> list:
    termes = config.termes_gardes()
    # Les métiers, les boutiques et les mots de majuscules.json (« Slime ») se traitent comme des noms de personnes
    # (STYLE §2) : leur majuscule est acceptée partout, noms, titres et phrases, sans être imposée (« un pêcheur » peut
    # désigner n'importe quel pêcheur, « Boule de slime » est le nom de Mojang).
    personnes = metiers_et_boutiques(corpus) + list(config.majuscules)
    # En corps de phrase, les noms des PNJ n'exemptent pas ; un mot seul déclaré l'est partout, un nom de plusieurs
    # mots là seulement où il figure en entier (« Océan de Roche » n'exempte pas « l'Océan » seul).
    seuls_declares, _ = noms_propres(termes + personnes)
    expressions_declarees = [mots(t) for t in termes + personnes if len(MOT.findall(t)) > 1]
    seuls, expressions = noms_propres(termes + personnes + registre.noms_de_pnj())
    # Dans un nom d'objet, après « de », « du », « des » ou « d' », un métier ou une boutique est un nom commun : n'y
    # exemptent que les autres sources (« Seau de Slime », « Panneau du Chêne sage », nom de PNJ).
    seuls_communs, expressions_communes = noms_propres(termes + list(config.majuscules) + registre.noms_de_pnj())
    constats = []
    titres = [(n.cle, n.fr) for n in registre.noms.values() if CLE_OBJET.match(n.cle) and n.origine != "vanilla"]
    titres += [(cle, fr) for cle, fr in corpus.textes_projet() if TITRE.search(cle)]
    titres += [(champ.cle, champ.fr) for champ in corpus.livres if champ.fr and TITRE.search(champ.cle)]
    oeuvres = _livres_de_competence(corpus)
    for cle, fr in titres:
        debut = DEBUT.match(fr).end()
        article = ARTICLE.match(fr, debut) if cle in oeuvres else None
        premier = MOT.search(fr, article.end()) if article else None
        couverts = [m.span() for m in expressions.finditer(fr)] if expressions else []
        nom_d_objet = bool(CLE_OBJET.match(cle))
        communs = [m.span() for m in expressions_communes.finditer(fr)] if nom_d_objet and expressions_communes else []
        fautes = [m for m in MOT.finditer(fr) if m.start() > debut and _capitale(m.group(0), ())
                  and not (_exempte(m, seuls_communs, communs) if nom_d_objet and APRES_DE.search(fr[:m.start()])
                           else _exempte(m, seuls, couverts))
                  and not OUVERTURE.search(fr[:m.start()]) and not MAITRISE.match(fr, m.start())
                  and not (premier and m.start() == premier.start())]
        details = ["majuscule interne : " + ", ".join(f"« {m.group(0)} »" for m in fautes)] if fautes else []
        attendu = _minuscules(fr, fautes)
        if premier and premier.group(0)[:1].islower():
            details.append(f"titre d'œuvre : « {premier.group(0)} » prend la majuscule après l'article "
                           "(« La Qualité de la terre »)")
            attendu = attendu[:premier.start()] + premier.group(0)[:1].upper() + attendu[premier.start() + 1:]
        if details:
            constats.append(Constat(NOM, cle, BLOQUANT, actuel=fr, attendu=attendu, detail=" ; ".join(details)))
    constats += _noms_propres_declares(corpus, config)
    if config.regle("casse_textes", options):
        constats += _corps_de_phrase(corpus, registre, seuls_declares, expressions_declarees)
        constats += _toponymes(corpus, registre, expressions)
    return constats


ARTICLE = re.compile(r"(?:Les?|La) |L'")
ARTICLES = frozenset({"le", "la", "les", "l"})  # le premier mot écrit d'un nom qui commence par un article


def metiers_et_boutiques(corpus) -> list:
    """Les noms affichés des métiers des villageois et des boutiques : leur majuscule est acceptée partout, comme celle
    d'un nom de personne (« Villageois Pêcheur invité », « Achète des graines au Marché »)."""
    return sorted({corpus.valeur(cle).strip() for cle in corpus.fr
                   if METIER_OU_BOUTIQUE.match(cle) and corpus.valeur(cle).strip()})


def _livres_de_competence(corpus) -> set:
    """Les noms des livres de compétence (item.society.<id> que décrit society_skills.books.<id>) : des titres
    d'œuvres, qui prennent la majuscule au premier nom après l'article (« La Qualité de la terre »)."""
    return {f"item.society.{cle.split('.')[2]}" for cle in corpus.fr
            if cle.startswith("society_skills.books.") and cle.count(".") == 3}


def _noms_propres_declares(corpus, config) -> list:
    """Un nom propre de plusieurs mots déclaré dans noms_propres.json (« Foire aux livres », « Caverne du
    Crâne ») garde ses majuscules partout où il est écrit : « la foire aux livres » est une faute."""
    propres = sorted({t.strip() for t in config.noms_propres if len(MOT.findall(t)) > 1 and t.strip()[:1].isupper()},
                     key=len, reverse=True)
    if not propres:
        return []
    canon = {t.lower(): t for t in propres}
    motif = re.compile(r"(?<!\w)(?:" + "|".join(map(re.escape, propres)) + r")(?!\w)", re.I)
    textes = corpus.textes_projet() + [(champ.cle, champ.fr) for champ in corpus.livres if champ.fr]
    constats = []
    for cle, fr in textes:
        fautes = [(m, canon[m.group(0).lower()]) for m in motif.finditer(fr)
                  if any(c[:1].isupper() and e[:1].islower()
                         for e, c in zip(MOT.findall(m.group(0)), MOT.findall(canon[m.group(0).lower()])))]
        if fautes:
            attendu = fr
            for m, juste in reversed(fautes):
                attendu = attendu[:m.start()] + juste + attendu[m.end():]
            constats.append(Constat(NOM, cle, BLOQUANT, actuel=fr, attendu=attendu, objet=fautes[0][1],
                                    detail="nom propre sans sa majuscule : "
                                           + ", ".join(f"« {m.group(0)} » → « {juste} »" for m, juste in fautes)))
    return constats


def noms_propres(termes) -> tuple:
    """(mots seuls, expression régulière des noms de plusieurs mots ou None). Un nom de plusieurs mots
    (« Caverne du Crâne ») n'exempte ses mots que là où il figure en entier : « Caverne » seul reste
    vérifié. Le trait d'union et l'apostrophe séparent aussi les mots (« Tri-bull »)."""
    seuls, expressions = set(), set()
    for terme in termes:
        trouves = MOT.findall(terme)
        if len(trouves) == 1:
            seuls.add(trouves[0])
        elif trouves:
            expressions.add(terme.strip())
    if not expressions:
        return seuls, None
    ordre = sorted(expressions, key=len, reverse=True)
    return seuls, re.compile(r"(?<!\w)(?:" + "|".join(map(re.escape, ordre)) + r")(?!\w)")


def _corps_de_phrase(corpus, registre, seuls, expressions) -> list:
    """Chaque nom d'objet cité dans un texte s'y écrit en minuscules, hors début de phrase et hors mots
    que le nom lui-même capitalise (« vin Aegis »). Les noms des PNJ n'exemptent pas ici : « Plans »
    est aussi le nom du vendeur de plans, mais « Achète des Plans » cite l'objet. Un mot seul déclaré
    (`seuls`) est exempté partout ; un nom déclaré de plusieurs mots (`expressions`, leurs mots pliés), là seulement
    où il figure en entier : « l'Océan de Roche », mais pas « l'Océan » seul. Seuls les objets sont cherchés : les
    boutiques, comme les métiers, se traitent en noms de personnes (STYLE §2). Un nom mis en valeur en entier dans un
    même passage garde la majuscule de son premier mot (« une &6Géode&r ») ; une majuscule interne que le nom n'a pas
    reste une faute (« &6Houe Dorée&r »)."""
    par_premier = {}
    for expression in expressions:
        if expression:
            par_premier.setdefault(expression[0], []).append(expression)
    index = {}
    for n in registre.noms.values():
        forme = mots(n.fr)
        if CLE_OBJET.match(n.cle) and forme:
            ecrits = tuple(e for _, e, _ in jetons(n.fr))
            index.setdefault(forme[0], {}).setdefault(forme, ecrits)
            # Un nom qui commence par un article se cherche aussi sans lui : « tomber dans le Vide » cite « Le vide ».
            if ecrits[0].lower().rstrip("'") in ARTICLES and len(forme) > 1:
                index.setdefault(forme[1], {}).setdefault(forme[1:], ecrits[1:])
    index = {premier: sorted(formes.items(), key=lambda f: len(f[0]), reverse=True)
             for premier, formes in index.items()}
    textes = [(cle, fr) for cle, fr in corpus.textes_projet() if cle not in registre.noms and not TITRE.search(cle)]
    textes += [(champ.cle, champ.fr) for champ in corpus.livres if champ.fr and not TITRE.search(champ.cle)]
    constats = []
    for cle, fr in textes:
        suite = jetons(fr)
        racines = tuple(m for m, _, _ in suite)
        couverts = {k for p, r in enumerate(racines) for e in par_premier.get(r, ()) if racines[p:p + len(e)] == e
                    for k in range(p, p + len(e))}  # les mots des noms déclarés qui figurent en entier
        passages = _passages(fr, len(suite))
        fautes, i = [], 0
        while i < len(suite):
            # Un nom qui commence par un article (« La boîte ») ne s'apparie ni au mot qui ouvre la phrase, ni à un article
            # écrit en minuscule : ce n'y est que l'article du texte (« La &6Boîte à chenilles&r ! », « via la &6Boîte de
            # pêche&r »).
            trouve = next(((f, e) for f, e in index.get(suite[i][0], ())
                           if tuple(m for m, _, _ in suite[i:i + len(f)]) == f
                           and not (e[0].lower() in ARTICLES and (suite[i][2] or not suite[i][1][:1].isupper()))),
                          None)
            if not trouve:
                i += 1
                continue
            forme, ecrits_du_nom = trouve
            mis_en_valeur = passages[i] is not None and set(passages[i:i + len(forme)]) == {passages[i]}
            for j in range(i, i + len(forme)):
                _, ecrit, debut = suite[j]
                if j in couverts:
                    faute = False
                elif j == i:
                    faute = not debut and not mis_en_valeur and _capitale(ecrit, seuls)
                else:  # un mot interne capitalisé par le nom lui-même est un nom propre
                    faute = _capitale(ecrit, seuls) and not ecrits_du_nom[min(j - i, len(ecrits_du_nom) - 1)][:1].isupper()
                if faute and ecrit not in fautes:
                    fautes.append(ecrit)
            i += len(forme)
        if fautes:
            constats.append(Constat(NOM, cle, BLOQUANT, actuel=fr, objet="corps",
                                    detail="nom d'objet capitalisé en corps de phrase : "
                                           + ", ".join(f"« {m} »" for m in fautes)))
    return constats


def _passages(texte: str, n: int) -> tuple:
    """Pour chacun des `n` mots de jetons(texte), le numéro du passage mis en valeur qui le contient, ou None. Un code
    remplacé par une espace sépare toujours deux mots : les mots des morceaux entre codes, mis bout à bout, sont ceux du
    texte entier ; s'ils ne le sont pas (n différent), aucun mot ne compte pour mis en valeur."""
    numeros, numero, compte, debut = [], None, 0, 0
    for code in CODES.finditer(texte):
        valeur = code.group(0)
        if len(valeur) != 2 or valeur[0] not in "§&" or valeur[1] not in COULEURS + FIN_DE_COULEUR:
            continue
        numeros += [numero] * len(jetons(texte[debut:code.start()]))
        if valeur[1] == FIN_DE_COULEUR:
            numero = None
        else:
            compte += 1
            numero = compte
        debut = code.end()
    numeros += [numero] * len(jetons(texte[debut:]))
    return tuple(numeros) if len(numeros) == n else (None,) * n


def _toponymes(corpus, registre, expressions) -> list:
    """Le terme générique d'un toponyme (« Grottes », « Lac », « Mer »…) reste en minuscule devant « de/du/des » et
    un nom propre, en corps de phrase : « les grottes de Camuy ». Pas en début de phrase ou d'élément de liste, ni
    dans un nom propre déclaré (« Caverne du Crâne », « Océan de Roche ») ou un nom du registre (un biome « Forêt
    de X »), qui gardent leur forme."""
    noms = sorted({n.fr for n in registre.noms.values() if n.fr and GENERIQUE.search(n.fr)}, key=len, reverse=True)
    du_registre = re.compile("|".join(map(re.escape, noms))) if noms else None
    textes = [(cle, fr) for cle, fr in corpus.textes_projet() if cle not in registre.noms and not TITRE.search(cle)]
    textes += [(champ.cle, champ.fr) for champ in corpus.livres if champ.fr and not TITRE.search(champ.cle)]
    constats = []
    for cle, fr in textes:
        fautes, exclus = [], None
        for m in GENERIQUE.finditer(fr):
            avant = sans_codes(fr[:m.start()])  # « $(li) », « \n » : un début de ligne
            if DEBUT.match(avant).end() == len(avant) or OUVERTURE.search(avant):
                continue
            if exclus is None:
                exclus = [s.span() for motif in (expressions, du_registre) if motif for s in motif.finditer(fr)]
            if not any(a <= m.start() < b for a, b in exclus):
                fautes.append(m)
        if fautes:
            constats.append(Constat(NOM, cle, BLOQUANT, actuel=fr, attendu=_minuscules(fr, fautes), objet="toponyme",
                                    detail="terme générique d'un toponyme capitalisé en corps de phrase : "
                                           + ", ".join(f"« {m.group(0)} »" for m in fautes)))
    return constats


def _capitale(mot: str, propres: set) -> bool:
    return mot[:1].isupper() and not mot.isupper() and mot not in propres


def _exempte(m, seuls: set, couverts: list) -> bool:
    """Le mot trouvé est exempté seul, ou couvert par un nom de plusieurs mots qui figure en entier."""
    return m.group(0) in seuls or any(a <= m.start() < b for a, b in couverts)


def _minuscules(texte: str, fautes) -> str:
    morceaux, fin = [], 0
    for m in fautes:
        morceaux += [texte[fin:m.start()], m.group(0)[0].lower() + m.group(0)[1:]]
        fin = m.end()
    return "".join(morceaux) + texte[fin:]
