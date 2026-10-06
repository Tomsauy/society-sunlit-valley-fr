"""Les paquets des agents (spec 3 §5) : ce que chaque filet a le droit de voir, et la forme exacte de ce qu'il rend.

Un paquet est un fichier `<nnn>.entree.json` ; l'agent écrit à côté `<nnn>.sortie.json`. Une sortie n'est lue que si
`valider` ne lui trouve aucun problème : une clé en trop, en moins ou en double, un champ manquant, une classe
inconnue, une correction vide ou identique au texte refusent tout le paquet."""
from __future__ import annotations

import json
import re
from pathlib import Path

TAILLE = 100              # spec 3 §9 : des paquets d'une centaine de textes
TAILLE_AVIS = 25          # confirmation, mesure et tiers : chaque élément demande des recherches
CONSIGNES = Path("fr-workspace/chasse/consignes")
# Ce que chaque filet voit. F1 ne voit jamais l'anglais d'origine avant sa rétrotraduction, ni le français pendant la
# comparaison ; F2 ne voit jamais l'anglais (spec 3 §5).
VUS = {
    "F1-retro": ("id", "espace", "fr"),
    "F1-comparaison": ("id", "espace", "en", "retro"),
    "F2": ("id", "espace", "fr"),
    "mesure": ("id", "espace", "en", "fr", "temoins"),
    "confirmation": ("id", "espace", "en", "fr", "temoins", "notes"),
    "tiers-mesure": ("id", "espace", "en", "fr", "temoins", "avis"),
    "tiers-confirmation": ("id", "espace", "en", "fr", "temoins", "notes", "avis"),
}
FICHIER_CONSIGNE = {"F1-retro": "F1-retrotraduction.md", "F1-comparaison": "F1-comparaison.md", "F2": "F2-lecture.md",
                    "mesure": "mesure-relecteur.md", "confirmation": "confirmation.md",
                    "tiers-mesure": "tiers.md", "tiers-confirmation": "tiers.md"}
CLASSES = {"mesure": ("majeur", "mineur", "correct"), "confirmation": ("majeur", "mineur", "fausse_alerte")}
DEFAUTS = ("majeur", "mineur")
PREUVE = re.compile(r"^(cle|fichier|temoin|jeu):\S")


def famille_de(filet: str) -> str:
    """« mesure » ou « confirmation » pour un filet d'avis ; vide pour F1 et F2."""
    return filet.replace("tiers-", "") if filet.replace("tiers-", "") in CLASSES else ""


def entrees(filet: str, nom: str, elements: list, taille: int = 0) -> list:
    """Les paquets d'un filet : chaque élément réduit à ce que le filet voit, par paquets de `taille`, numérotés
    « <nom>/<filet>/001 »…"""
    if filet not in VUS:
        raise ValueError(f"filet inconnu : {filet}")
    taille = taille or (TAILLE_AVIS if famille_de(filet) else TAILLE)
    vus = VUS[filet]
    reduits = [{k: e[k] for k in vus if k in e} for e in elements]
    for e in reduits:
        manque = [k for k in ("id", "fr", "en", "retro") if k in vus and k not in e]
        if manque:
            raise ValueError(f"{e.get('id')} : {', '.join(manque)} manque pour le filet {filet}")
    return [{"paquet": f"{nom}/{filet}/{i // taille + 1:03d}", "filet": filet,
             "consigne": (CONSIGNES / FICHIER_CONSIGNE[filet]).as_posix(), "elements": reduits[i:i + taille]}
            for i in range(0, len(reduits), taille)]


def ecrire_entrees(dossier, paquets: list) -> list:
    """Écrit chaque paquet sous <dossier>/<filet>/<nnn>.entree.json ; rend les chemins."""
    chemins = []
    for p in paquets:
        chemin = Path(dossier) / p["filet"] / f"{p['paquet'].rsplit('/', 1)[1]}.entree.json"
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(json.dumps(p, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        chemins.append(chemin)
    return chemins


def _texte(v) -> bool:
    return isinstance(v, str) and bool(v.strip())


def valider(entree: dict, sortie) -> list:
    """Les problèmes d'une sortie face à son paquet ; vide si elle est bonne."""
    if not isinstance(sortie, dict):
        return ["la sortie n'est pas un objet JSON"]
    problemes = []
    if sortie.get("paquet") != entree["paquet"]:
        problemes.append(f"« paquet » vaut {sortie.get('paquet')!r}, attendu {entree['paquet']!r}")
    items = sortie.get("sorties")
    if not isinstance(items, list) or not all(isinstance(x, dict) for x in items):
        return problemes + ["« sorties » : une liste d'objets est attendue"]
    mauvais = [f"{n} : « id » doit être une chaîne" for n, x in enumerate(items, start=1) if not isinstance(x.get("id"), str)]
    if mauvais:
        return problemes + mauvais
    attendus = [e["id"] for e in entree["elements"]]
    rendus = [x.get("id") for x in items]
    for i in sorted({i for i in rendus if rendus.count(i) > 1}, key=str):
        problemes.append(f"{i} : rendu {rendus.count(i)} fois")
    for i in sorted(set(attendus) - set(rendus)):
        problemes.append(f"{i} : manque dans la sortie")
    for i in sorted({i for i in rendus if i not in set(attendus)}, key=str):
        problemes.append(f"{i} : n'est pas dans le paquet")
    fr_de = {e["id"]: e.get("fr", "") for e in entree["elements"]}
    filet, famille = entree["filet"], famille_de(entree["filet"])
    for x in items:
        if x.get("id") not in fr_de:
            continue
        ou = x["id"]
        if filet == "F1-retro" and not _texte(x.get("retro")):
            problemes.append(f"{ou} : « retro » vide")
        elif filet in ("F1-comparaison", "F2"):
            drapeau = "ecart" if filet == "F1-comparaison" else "accroche"
            if not isinstance(x.get(drapeau), bool):
                problemes.append(f"{ou} : « {drapeau} » : true ou false")
            elif x[drapeau] and not _texte(x.get("note")):
                problemes.append(f"{ou} : « note » vide pour un signalement")
        elif famille:
            if x.get("classe") not in CLASSES[famille]:
                problemes.append(f"{ou} : « classe » parmi {', '.join(CLASSES[famille])}")
                continue
            if not _texte(x.get("raison")):
                problemes.append(f"{ou} : « raison » vide")
            preuves = x.get("preuves", [])
            if not isinstance(preuves, list) or not all(isinstance(p, str) and PREUVE.match(p) for p in preuves):
                problemes.append(f"{ou} : « preuves » : une liste de « cle:… », « fichier:… », « temoin:… », « jeu:… »")
            if "question" in x and not _texte(x["question"]):
                problemes.append(f"{ou} : « question » vide")
            if x["classe"] in DEFAUTS and "question" not in x:
                if not _texte(x.get("correction")):
                    problemes.append(f"{ou} : « correction » vide pour un défaut")
                elif x["correction"] == fr_de[ou]:
                    problemes.append(f"{ou} : « correction » identique au texte")
    return problemes


def verifier_preuve(preuve: str, cles: set, racines: list) -> str:
    """Le problème d'une preuve, vide si elle tient : « cle:<clé> » doit exister dans le corpus, « fichier:<chemin>[:<ligne>] »
    dans l'un des dossiers `racines`, à une ligne qui existe. « temoin:… » et « jeu:… » se relisent à la main."""
    genre, _, valeur = preuve.partition(":")
    if genre == "cle":
        return "" if valeur in cles else f"{preuve} : clé inconnue du corpus"
    if genre == "fichier":
        chemin, _, ligne = valeur.partition(":")
        for racine in racines:
            cible = Path(racine) / chemin
            if cible.is_file():
                if ligne and (not ligne.isdigit() or not 0 < int(ligne) <= len(cible.read_text(encoding="utf-8",
                                                                                        errors="replace").splitlines())):
                    return f"{preuve} : ligne {ligne} hors du fichier"
                return ""
        return f"{preuve} : fichier introuvable"
    return ""


def nom_sortie(entree_chemin: Path, relecteur: str = "") -> Path:
    """« 001.entree.json » -> « 001.sortie.json », ou « 001.sortie-A.json » pour le relecteur A."""
    return entree_chemin.with_name(entree_chemin.name.replace(".entree.", f".sortie{'-' + relecteur if relecteur else ''}."))


def textes_lus(dossier, filet: str) -> dict:
    """{id : français} des paquets d'un filet : ce que les agents ont lu."""
    return {e["id"]: e.get("fr", "") for chemin in sorted((Path(dossier) / filet).glob("*.entree.json"))
            for e in json.loads(chemin.read_text(encoding="utf-8"))["elements"]}


def lire_sorties(dossier, filet: str, relecteur: str = "", numero: str = "") -> tuple:
    """({id : élément rendu}, problèmes) pour tous les paquets d'un filet sous <dossier>/<filet>/ (ou le seul paquet
    `numero`, « 007 »), rendus par `relecteur` (A, B ou C pour les avis). Un paquet sans sortie, ou dont la sortie a
    un problème, n'apporte rien et nomme son problème."""
    rendus, problemes = {}, []
    for chemin in sorted((Path(dossier) / filet).glob(f"{numero or '*'}.entree.json")):
        entree = json.loads(chemin.read_text(encoding="utf-8"))
        cible = nom_sortie(chemin, relecteur)
        if not cible.is_file():
            problemes.append(f"{entree['paquet']} : pas de sortie ({cible.name})")
            continue
        try:
            sortie = json.loads(cible.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            problemes.append(f"{entree['paquet']} : sortie illisible ({e})")
            continue
        p = valider(entree, sortie)
        problemes += [f"{entree['paquet']} : {x}" for x in p]
        if not p:
            rendus.update({x["id"]: x for x in sortie["sorties"]})
    return rendus, problemes
