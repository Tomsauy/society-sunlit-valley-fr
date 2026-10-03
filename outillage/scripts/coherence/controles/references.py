"""Contrôle references : un texte qui cite un objet emploie le nom affiché de cet objet.

1. Repérer dans l'anglais du texte les noms citables, le plus long d'abord ; le nom qu'un objet renommé tient
   de son identifiant (« Growth Totem » pour « Totem of Glowth ») et le nom qu'une coordination sous-entend
   (« Umbra or Highland Wool ») comptent aussi.
2. Identifier l'objet cité, dans cet ordre de preuve : lien explicite (objet de la tâche de quête,
   icône ou objet de l'entrée du livre, infobulle déclarée dans les scripts, clé qui prolonge celle
   de l'objet), voisinage (même namespace), épingle déclarée dans exceptions.json. Sinon :
   « référence ambiguë », bloquant — jamais l'un des homonymes au hasard.
3. Exiger dans le français le nom affiché, aux pluriels, accents, casse et élisions près ; le nom retrouvé
   s'écrit avec les accents du nom affiché (« Gobie ambré » n'est pas « Gobie ambre »).

S'y ajoutent trois lectures de liens : le nom commun d'une famille d'objets (« Sewing Needle »), le titre de quête
qui vise plusieurs objets (« Any hammer core ») et le titre d'une fiche de livre, qui nomme ce qu'elle présente.
"""
from __future__ import annotations

import re
from pathlib import Path

from compare_accents import plier

from ..modele import BLOQUANT, SIGNALE, Constat
from ..registre import CHIFFRE, CLE_OBJET
from ..texte import contient_mots, jetons, mots, racine
from .accents import accent_fautif, formes_uniques

NOM = "references"
PROLONGE_UN_OBJET = re.compile(r"^(?:item|block|entity|fluid|effect|enchantment|biome)\.([a-z0-9_]+)\.([a-z0-9_/]+)\.")
# Deux des seize couleurs de teinture de Minecraft s'écrivent en deux mots : « Light Blue », « Light Gray ».
CLAIR, COULEURS_CLAIRES = mots("Light")[0], frozenset(mots("Blue Gray"))
# Blocs dérivés que Mojang nomme d'un autre nom que leur base : Fence Gate (Portillon), Glass Pane
# (Vitre), Rose Bush (Rosier) ; Window Pane (Cluttered) suit Glass Pane.
DERIVES_RENOMMES = frozenset({mots("Fence Gate"), mots("Glass Pane"), mots("Window Pane"), mots("Rose Bush")})


def verifier(corpus, registre, config, options) -> list:
    index = _index(registre)
    liens = _liens(corpus)
    epingles = {}
    for e in config.exceptions:
        if e.get("epingle") and e.get("controle") == NOM:
            epingles.setdefault(e.get("cle"), set()).add(e.get("objet", ""))
    utilisees = set()
    formes = formes_uniques(config)
    double_sens = [(re.compile(rf"\b(?:{r['anglais']})\b", re.I), {plier(j): j for j in r["justes"]})
                   for r in config.double_sens]

    def mal_accentue(en: str):
        """Le mot est-il mal accentué selon le vocabulaire, ou selon un double sens que l'anglais tranche ?"""
        def verdict(mot: str) -> bool:
            juste = formes.get(plier(mot))
            if juste and accent_fautif(mot, juste):
                return True
            justes = [j[plier(mot)] for anglais, j in double_sens if plier(mot) in j and anglais.search(en)]
            return bool(justes) and mot.lower() not in justes
        return verdict

    constats = []
    for cle, en, fr, ns in _textes(corpus):
        mots_fr, vus, est_un_nom = mots(fr), set(), cle in registre.noms
        for motif, candidats in _citations(jetons(en), index, est_un_nom):
            candidats = [n for n in candidats if n.cle != cle]
            if not candidats:
                continue
            vise = _resoudre(cle, ns, candidats, liens, epingles, utilisees)
            marque = vise.cle if vise else motif
            if marque in vus:
                continue
            vus.add(marque)
            if vise is None:
                constats.append(Constat(
                    NOM, cle, BLOQUANT, actuel=fr, objet=candidats[0].en,
                    detail=f"référence ambiguë : « {candidats[0].en} » désigne plusieurs objets ; épingler le bon",
                    preuve=" ; ".join(f"{n.cle} = {n.fr}" for n in candidats)))
            elif not _present(mots_fr, mots(vise.fr), est_un_nom):
                constats.append(Constat(
                    NOM, cle, BLOQUANT, actuel=fr, attendu=vise.fr, objet=vise.cle,
                    detail=f"cite « {vise.en} », dont le nom affiché est « {vise.fr} »", preuve=vise.cle))
            else:
                ecart = _accents_ecartes(fr, vise.fr, mal_accentue(en), mal_accentue(vise.en))
                if ecart:
                    constats.append(Constat(
                        NOM, cle, BLOQUANT, actuel=fr, attendu=vise.fr, objet=vise.cle, preuve=vise.cle,
                        detail=f"cite « {vise.en} » en écrivant « {ecart[0]} » : le nom affiché « {vise.fr} » "
                               f"écrit « {ecart[1]} »"))
    constats += _noms_de_familles(corpus, registre, index, liens)
    constats += _titres_a_plusieurs_objets(corpus, registre, liens, {c.cle for c in constats})
    constats += _titres_de_fiches(corpus, registre, config, {c.cle for c in constats})
    for cle, objets in sorted(epingles.items()):
        for objet in sorted(objets):
            if (cle, objet) not in utilisees:
                constats.append(Constat(NOM, cle, SIGNALE, objet=objet, detail="épingle inutilisée : à retirer"))
    return constats


MOTS_VIDES = frozenset(mots("de d du des en à au aux la le les l un une"))
MOTS_OUTILS_EN = frozenset(mots("the of from with s a an and or for in on to at by"))
MOT_ECRIT = re.compile(r"[^\W_]+")


def _noms_de_familles(corpus, registre, index, liens) -> list:
    """Un texte qui cite le nom commun d'une famille d'objets reprend leur début commun en français :
    « Sewing Needle », fin commune de « Iron Sewing Needle » et « Gold Sewing Needle », s'écrit « Aiguille
    de couture ». La fin compte deux mots au moins, n'est ni le nom d'un objet ni un mot générique, et n'est
    pas lue dans un nom plus long qu'elle termine (« Iron Sewing Needle » cite l'aiguille de fer). Seuls la
    lisent les textes liés à un objet de la famille (tâche de quête, infobulle, fiche de livre) et les étiquettes
    des groupes d'objets (stackgroup) : ailleurs, deux mots communs n'y suffisent pas."""
    familles = {}
    for fin, (debut, noms) in _familles(registre).items():
        familles.setdefault(fin[0], []).append((fin, debut, noms))
    for liste in familles.values():
        liste.sort(key=lambda f: -len(f[0]))
    noms_complets = {motif for liste in index.values() for motif, _ in liste}
    constats = []
    for cle, en, fr, _ in _textes(corpus):
        lies, groupe = _lies(cle, liens), cle.startswith("stackgroup.")
        if not lies and not groupe:
            continue
        suite, mots_fr, vus = mots(en), mots(fr), set()
        for i in range(len(suite)):
            for fin, debut, noms in familles.get(suite[i], ()):
                if suite[i:i + len(fin)] != fin or fin in vus:
                    continue
                if not groupe and not any(n.identifiant in lies for n in noms):
                    continue
                if any(suite[i - j:i] + fin in noms_complets for j in (1, 2, 3) if i - j >= 0):
                    break
                vus.add(fin)
                if not contient_mots(mots_fr, debut):
                    attendu = _debut_ecrit(noms[0].fr, len(debut))
                    anglais = " ".join(MOT_ECRIT.findall(noms[0].en)[-len(fin):])
                    constats.append(Constat(
                        NOM, cle, BLOQUANT, actuel=fr, attendu=attendu, objet=anglais,
                        preuve=" ; ".join(f"{n.cle} = {n.fr}" for n in noms[:5]),
                        detail=f"cite « {anglais} », nom commun de {len(noms)} objets (« {noms[0].fr} »…) : "
                               f"« {attendu} »"))
                break
    return constats


def _familles(registre) -> dict:
    """Fin anglaise commune (deux mots ou plus) -> (début français commun, noms) des objets qui la partagent."""
    membres = {}
    for nom in registre.noms.values():
        if CLE_OBJET.match(nom.cle) and registre.citable(nom) and RETIRE not in mots(nom.en):
            motif = mots(nom.en)
            for t in range(2, len(motif)):
                membres.setdefault(motif[-t:], []).append(nom)
    familles = {}
    for fin, noms in membres.items():
        if len(noms) < 2 or fin[0] in MOTS_OUTILS_EN or fin in registre.homographes or fin in registre.generiques:
            continue
        debut = mots(noms[0].fr)
        for nom in noms[1:]:
            autre = mots(nom.fr)
            k = 0
            while k < min(len(debut), len(autre)) and debut[k] == autre[k]:
                k += 1
            debut = debut[:k]
        while debut and debut[-1] in MOTS_VIDES:
            debut = debut[:-1]
        if debut:
            familles[fin] = (debut, sorted(noms, key=lambda n: n.cle))
    return familles


def _debut_ecrit(nom: str, n: int) -> str:
    """Les n premiers mots du nom, tels qu'il les écrit (« Oeuf d'apparition »)."""
    trouves = list(MOT_ECRIT.finditer(nom))
    return nom[:trouves[n - 1].end()] if len(trouves) >= n else nom


TITRE_DE_QUETE = re.compile(r"^ftbquests\..*\.(?:title|subtitle)$")
QUELCONQUE = mots("any")[0]


def _titres_a_plusieurs_objets(corpus, registre, liens, deja_releves=frozenset()) -> list:
    """Un titre de quête ou de tâche qui vise plusieurs objets et reprend un mot que partage leur anglais
    (« Any Log » : Oak Log, Birch Log) reprend le mot que partage leur français (« bûche ») ; s'ils n'en
    partagent aucun (« Any hammer core » : « Petit noyau », « Coeur d'impact »), le titre ne peut pas être juste
    et le constat le dit. Un titre dont une citation est déjà relevée n'en reçoit pas un second constat."""
    constats = []
    for cle, fr in corpus.textes_projet():
        if not TITRE_DE_QUETE.match(cle) or cle in deja_releves:
            continue
        en = corpus.anglais(cle)
        titre = set(mots(en)) - MOTS_OUTILS_EN - {QUELCONQUE}
        vises = {}
        for ident in sorted(liens.get(cle, ())):
            for nom in registre.par_identifiant.get(ident, []):
                if titre & set(mots(nom.en)):
                    vises.setdefault(nom.cle, nom)
        if len(vises) < 2:
            continue
        vises = list(vises.values())
        communs_en = titre.intersection(*(set(mots(n.en)) for n in vises))
        if not communs_en:
            continue
        anglais = next(ecrit for m, ecrit, _ in jetons(en) if m in communs_en)
        communs_fr = set.intersection(*(set(_au_masculin(mots(n.fr))) - MOTS_VIDES for n in vises))
        noms_fr = ", ".join(f"« {n.fr} »" for n in vises)
        if not communs_fr:
            constats.append(Constat(NOM, cle, BLOQUANT, actuel=fr, objet=vises[0].cle,
                                    preuve=" ; ".join(n.cle for n in vises),
                                    detail=f"vise {noms_fr}, qui ne partagent aucun mot pour « {anglais} »"))
        elif not communs_fr & set(_au_masculin(mots(fr))):
            attendu = next(ecrit for m, ecrit, _ in jetons(vises[0].fr) if _au_masculin((m,))[0] in communs_fr)
            constats.append(Constat(NOM, cle, BLOQUANT, actuel=fr, attendu=attendu, objet=vises[0].cle,
                                    preuve=" ; ".join(n.cle for n in vises),
                                    detail=f"vise {noms_fr}, dont « {anglais} » se dit « {attendu} »"))
    return constats


POUSSE = re.compile(r"^Pousses? (?:de |d'|des )?", re.I)
ARBRE = mots("tree")[0]


def _titres_de_fiches(corpus, registre, config, deja_releves=frozenset()) -> list:
    """Le titre d'une fiche de livre nomme ce qu'elle présente, même quand son anglais ne le cite pas (coquille,
    nom d'avant un renommage) :
    - l'objet lié dont l'identifiant porte le nom du fichier (fish/duality_damselfish.json), ou l'un de ceux qui
      le partagent (l'animal et sa viande : minecraft:chicken) ;
    - pour une fiche d'arbre (« Pine Tree »), l'arbre de la pousse liée (« Pousse alpine » : alpin, au genre
      près ; une faute connue du nom de la pousse, « pallisandre », corrigée) ;
    - pour un nom de page, le gabarit du nom de l'objet lié rempli du titre de la fiche (« %s Slime » s'affiche
      « Slime %s » : la page « Ender Slime » de la fiche « Ender » s'écrit « Slime Ender »).
    Un champ dont une citation est déjà relevée n'en reçoit pas un second constat."""
    fautes = [(re.compile(rf"(?<!\w){re.escape(f['forme'])}(?!\w)", 0 if f.get("casse") else re.I), f["juste"])
              for f in config.formes_interdites]  # comme le contrôle orthographe : une forme à « casse » est exacte
    titres = {champ.fichier: champ for champ in corpus.livres if champ.pointeur == "/name"}
    constats = []
    for champ in corpus.livres:
        if not champ.fr.strip() or champ.cle in deja_releves:
            continue
        lies = [nom for ident in champ.objets for nom in registre.par_identifiant.get(ident, [])]
        mots_fr, mots_en, ecart = mots(champ.fr), mots(champ.en), None
        if champ.pointeur == "/name":
            tige = Path(champ.fichier).stem
            eponymes = [nom for nom in lies if nom.identifiant.split(":")[1] == tige]
            if eponymes and not any(contient_mots(mots_en, mots(nom.en)) or contient_mots(mots_fr, mots(nom.fr))
                                    for nom in eponymes):
                nom = eponymes[0]
                ecart = (nom, nom.fr, f"la fiche présente « {nom.en} », dont le nom affiché est « {nom.fr} »")
            pousses = [nom for nom in lies if nom.identifiant.endswith("_sapling")]
            if ecart is None and len(mots_en) > 1 and mots_en[-1] == ARBRE and len(pousses) == 1:
                arbre = POUSSE.sub("", pousses[0].fr)
                for faute, juste in fautes:
                    arbre = faute.sub(juste, arbre)
                if arbre != pousses[0].fr and not contient_mots(_au_masculin(mots_fr), _au_masculin(mots(arbre))):
                    ecart = (pousses[0], arbre,
                             f"la fiche d'arbre ne nomme pas l'arbre de sa pousse « {pousses[0].fr} »")
        elif champ.fichier in titres:
            titre = titres[champ.fichier]
            for nom in lies:
                if nom.en.count("%s") == 1 and nom.fr.count("%s") == 1 and \
                        mots(nom.en.replace("%s", titre.en)) == mots_en:
                    rempli = nom.fr.replace("%s", titre.fr).strip()
                    if not contient_mots(mots_fr, mots(rempli)):
                        ecart = (nom, rempli, f"« {champ.en} » s'affiche « {nom.fr} » rempli du titre de la fiche")
                    break
        if ecart:
            nom, attendu, detail = ecart
            constats.append(Constat(NOM, champ.cle, BLOQUANT, actuel=champ.fr, attendu=attendu, objet=nom.cle,
                                    detail=detail, preuve=nom.cle))
    return constats


def _au_masculin(suite) -> tuple:
    """Les mots sans leur marque de féminin (« alpine », « ancienne », « imitatrice » : alpin, ancien,
    imitateur) : un arbre est masculin, sa pousse féminine ; un adjectif suit le nom qu'il qualifie."""
    resultat = []
    for mot in suite:
        if len(mot) > 5 and mot.endswith("trice"):
            mot = mot[:-5] + "teur"
        elif len(mot) > 3 and mot.endswith("e"):
            mot = mot[:-1]
            if len(mot) > 2 and mot[-1] == mot[-2] and mot[-1] in "lnt":
                mot = mot[:-1]
        resultat.append(mot)
    return tuple(resultat)


def _present(mots_fr, mots_nom, dans_un_nom) -> bool:
    """Le nom figure-t-il dans le français ? Dans un nom composé, ses mots peuvent être séparés
    (« Petite porte à barreaux en chêne » contient « Porte en chêne ») : le français place les
    qualificatifs autour du nom qu'ils qualifient."""
    if contient_mots(mots_fr, mots_nom):
        return True
    if not dans_un_nom or not mots_nom:
        return False
    positions, depart = [], 0
    for mot in mots_nom:
        try:
            depart = mots_fr.index(mot, depart) + 1
        except ValueError:
            return False
        positions.append(depart)
    return positions[-1] - positions[0] < len(mots_nom) + 3


def _ecriture(ecrit: str) -> str:
    """La forme écrite d'un mot, comparable à une autre aux seuls accents près : minuscules, ligatures
    dénouées, pluriel régulier neutralisé."""
    return racine(ecrit.lower().replace("œ", "oe").replace("æ", "ae"))


def _accents_ecartes(fr: str, nom: str, texte_fautif=lambda mot: False, nom_fautif=lambda mot: False):
    """(mot du texte, mot du nom) quand aucune occurrence du nom dans le texte ne l'écrit avec ses accents ;
    None si l'une l'écrit comme le nom affiché, ou si le nom n'y figure pas d'un seul tenant. Un écart dont
    l'un des mots est mal accentué (vocabulaire figé, double sens) ne compte pas : le texte fautif relève du
    contrôle accents, le nom affiché fautif (« Fenètre » d'un jar) de sa propre correction."""
    suite, modele = jetons(fr), jetons(nom)
    attendus, n, ecart = [m for m, _, _ in modele], len(modele), None
    for i in range(len(suite) - n + 1):
        if [m for m, _, _ in suite[i:i + n]] != attendus:
            continue
        difference = next(((a, b) for (_, a, _), (_, b, _) in zip(suite[i:i + n], modele)
                           if _ecriture(a) != _ecriture(b) and not texte_fautif(a) and not nom_fautif(b)), None)
        if difference is None:
            return None
        ecart = ecart or difference
    return ecart


def _textes(corpus):
    for cle, fr in corpus.textes_projet():
        en = corpus.anglais(cle)
        m = CLE_OBJET.match(cle)
        if cle.startswith("block_type.") or ("%" in en and m):
            continue  # gabarits : leur nom vient d'ailleurs, les contrôles everycomp et codes les suivent
        if en.strip() and fr.strip():
            # le namespace d'un nom est celui de sa clé, pas celui du fichier qui la surcharge
            yield cle, en, fr, m.group(2) if m else corpus.ns_projet.get(cle, "")
    for champ in corpus.livres:
        if champ.en.strip() and champ.fr.strip():
            yield champ.cle, champ.en, champ.fr, ""


def _index(registre) -> dict:
    """Premier mot -> [(motif, noms)], les motifs les plus longs d'abord ; les noms d'origine des objets
    renommés (_alias) y figurent aussi."""
    motifs = dict(registre.par_anglais)
    for motif, noms in _alias(registre).items():
        motifs.setdefault(motif, noms)
    index = {}
    for motif, noms in motifs.items():
        if motif:
            index.setdefault(motif[0], []).append((motif, noms))
    for liste in index.values():
        liste.sort(key=lambda paire: -len(paire[0]))
    return index


EFFET = mots("effect")[0]
RETIRE = mots("removed")[0]


def _alias(registre) -> dict:
    """Motif -> noms : le nom qu'un objet renommé tient de son identifiant (« growth_totem », affiché
    « Totem of Glowth ») ; un anglais resté sur l'ancien nom (« Growth Totem ») le cite encore.

    L'alias doit être distinctif : ni un mot générique, ni une partie d'un nom anglais du registre, le sien
    compris (« fence_gate » d'une barrière enneigée, « willow_door » de « Mystic Willow Door »), au pluriel,
    au possessif et aux traits d'union près (« Gearo Berries », « Dolphin's Grace », « Tri-bull »). D'un seul
    mot, il ne vaut que pour un effet, cité « X effect » (« Drunk effect ») ; un objet retiré (« REMOVED ») n'en
    a pas."""
    parties, colles = set(), set()
    for motif in registre.homographes:
        forme = _sans_flexion(motif)
        parties.update(forme[i:j] for i in range(len(forme)) for j in range(i + 1, len(forme) + 1))
        colles.add("".join(forme))
    alias = {}
    for nom in registre.noms.values():
        m = CLE_OBJET.match(nom.cle)
        if not m or CHIFFRE.search(m.group(3)) or not registre.citable(nom) or RETIRE in mots(nom.en):
            continue
        motif = mots(m.group(3).replace("_", " ").replace("/", " "))
        forme = _sans_flexion(motif)
        if not motif or motif in registre.generiques or forme in parties or "".join(forme) in colles:
            continue
        if len(motif) == 1:
            if len(motif[0]) < 5 or not nom.cle.startswith("effect."):
                continue
            motif += (EFFET,)
        alias.setdefault(motif, []).append(nom)
    return alias


def _sans_flexion(motif) -> tuple:
    """Le motif sans possessif ni pluriel en -ies (« Dolphin's », « Berries »), pour comparer des noms anglais."""
    return tuple(m[:-2] + "y" if m.endswith("ie") else m for m in motif if m != "s")


def _citations(jetons_en, index, est_un_nom):
    """(motif, noms) de chaque nom cité, sans chevauchement ; un nom ne se cite pas lui-même en entier.

    Un nom d'un seul mot est cité comme un autre, dans un nom comme dans une phrase ; un matériau se déclare par
    une exception à objet, un mot qui ne cite jamais son objet dans mots_generiques.json (spec 2 §7, fiche du
    30/09 : meme-mod).

    Deux suites de mots désignent autre chose que le nom qu'elles contiennent : une couleur claire
    (« Light Blue Bath » ne cite pas « Blue Bath ») et un dérivé que Mojang renomme (« Oak Fence
    Gate », un portillon, ne cite pas « Oak Fence »)."""
    mots_en = tuple(m for m, _, _ in jetons_en)
    i, n = 0, len(mots_en)
    while i < n:
        for motif, noms in index.get(mots_en[i], ()):
            k = len(motif)
            if tuple(mots_en[i:i + k]) != motif or (est_un_nom and i == 0 and k == n):
                continue
            if (i and mots_en[i - 1] == CLAIR and motif[0] in COULEURS_CLAIRES) or \
                    (i + k < n and (motif[-1], mots_en[i + k]) in DERIVES_RENOMMES):
                continue
            yield motif, noms
            yield from _ellipse(mots_en, i, motif, index)
            i += k
            break
        else:
            i += 1


COORDINATION = frozenset(mots("or and"))


def _ellipse(mots_en, i, motif, index):
    """Le nom qu'une coordination sous-entend : « Umbra or Highland Wool » cite aussi « Umbra Wool », « Dark
    Oak and Birch Planks » « Dark Oak Planks ». Le nom trouvé en i garde sa tête ; deux mots avant la
    conjonction, puis un seul, en prennent le modificateur, si le nom ainsi formé existe : le plus long d'abord,
    sans quoi « Oak Planks » (vanilla) masquerait « Dark Oak Planks »."""
    if i < 2 or mots_en[i - 1] not in COORDINATION:
        return
    for garde in range(1, len(motif)):
        for j in (2, 1):
            if i - 1 - j < 0:
                continue
            autre = tuple(mots_en[i - 1 - j:i - 1]) + motif[garde:]
            for candidat, noms in index.get(autre[0], ()):
                if candidat == autre:
                    yield candidat, noms
                    return


def _liens(corpus) -> dict:
    """Clé de texte -> identifiants des objets qu'elle désigne explicitement."""
    liens = {}

    def lier(cle, ids):
        if cle and ids:
            liens.setdefault(cle, set()).update(ids)

    for quete in corpus.quetes:
        titres = {t.cle_titre for t in quete.taches}
        tous = {o for t in quete.taches for o in t.objets} | ({quete.icone} if quete.icone else set())
        for cle in set(quete.cles) - titres:
            lier(cle, tous)
        for tache in quete.taches:
            lier(tache.cle_titre, set(tache.objets))
    for cle, ids in corpus.infobulles.items():
        lier(cle, set(ids))
    for champ in corpus.livres:
        lier(champ.cle, set(champ.objets))
    return liens


def _un_seul_francais(noms) -> bool:
    return len({tuple(mots(n.fr)) for n in noms}) == 1


def _lies(cle, liens) -> set:
    """Les objets que le texte désigne explicitement, clé prolongée comprise."""
    lies = set(liens.get(cle, ()))
    m = PROLONGE_UN_OBJET.match(cle)
    if m:
        lies.add(f"{m.group(1)}:{m.group(2)}")
    return lies


def _resoudre(cle, ns, candidats, liens, epingles, utilisees):
    if _un_seul_francais(candidats):
        # Même nom affiché partout : le texte attendu ne dépend pas de l'objet retenu, mais l'objet du constat, si ;
        # une épingle le fixe, pour que la dette et les exceptions qui le nomment le retrouvent.
        for n in candidats:
            if n.cle in epingles.get(cle, ()):
                utilisees.add((cle, n.cle))
                return n
        return candidats[0]
    lies = _lies(cle, liens)
    for garde in (lambda n: n.identifiant in lies,
                  lambda n: bool(ns) and n.identifiant.split(":")[0] == ns):
        retenus = [n for n in candidats if garde(n)]
        if retenus and _un_seul_francais(retenus):
            return retenus[0]
    for n in candidats:
        if n.cle in epingles.get(cle, ()):
            utilisees.add((cle, n.cle))
            return n
    return None
