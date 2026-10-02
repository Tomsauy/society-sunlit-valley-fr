"""L'applicateur (spec 2 §8) : contrôle un lot, puis l'écrit tout entier ou pas du tout.

Il est le seul à écrire les actions d'un lot : les textes du pack (fichiers de langue du projet, pages des livres,
journal, surcharges des traductions officielles), provenance.json, les exceptions, les mots génériques et les
renvois. Mojang n'est jamais surchargé (spec 2 §2). Chaque fichier garde son format : langue en JSON trié indenté
à 2, livres indentés à 4, données du vérificateur et provenance indentées à 1."""
from __future__ import annotations

import datetime
import json
from dataclasses import dataclass, field
from pathlib import Path

from coherence import config as config_mod
from coherence.corpus import CLE_JOURNAL, JOURNAL
from coherence.rapport import empreinte, objet_de

LANGUE = "kubejs/assets/{}/lang/fr_fr.json"
FICHIER_JOURNAL = (JOURNAL / "changelog_fr_fr.markdown").as_posix()


@dataclass
class Plan:
    lot: dict
    textes: dict = field(default_factory=dict)        # fichier relatif à la racine du pack -> {clé ou pointeur : texte}
    journal: object = None                            # le nouveau texte du journal, s'il change
    traces: list = field(default_factory=list)        # (clé, entrée de provenance)
    exceptions: list = field(default_factory=list)    # à ajouter, ou à mettre à la place de celle de même triplet
    retraits: list = field(default_factory=list)      # triplets des exceptions à retirer
    generiques: dict = field(default_factory=dict)
    renvois: list = field(default_factory=list)
    deja: list = field(default_factory=list)          # indices des actions déjà appliquées : rien à écrire
    refus: list = field(default_factory=list)         # (indice de l'action, raison)

    def bilan(self) -> str:
        types = {}
        for a in self.lot["actions"]:
            types[a["type"]] = types.get(a["type"], 0) + 1
        compte = ", ".join(f"{n} {t}" for t, n in sorted(types.items())) or "aucune action"
        fichiers = len(self.textes) + (self.journal is not None)
        return (f"{self.lot['lot']} : {compte} ; {len(self.deja)} déjà appliquée(s) ; "
                f"{fichiers} fichier(s) de texte à écrire ; {len(self.refus)} refus")


def triplet_exc(e) -> tuple:
    return e.get("controle"), e.get("cle"), objet_de(e.get("objet"))


def espaces_des_jars(espace) -> dict:
    """Clé -> espace de noms du mod qui la définit dans son jar (extracted/<jar>/<espace>/), pour y poser sa
    surcharge ; la première trouvée, dans l'ordre des dossiers."""
    espaces = {}
    extraits = Path(espace) / "extracted"
    if not extraits.is_dir():
        return espaces
    for jar in sorted(p for p in extraits.iterdir() if p.is_dir()):
        for ns in sorted(p for p in jar.iterdir() if p.is_dir()):
            for nom in ("en_us.json", "fr_fr.json"):
                chemin = ns / nom
                if chemin.is_file():
                    for cle in json.loads(chemin.read_text(encoding="utf-8-sig")):
                        espaces.setdefault(cle, ns.name)
    return espaces


def _livre(cle: str):
    """« <livre>/<fichier>#<pointeur> » -> (fichier relatif à la racine du pack, pointeur)."""
    fichier, pointeur = cle.split("#", 1)
    livre, reste = fichier.split("/", 1)
    return f"patchouli_books/{livre}/fr_fr/{reste}", pointeur


def _lire_pointeur(chemin: Path, pointeur: str):
    """Le texte au pointeur d'un fichier de livre ; None si le fichier ou le pointeur manque."""
    try:
        objet = json.loads(chemin.read_text(encoding="utf-8"))
        for morceau in pointeur.strip("/").split("/"):
            objet = objet[int(morceau)] if isinstance(objet, list) else objet[morceau]
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        return None
    return objet if isinstance(objet, str) else None


def _poser(objet, pointeur: str, valeur: str) -> None:
    morceaux = pointeur.strip("/").split("/")
    for morceau in morceaux[:-1]:
        objet = objet[int(morceau)] if isinstance(objet, list) else objet[morceau]
    if isinstance(objet, list):
        objet[int(morceaux[-1])] = valeur
    else:
        objet[morceaux[-1]] = valeur


def _entree(lot, type_, fr, action, jour) -> dict:
    entree = {"type": type_, "lot": lot["lot"], "fr": fr, "raison": action["motif"], "date": jour}
    if action.get("question"):
        entree["question"] = action["question"]
    return entree


def planifier(lot, corpus, config, racine, espace, jour=None) -> Plan:
    """Contrôle chaque action du lot et prépare ses écritures ; rien n'est écrit (voir ecrire)."""
    plan = Plan(lot)
    jour = jour or datetime.date.today().isoformat()
    racine = Path(racine)
    perimetre = set(lot["perimetre"])
    jars = espaces_des_jars(espace)
    fichiers_projet = {}
    for ns, cle in corpus.projet:
        fichiers_projet.setdefault(cle, []).append(ns)
    finales = {}
    for i, a in enumerate(lot["actions"]):
        if a["type"] != "mot_generique" and a["cle"] not in perimetre:
            plan.refus.append((i, f"{a['cle']} : hors du périmètre du lot"))
        elif a["type"] == "correction":
            if a["cle"] in finales:
                plan.refus.append((i, f"{a['cle']} : deux corrections de la même clé dans le lot"))
            else:
                finales[a["cle"]] = a["apres"]
                _corriger(plan, i, a, corpus, racine, fichiers_projet, jars, jour)
    refusees = {i for i, _ in plan.refus}
    texte_final = lambda cle: finales.get(cle, corpus.texte(cle))  # noqa: E731
    existantes = {triplet_exc(e): e for e in config.exceptions if not e.get("epingle")}
    for i, a in enumerate(lot["actions"]):
        if i in refusees or a["type"] == "correction":
            continue
        if a["type"] == "trace":
            _tracer(plan, i, a, config, texte_final, jour)
        elif a["type"] == "exception":
            _excepter(plan, i, a, existantes, texte_final, jour)
        elif a["type"] == "retrait":
            # Un retrait qui ne retire rien est un refus : rejouer un lot ne doit pas masquer une cible erronée.
            t = (a["controle"], a["cle"], objet_de(a.get("objet")))
            if t in existantes:
                plan.retraits.append(t)
            elif any(triplet_exc(e) == t for e in config.exceptions):
                plan.refus.append((i, f"{a['cle']} : exception épinglée, jamais retirée par un lot"))
            else:
                plan.refus.append((i, f"{a['cle']} : aucune exception {a['controle']} à retirer pour cette clé"
                                      " et cet objet"))
        elif a["type"] == "mot_generique":
            if config.mots_generiques.get(a["mot"]) == a["motif"]:
                plan.deja.append(i)
            else:
                plan.generiques[a["mot"]] = a["motif"]
        else:  # renvoi
            entree = {k: a[k] for k in ("controle", "cle", "objet", "motif") if k in a}
            (plan.deja.append(i) if entree in config.renvois else plan.renvois.append(entree))
    return plan


def _corriger(plan, i, a, corpus, racine, fichiers_projet, jars, jour) -> None:
    cle, avant, apres = a["cle"], a["avant"], a["apres"]
    livre = "#" in cle
    absente = cle != CLE_JOURNAL and not livre and cle not in corpus.fr
    du_projet = cle != CLE_JOURNAL and not livre and not absente and corpus.origine_fr.get(cle) == "projet"
    if livre:
        fichier, pointeur = _livre(cle)
        actuel = _lire_pointeur(racine / fichier, pointeur)
        if actuel is None:
            plan.refus.append((i, f"{cle} : pointeur introuvable dans le livre français"))
            return
    else:
        actuel = None if absente else corpus.texte(cle)
    # Une clé définie dans plusieurs fichiers du projet : chaque définition prend le nouveau texte, même quand celle
    # qui s'affiche le porte déjà (point de vigilance 2).
    en_retard = sorted(ns for ns in fichiers_projet.get(cle, ()) if corpus.projet[(ns, cle)] != apres) if du_projet else []
    if actuel == apres and not en_retard:
        plan.deja.append(i)
        return
    if actuel not in (avant, apres):
        plan.refus.append((i, f"{cle} : le texte a changé depuis la proposition (actuel : {actuel!r})"))
        return
    if cle == CLE_JOURNAL:
        plan.journal = apres
    elif livre:
        plan.textes.setdefault(fichier, {})[pointeur] = apres
    elif absente:
        plan.textes.setdefault(LANGUE.format(a["espace"]), {})[cle] = apres
    elif corpus.origine_fr.get(cle) == "vanilla":
        plan.refus.append((i, f"{cle} : texte de Mojang, jamais surchargé (spec 2 §2)"))
        return
    elif du_projet:
        for ns in en_retard:
            plan.textes.setdefault(LANGUE.format(ns), {})[cle] = apres
    else:  # traduction officielle d'un mod : une clé de surcharge
        ns = a.get("espace") or jars.get(cle)
        if not ns:
            plan.refus.append((i, f"{cle} : espace de noms du mod introuvable ; préciser « espace »"))
            return
        plan.textes.setdefault(LANGUE.format(ns), {})[cle] = apres
    plan.traces.append((cle, _entree(plan.lot, "correction", apres, a, jour)))


def _tracer(plan, i, a, config, texte_final, jour) -> None:
    """Une décision qui garde le texte tel quel : elle cite le texte que la clé aura après le lot."""
    if a["fr"] != texte_final(a["cle"]):
        plan.refus.append((i, f"{a['cle']} : la trace doit citer le texte tel qu'il sera ({texte_final(a['cle'])!r})"))
        return
    decisions = config.provenance.get("cles", {}).get(a["cle"], [])
    if decisions and decisions[-1].get("lot") == plan.lot["lot"] and decisions[-1].get("fr") == a["fr"]:
        plan.deja.append(i)
        return
    plan.traces.append((a["cle"], _entree(plan.lot, "decision", a["fr"], a, jour)))


def _excepter(plan, i, a, existantes, texte_final, jour) -> None:
    """Une exception, avec l'empreinte du texte final quand elle n'a pas d'objet (spec 2 §7)."""
    entree = {"controle": a["controle"], "cle": a["cle"]}
    if a.get("objet"):
        entree["objet"] = a["objet"]
    entree.update(motif=a["motif"], date=jour)
    if a.get("question"):
        entree["question"] = a["question"]
    if not a.get("objet"):
        entree["empreinte"] = empreinte(texte_final(a["cle"]) or "")
    ancienne = existantes.get(triplet_exc(entree))
    sans_date = lambda e: {k: v for k, v in e.items() if k != "date"}  # noqa: E731
    if ancienne is not None and sans_date(ancienne) == sans_date(entree):
        plan.deja.append(i)
    else:
        plan.exceptions.append(entree)


def ecrire(plan, racine, espace) -> None:
    """Écrit un plan sans refus : textes du pack, provenance, données du vérificateur."""
    if plan.refus:
        raise ValueError("un plan refusé ne s'écrit pas")
    racine, espace = Path(racine), Path(espace)
    for fichier, valeurs in sorted(plan.textes.items()):
        chemin = racine / fichier
        if fichier.startswith("patchouli_books/"):
            donnees = json.loads(chemin.read_text(encoding="utf-8"))
            for pointeur, valeur in valeurs.items():
                _poser(donnees, pointeur, valeur)
            texte = json.dumps(donnees, ensure_ascii=False, indent=4)
        else:
            donnees = json.loads(chemin.read_text(encoding="utf-8")) if chemin.is_file() else {}
            donnees.update(valeurs)
            texte = json.dumps(donnees, ensure_ascii=False, indent=2, sort_keys=True)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(texte + "\n", encoding="utf-8")
    if plan.journal is not None:
        (racine / FICHIER_JOURNAL).write_text(plan.journal, encoding="utf-8")
    if plan.traces:
        chemin = espace / "provenance.json"
        provenance = json.loads(chemin.read_text(encoding="utf-8"))
        for cle, entree in plan.traces:
            provenance["cles"].setdefault(cle, []).append(entree)
        chemin.write_text(json.dumps(provenance, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if plan.exceptions or plan.retraits or plan.generiques or plan.renvois:
        config = config_mod.charger_config(espace)
        if plan.exceptions or plan.retraits:
            otees = {triplet_exc(e) for e in plan.exceptions} | set(plan.retraits)
            gardees = [e for e in config.exceptions if e.get("epingle") or triplet_exc(e) not in otees]
            config_mod.ecrire(espace, "exceptions", gardees + plan.exceptions)
        if plan.generiques:
            config_mod.ecrire(espace, "mots_generiques", {**config.mots_generiques, **plan.generiques})
        if plan.renvois:
            config_mod.ecrire(espace, "renvois", config.renvois + plan.renvois)
