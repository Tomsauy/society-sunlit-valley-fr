"""Le corpus : ce que le jeu affiche, reconstitué comme il fusionne les langues.

Vanilla, puis les jars extraits, puis kubejs/assets du pack, par namespace et par clé. Le jeu
parcourt les namespaces dans le même ordre pour en_us et fr_fr : quand une clé est définie dans
deux fichiers du pack, le français affiché suit l'anglais qui gagne. Le corpus retient le dernier
namespace dans l'ordre alphabétique et `doublons()` rend ces clés visibles.
"""
from __future__ import annotations

import gzip
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import js, snbt

TEMOINS = ("ko_kr", "zh_cn")
CLE_JOURNAL = "journal"  # clé des constats qui portent sur le journal des modifications
MC_EN, MC_FR, RECONSTITUE = "references/mc_en_us.json", "references/mc_fr_fr.json", "society-corrected-en.json"
# Fichiers de l'espace de travail lus hors instantané : tous requis, car sans eux des contrôles se videraient sans
# bruit (le français de Mojang, l'anglais des objets KubeJS sans anglais).
FICHIERS_REQUIS = (MC_EN, MC_FR, RECONSTITUE)


class CorpusIncomplet(Exception):
    """Une entrée manque ou est illisible ; le message dit laquelle et que faire."""


def affichee(cle: str) -> bool:
    """Faux pour une clé de commentaire (« _comment », « __support_… », « _quark.config… ») : les mods
    marquent ainsi ce que le jeu n'affiche jamais."""
    return not cle.startswith("_")


def lire_json(chemin: Path, defaut=None):
    """Le contenu d'un JSON ; `defaut` (un dict vide par défaut) s'il n'existe pas."""
    try:
        texte = Path(chemin).read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return {} if defaut is None else defaut
    try:
        return json.loads(texte)
    except json.JSONDecodeError as e:
        raise CorpusIncomplet(f"{chemin} : JSON illisible ({e})") from e


@dataclass
class ChampLivre:
    fichier: str
    pointeur: str
    en: str
    fr: str = ""
    objets: tuple = ()

    @property
    def cle(self) -> str:
        return f"{self.fichier}#{self.pointeur}"


@dataclass
class Tache:
    cle_titre: str
    objets: tuple


@dataclass
class Quete:
    identifiant: str
    chapitre: str
    icone: str
    cles: tuple
    taches: tuple


@dataclass
class Corpus:
    en: dict = field(default_factory=dict)
    origine_en: dict = field(default_factory=dict)
    fr_base: dict = field(default_factory=dict)
    origine_base: dict = field(default_factory=dict)
    fr: dict = field(default_factory=dict)
    origine_fr: dict = field(default_factory=dict)
    projet: dict = field(default_factory=dict)
    ns_projet: dict = field(default_factory=dict)
    temoins: dict = field(default_factory=dict)
    reconstitue: dict = field(default_factory=dict)
    livres: list = field(default_factory=list)
    journal_en: str = ""
    journal_fr: str = ""
    quetes: list = field(default_factory=list)
    vendus: set = field(default_factory=set)
    essences: list = field(default_factory=list)
    infobulles: dict = field(default_factory=dict)
    arguments: dict = field(default_factory=dict)
    scripts_amont: dict = field(default_factory=dict)  # None quand git n'a pas pu lire l'amont
    version: str = ""

    def anglais(self, cle: str) -> str:
        """L'anglais affiché ; à défaut, l'anglais reconstitué des objets KubeJS sans anglais."""
        valeur = self.en.get(cle) or ""
        return valeur if valeur.strip() else self.reconstitue.get(cle, "")

    def valeur(self, cle: str) -> str:
        return self.fr.get(cle, "")

    def texte(self, cle: str) -> str:
        """Le français d'une clé de langue, d'un champ de livre (« fichier#pointeur ») ou du journal."""
        if cle == CLE_JOURNAL:
            return self.journal_fr
        if "#" not in cle:
            return self.fr.get(cle, "")
        champ = self.champ(cle)
        return champ.fr if champ else ""

    def champ(self, cle: str):
        """Le champ de livre de clé « <livre>/<fichier>#<pointeur> », ou None si le livre anglais ne l'a pas."""
        return next((champ for champ in self.livres if champ.cle == cle), None)

    def textes_projet(self) -> list:
        """(clé, français) des clés affichées que définit le projet, une fois chacune, triées."""
        return sorted((cle, v) for cle, v in self.fr.items() if self.origine_fr.get(cle) == "projet" and affichee(cle))

    def doublons(self) -> dict:
        """Clé -> {namespace: valeur}, pour les clés affichées définies deux fois avec deux valeurs."""
        par_cle = {}
        for (ns, cle), valeur in self.projet.items():
            if affichee(cle):
                par_cle.setdefault(cle, {})[ns] = valeur
        return {cle: d for cle, d in sorted(par_cle.items()) if len(set(d.values())) > 1}


FORMAT_INSTANTANE = 1


def charger(racine, espace, instantane=None) -> Corpus:
    """Le corpus du pack `racine` ; avec `instantane`, tout sauf notre français vient de ce fichier."""
    racine, espace = Path(racine), Path(espace)
    corpus = Corpus()
    if instantane is not None:
        if _depuis_instantane(corpus, Path(instantane), racine, espace):
            return corpus  # instantané complet : notre français y est aussi
    else:
        _exiger(racine / "kubejs" / "assets", espace / "extracted", espace / "references")
        _anglais_et_bases(corpus, racine, espace)
        for charge in SOURCES_ANNEXES:
            charge(corpus, racine)
        corpus.version = _version(racine)
    _francais_du_projet(corpus, racine)
    for complete in COMPLEMENTS_FRANCAIS:
        complete(corpus, racine)
    return corpus


def _exiger(*chemins: Path) -> None:
    for chemin in chemins:
        if not chemin.exists():
            raise CorpusIncomplet(
                f"{chemin} introuvable. Dans le clone de travail, lancer extract_langs.py et "
                "fetch_vanilla_refs.py ; ailleurs, comme sur le fork, passer --instantane FICHIER.")


def _dossiers_lang(racine: Path) -> list:
    return sorted((racine / "kubejs" / "assets").glob("*/lang"))


def _lire_requis(chemin: Path, nom: str) -> dict:
    if not chemin.is_file():
        raise CorpusIncomplet(f"{nom} introuvable ({chemin}) : ce fichier de l'espace de travail est requis ; "
                              "le régénérer (fetch_vanilla_refs.py pour references/).")
    return lire_json(chemin)


def _anglais_et_bases(corpus: Corpus, racine: Path, espace: Path) -> None:
    for cle, v in _lire_requis(espace / MC_EN, MC_EN).items():
        corpus.en[cle], corpus.origine_en[cle] = v, "vanilla"
    for cle, v in _lire_requis(espace / MC_FR, MC_FR).items():
        corpus.fr_base[cle], corpus.origine_base[cle] = v, "vanilla"
    for jar in sorted(p for p in (espace / "extracted").iterdir() if p.is_dir()):
        for ns in sorted(p for p in jar.iterdir() if p.is_dir()):
            for cle, v in lire_json(ns / "en_us.json").items():
                corpus.en[cle], corpus.origine_en[cle] = v, "jar"
            for cle, v in lire_json(ns / "fr_fr.json").items():
                corpus.fr_base[cle], corpus.origine_base[cle] = v, "jar"
    for dossier in _dossiers_lang(racine):
        ns = dossier.parent.name
        for cle, v in lire_json(dossier / "en_us.json").items():
            corpus.en[cle], corpus.origine_en[cle] = v, "projet"
        for langue in TEMOINS:
            for cle, v in lire_json(dossier / f"{langue}.json").items():
                corpus.temoins.setdefault((ns, cle), {})[langue] = v
    corpus.reconstitue = _lire_requis(espace / RECONSTITUE, RECONSTITUE)


def _francais_du_projet(corpus: Corpus, racine: Path) -> None:
    corpus.fr = dict(corpus.fr_base)
    corpus.origine_fr = dict(corpus.origine_base)
    for dossier in _dossiers_lang(racine):
        ns = dossier.parent.name
        for cle, v in lire_json(dossier / "fr_fr.json").items():
            corpus.fr[cle], corpus.origine_fr[cle] = v, "projet"
            corpus.projet[(ns, cle)] = v
            corpus.ns_projet[cle] = ns


def _version(racine: Path) -> str:
    return str(lire_json(racine / "pakku.json").get("version", ""))


def ecrire_instantane(corpus: Corpus, chemin, complet: bool = False) -> None:
    """Écrit tout ce qui n'est pas notre français — avec `complet`, notre français aussi —, en JSON
    compressé aux octets reproductibles."""
    donnees = {
        "format": FORMAT_INSTANTANE,
        "version": corpus.version,
        "en": corpus.en,
        "origine_en": corpus.origine_en,
        "fr_base": corpus.fr_base,
        "origine_base": corpus.origine_base,
        "temoins": {f"{ns}\t{cle}": v for (ns, cle), v in corpus.temoins.items()},
        "reconstitue": corpus.reconstitue,
        "livres": [{"fichier": c.fichier, "pointeur": c.pointeur, "en": c.en, "objets": list(c.objets)}
                   for c in corpus.livres],
        "journal_en": corpus.journal_en,
        "quetes": [{"identifiant": q.identifiant, "chapitre": q.chapitre, "icone": q.icone,
                    "cles": list(q.cles),
                    "taches": [{"cle_titre": t.cle_titre, "objets": list(t.objets)} for t in q.taches]}
                   for q in corpus.quetes],
        "vendus": sorted(corpus.vendus),
        "essences": corpus.essences,
        "infobulles": {cle: sorted(ids) for cle, ids in corpus.infobulles.items()},
        "arguments": corpus.arguments,
        "scripts_amont": corpus.scripts_amont,
    }
    if complet:
        donnees.update({"complet": True, "fr": corpus.fr, "origine_fr": corpus.origine_fr,
                        "projet": {f"{ns}\t{cle}": v for (ns, cle), v in corpus.projet.items()},
                        "ns_projet": corpus.ns_projet, "journal_fr": corpus.journal_fr})
        for brut, champ in zip(donnees["livres"], corpus.livres):
            brut["fr"] = champ.fr
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    brut = json.dumps(donnees, ensure_ascii=False, sort_keys=True).encode("utf-8")
    with open(chemin, "wb") as f, gzip.GzipFile(filename="", mode="wb", fileobj=f, mtime=0) as gz:
        gz.write(brut)


def _depuis_instantane(corpus: Corpus, chemin: Path, racine: Path, espace: Path) -> bool:
    """Charge l'instantané ; rend True s'il est complet (notre français compris)."""
    try:
        with gzip.open(chemin, "rt", encoding="utf-8") as f:
            d = json.load(f)
    except FileNotFoundError as e:
        raise CorpusIncomplet(f"instantané introuvable : {chemin}") from e
    except (OSError, json.JSONDecodeError) as e:
        raise CorpusIncomplet(f"instantané illisible : {chemin} ({e})") from e
    if d.get("format") != FORMAT_INSTANTANE:
        raise CorpusIncomplet(f"instantané au format {d.get('format')}, attendu {FORMAT_INSTANTANE} : "
                              "le régénérer avec --ecrire-instantane")
    version_du_pack = _version(racine) or _lire_texte(espace / "version-du-pack.txt").strip()
    if version_du_pack and version_du_pack != d["version"] and not d.get("complet"):
        raise CorpusIncomplet(f"instantané de la version {d['version']}, pack en version "
                              f"{version_du_pack} : régénérer l'instantané")
    corpus.version = d["version"]
    corpus.en, corpus.origine_en = d["en"], d["origine_en"]
    corpus.fr_base, corpus.origine_base = d["fr_base"], d["origine_base"]
    corpus.temoins = {tuple(cle.split("\t", 1)): v for cle, v in d["temoins"].items()}
    corpus.reconstitue = d["reconstitue"]
    corpus.livres = [ChampLivre(c["fichier"], c["pointeur"], c["en"], "", tuple(c["objets"]))
                     for c in d["livres"]]
    corpus.journal_en = d["journal_en"]
    corpus.quetes = [Quete(q["identifiant"], q["chapitre"], q["icone"], tuple(q["cles"]),
                           tuple(Tache(t["cle_titre"], tuple(t["objets"])) for t in q["taches"]))
                     for q in d["quetes"]]
    corpus.vendus = set(d["vendus"])
    corpus.essences = list(d["essences"])
    corpus.infobulles = {cle: set(ids) for cle, ids in d["infobulles"].items()}
    corpus.arguments = d["arguments"]
    corpus.scripts_amont = d["scripts_amont"]
    if not d.get("complet"):
        return False
    corpus.fr, corpus.origine_fr, corpus.ns_projet = d["fr"], d["origine_fr"], d["ns_projet"]
    corpus.projet = {tuple(cle.split("\t", 1)): v for cle, v in d["projet"].items()}
    corpus.journal_fr = d["journal_fr"]
    for champ, brut in zip(corpus.livres, d["livres"]):
        champ.fr = brut.get("fr", "")
    return True


ID = re.compile(r"[a-z0-9_.-]+:[a-z0-9_/.-]+")
REF = re.compile(r"\{([a-z0-9_]+(?:\.[A-Za-z0-9_]+)+)\}")
CHAMPS_TEXTE_LIVRE = {"name", "title", "text", "subtitle", "description", "landing_text"}
CHAMPS_OBJET_LIVRE = {"icon", "item", "entity"}
JOURNAL = Path("config") / "fancymenu" / "assets"


def _lire_texte(chemin: Path) -> str:
    try:
        return chemin.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _livres(corpus: Corpus, racine: Path) -> None:
    for dossier_en in sorted((racine / "patchouli_books").glob("*/en_us")):
        livre = dossier_en.parent.name
        for chemin in sorted(dossier_en.rglob("*.json")):
            fichier = f"{livre}/{chemin.relative_to(dossier_en).as_posix()}"
            donnees = lire_json(chemin)
            objets = tuple(sorted(set(_objets_livre(donnees))))
            for pointeur, texte in _champs_livre(donnees):
                corpus.livres.append(ChampLivre(fichier, pointeur, texte, "", objets))


def _champs_livre(objet, pointeur=""):
    if isinstance(objet, dict):
        for cle, valeur in objet.items():
            if cle in CHAMPS_TEXTE_LIVRE and isinstance(valeur, str):
                yield f"{pointeur}/{cle}", valeur
            else:
                yield from _champs_livre(valeur, f"{pointeur}/{cle}")
    elif isinstance(objet, list):
        for i, valeur in enumerate(objet):
            yield from _champs_livre(valeur, f"{pointeur}/{i}")


def _objets_livre(objet):
    if isinstance(objet, dict):
        for cle, valeur in objet.items():
            if cle in CHAMPS_OBJET_LIVRE and isinstance(valeur, str):
                for morceau in valeur.split(","):
                    m = ID.match(morceau.strip())
                    if m:
                        yield m.group(0)
            else:
                yield from _objets_livre(valeur)
    elif isinstance(objet, list):
        for valeur in objet:
            yield from _objets_livre(valeur)


def _francais_des_livres(corpus: Corpus, racine: Path) -> None:
    fichiers = {}
    for champ in corpus.livres:
        if champ.fichier not in fichiers:
            livre, reste = champ.fichier.split("/", 1)
            fichiers[champ.fichier] = lire_json(racine / "patchouli_books" / livre / "fr_fr" / reste)
        champ.fr = _suivre(fichiers[champ.fichier], champ.pointeur)


def _suivre(objet, pointeur: str) -> str:
    for morceau in pointeur.strip("/").split("/"):
        if isinstance(objet, list) and morceau.isdigit() and int(morceau) < len(objet):
            objet = objet[int(morceau)]
        elif isinstance(objet, dict) and morceau in objet:
            objet = objet[morceau]
        else:
            return ""
    return objet if isinstance(objet, str) else ""


def _journal(corpus: Corpus, racine: Path) -> None:
    corpus.journal_en = _lire_texte(racine / JOURNAL / "changelog_en_us.markdown")


def _francais_du_journal(corpus: Corpus, racine: Path) -> None:
    chemin = racine / JOURNAL / "changelog_fr_fr.markdown"
    if corpus.journal_en and not chemin.is_file():
        raise CorpusIncomplet(f"{chemin} introuvable : le changelog anglais existe, notre traduction doit "
                              "exister aussi.")
    corpus.journal_fr = _lire_texte(chemin)


def _quetes(corpus: Corpus, racine: Path) -> None:
    for chemin in sorted((racine / "config" / "ftbquests" / "quests" / "chapters").glob("*.snbt")):
        try:
            donnees = snbt.lire(chemin.read_text(encoding="utf-8"))
        except snbt.ErreurSNBT as e:
            raise CorpusIncomplet(f"{chemin} : SNBT illisible ({e})") from e
        quetes = donnees.get("quests", []) if isinstance(donnees, dict) else []
        for q in quetes:
            if not isinstance(q, dict):
                continue
            taches = tuple(
                Tache(_premiere_ref(t.get("title", "")),
                      tuple(_ids_objets([t.get(k) for k in ("item", "entity", "icon")])))
                for t in q.get("tasks", []) if isinstance(t, dict))
            icone = next(iter(_ids_objets([q.get("icon")])), "")
            corpus.quetes.append(Quete(str(q.get("id", "")).lstrip("0"), chemin.stem, icone,
                                       tuple(sorted(set(_refs(q)))), taches))


def _refs(objet):
    if isinstance(objet, str):
        yield from REF.findall(objet)
    elif isinstance(objet, dict):
        for valeur in objet.values():
            yield from _refs(valeur)
    elif isinstance(objet, list):
        for valeur in objet:
            yield from _refs(valeur)


def _premiere_ref(texte) -> str:
    m = REF.search(texte) if isinstance(texte, str) else None
    return m.group(1) if m else ""


def _ids_objets(valeur) -> list:
    if isinstance(valeur, str):
        return [valeur] if ID.fullmatch(valeur) else []
    if isinstance(valeur, dict):
        ident = valeur.get("id")
        ids = [ident] if isinstance(ident, str) and ID.fullmatch(ident) else []
        for cle, sous in valeur.items():
            if cle != "id":
                ids += _ids_objets(sous)
        return ids
    if isinstance(valeur, list):
        return [i for sous in valeur for i in _ids_objets(sous)]
    return []


def _vendus(corpus: Corpus, racine: Path) -> None:
    for chemin in sorted((racine / "kubejs" / "data" / "society_trading" / "shops").glob("*.json")):
        for echange in lire_json(chemin).get("trades", []):
            offre = echange.get("offer") if isinstance(echange, dict) else None
            if isinstance(offre, dict) and isinstance(offre.get("item"), str) and "nbt" not in offre:
                corpus.vendus.add(offre["item"])


def _essences(corpus: Corpus, racine: Path) -> None:
    chemin = racine / "config" / "everycomp-entries.toml"
    if not chemin.is_file():
        if any(cle.startswith(("wood_type.", "leaves_type.")) for cle in corpus.en):
            raise CorpusIncomplet(f"{chemin} introuvable : le corpus contient des clés wood_type./leaves_type. "
                                  "(Every Compat est présent), ce fichier est donc requis.")
        return
    texte = _lire_texte(chemin)
    section = None
    for ligne in texte.split("[entries]")[0].splitlines():
        if ligne.strip().startswith("["):
            m = re.match(r"\s*\[types\.(\w+)\.(\w+)\]", ligne)
            section = f"{m.group(1)}.{m.group(2)}" if m else None
            continue
        m = re.match(r"\s*(\w+)\s*=\s*true\b", ligne)
        if m and section:
            corpus.essences.append(f"{section}.{m.group(1)}")


def _scripts(corpus: Corpus, racine: Path) -> None:
    sources = js.lire_scripts(racine)
    corpus.infobulles = js.infobulles(sources)
    corpus.arguments = js.arguments_gabarits(sources)
    corpus.scripts_amont = js.blobs_amont(racine)


# Chargeurs des autres sources : côté anglais et structure, puis côté français (seul ce dernier
# tourne quand le reste vient d'un instantané).
SOURCES_ANNEXES = (_livres, _journal, _quetes, _vendus, _essences, _scripts)
COMPLEMENTS_FRANCAIS = (_francais_des_livres, _francais_du_journal)
