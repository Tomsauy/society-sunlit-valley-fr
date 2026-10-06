"""Les données de cohérence (fr-workspace/coherence/), le vocabulaire et les décisions tracées.

Chaque fichier lu est requis : un fichier absent viderait son contrôle sans bruit, et le rapport inviterait
alors à retirer de la dette des constats qu'il ne cherche plus. Une valeur vide s'écrit explicitement."""
from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

DEFAUTS = {
    "exceptions": [],
    "dette": [],
    "familles": {"familles": [], "accords": {}},
    "gabarits": {},
    "largeurs": [],
    "scripts_patches": {},
    "mots_generiques": {},
    "mods_retires": {},
    "formes_interdites": [],
    "noms_propres": {},
    "majuscules": {},
    "termes_imposes": [],
    "regles": {"casse_textes": False, "pourcentages": "", "nombres": False, "largeurs_mods": False,
               "terminologie_interdits": False},
    "double_sens": [],
    "homographes": {},
    "renvois": [],
}
VOCABULAIRE, PROVENANCE, GARDER_ANGLAIS = "accents/vocabulaire.json", "provenance.json", "KEEP-ENGLISH.md"
# Chemins, relatifs à l'espace de travail, des fichiers que lit charger_config : tous requis.
FICHIERS_REQUIS = tuple(f"coherence/{nom}.json" for nom in DEFAUTS) + (VOCABULAIRE, PROVENANCE, GARDER_ANGLAIS)
# Valeur que prend une règle en attente de décision quand les tests les activent toutes.
ACTIVATION_DE_TEST = {"casse_textes": True, "pourcentages": "espace", "nombres": True, "largeurs_mods": True,
                      "terminologie_interdits": True}
TERME_GARDE = re.compile(r"^\|\s*\*\*(.+?)\*\*\s*\|", re.M)


class ConfigInvalide(Exception):
    pass


@dataclass
class Config:
    espace: Path
    exceptions: list = field(default_factory=list)
    dette: list = field(default_factory=list)
    familles: dict = field(default_factory=lambda: copy.deepcopy(DEFAUTS["familles"]))
    gabarits: dict = field(default_factory=dict)
    largeurs: list = field(default_factory=list)
    scripts_patches: dict = field(default_factory=dict)
    mots_generiques: dict = field(default_factory=dict)
    mods_retires: dict = field(default_factory=dict)
    formes_interdites: list = field(default_factory=list)
    noms_propres: dict = field(default_factory=dict)
    majuscules: dict = field(default_factory=dict)  # lu par casse seul (STYLE §2)
    termes_imposes: list = field(default_factory=list)
    regles: dict = field(default_factory=lambda: dict(DEFAUTS["regles"]))
    double_sens: list = field(default_factory=list)
    homographes: dict = field(default_factory=dict)
    renvois: list = field(default_factory=list)
    vocabulaire: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=lambda: {"cles": {}})
    garder_anglais: set = field(default_factory=set)

    def glossaire(self) -> list:
        """Les termes du glossaire de provenance.json : {en, fr, garde_anglais, origine, raison}."""
        glossaire = self.provenance.get("glossaire", [])
        return glossaire if isinstance(glossaire, list) else []

    def termes_gardes(self) -> list:
        """Les termes écrits tels quels à dessein : noms_propres.json, KEEP-ENGLISH, termes que le glossaire garde en
        anglais. Chaque contrôle qui les exempte (casse, anglais_residuel) y applique sa propre normalisation."""
        return (list(self.noms_propres) + list(self.garder_anglais)
                + [e.get("en", "") for e in self.glossaire() if e.get("garde_anglais")])

    def regle(self, nom: str, options):
        """La valeur d'une règle en attente de décision ; `options.toutes_regles` l'active."""
        valeur = self.regles.get(nom)
        if options.toutes_regles and not valeur:
            return ACTIVATION_DE_TEST[nom]
        return valeur


def _texte(chemin: Path) -> str:
    try:
        return chemin.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise ConfigInvalide(f"{chemin} introuvable : chaque fichier de données est requis — l'écrire, au besoin "
                             "avec sa valeur vide (fr-workspace/coherence/LISEZMOI.md)") from e


def _lire(chemin: Path):
    texte = _texte(chemin)
    try:
        return json.loads(texte)
    except json.JSONDecodeError as e:
        raise ConfigInvalide(f"{chemin} : JSON illisible ({e})") from e


def charger_config(espace) -> Config:
    espace = Path(espace)
    donnees = {}
    for nom in DEFAUTS:
        chemin = espace / "coherence" / f"{nom}.json"
        donnees[nom] = _lire(chemin)
        VALIDER[nom](chemin, donnees[nom])
    vocabulaire, provenance = _lire(espace / VOCABULAIRE), _lire(espace / PROVENANCE)
    _exiger(isinstance(vocabulaire, dict), espace / VOCABULAIRE, "un objet est attendu")
    _exiger(isinstance(provenance, dict) and isinstance(provenance.get("cles"), dict), espace / PROVENANCE,
            "un objet avec un objet « cles » est attendu")
    garder = _texte(espace / GARDER_ANGLAIS)
    return Config(
        espace=espace,
        vocabulaire=vocabulaire,
        provenance=provenance,
        garder_anglais={terme.strip() for terme in TERME_GARDE.findall(garder)},
        **donnees,
    )


# Forme et valeurs de chaque fichier, vérifiées au chargement : un JSON valide mais mal formé (« dette.json » réduit à
# ["x"], un terme imposé sans « francais », « pourcentages » à « espaces ») arrête le vérificateur en nommant le
# fichier, au lieu d'une trace de pile ou d'une règle activée à rebours.
TYPES_ARGUMENT = ("nom_objet", "saison", "autre")
POURCENTAGES = ("", "espace", "colle")
PORTEES = ("tout", "noms", "textes")


def _exiger(condition, chemin, probleme) -> None:
    if not condition:
        raise ConfigInvalide(f"{chemin} : {probleme}")


def _chaine(v) -> bool:
    return isinstance(v, str)


def _chaines(v) -> bool:
    return isinstance(v, list) and all(isinstance(x, str) for x in v)


def _objet(v) -> bool:
    """L'objet d'une exception ou d'une entrée de dette : une clé, ou la liste des clés d'un groupe d'homonymes."""
    return isinstance(v, str) or _chaines(v)


def _regex(v) -> bool:
    try:
        re.compile(v)
    except (re.error, TypeError):
        return False
    return isinstance(v, str)


def _booleen(v) -> bool:
    return isinstance(v, bool)


def _entier(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _enregistrements(chemin, donnees, requis=(), facultatifs=()):
    """Une liste d'objets : chaque champ requis est une chaîne non vide, chaque champ facultatif présent passe son test."""
    _exiger(isinstance(donnees, list), chemin, "une liste est attendue")
    for i, e in enumerate(donnees):
        _exiger(isinstance(e, dict), chemin, f"entrée {i} : un objet est attendu")
        for champ in requis:
            _exiger(isinstance(e.get(champ), str) and e[champ].strip(), chemin,
                    f"entrée {i} : « {champ} » manque ou n'est pas une chaîne")
        for champ, test, attendu in facultatifs:
            _exiger(champ not in e or test(e[champ]), chemin, f"entrée {i} : « {champ} » doit être {attendu}")


def _motifs(chemin, donnees):
    """Un objet {mot ou clé : motif}."""
    _exiger(isinstance(donnees, dict), chemin, "un objet {terme : motif} est attendu")
    for cle, motif in donnees.items():
        _exiger(isinstance(motif, str), chemin, f"« {cle} » : le motif doit être une chaîne")


def _exceptions(chemin, donnees):
    _enregistrements(chemin, donnees, ("controle", "cle"), (
        ("objet", _objet, "une clé ou une liste de clés"), ("motif", _chaine, "une chaîne"),
        ("epingle", _booleen, "true ou false"), ("date", _chaine, "une chaîne"),
        ("empreinte", _chaine, "une chaîne"), ("question", _chaine, "une chaîne")))


def _dette(chemin, donnees):
    _enregistrements(chemin, donnees, ("controle", "cle", "empreinte"), (
        ("objet", _objet, "une clé ou une liste de clés"), ("en_attente_de_decision", _booleen, "true ou false")))


def _familles(chemin, donnees):
    _exiger(isinstance(donnees, dict) and isinstance(donnees.get("familles"), list)
            and isinstance(donnees.get("accords"), dict), chemin, "un objet {familles : [...], accords : {...}} est attendu")
    _enregistrements(chemin, donnees["familles"], ("nom", "motif", "gabarit"), (
        ("source", _chaines, "une liste de clés"), ("anglais", _chaine, "une chaîne"),
        ("cles_source", lambda v: isinstance(v, dict), "un objet"), ("noms_source", lambda v: isinstance(v, dict), "un objet")))
    for cle, accord in donnees["accords"].items():
        _exiger(isinstance(accord, dict), chemin, f"accord de {cle} : un objet est attendu")
        _exiger(accord.get("genre", "m") in ("m", "f") and accord.get("nombre", "s") in ("s", "p"), chemin,
                f"accord de {cle} : genre « m » ou « f », nombre « s » ou « p »")


def _gabarits(chemin, donnees):
    _exiger(isinstance(donnees, dict), chemin, "un objet {clé : types des arguments} est attendu")
    for cle, positions in donnees.items():
        _exiger(isinstance(positions, list) and all(isinstance(p, list) and p and all(t in TYPES_ARGUMENT for t in p)
                                                    for p in positions), chemin,
                f"« {cle} » : une liste, par argument, de types parmi {', '.join(TYPES_ARGUMENT)}")


def contrainte_de_mod(entree) -> bool:
    """Une entrée de largeurs.json venue de l'inventaire des mods (elle porte sa preuve) : son « motif » est une
    expression sur la clé, et elle n'est lue que sous la règle largeurs_mods. Sans preuve, c'est l'ancienne entrée
    manuelle {cle, limite, motif}, dont le motif est la justification, toujours active."""
    return "preuve" in entree


def _largeurs(chemin, donnees):
    _enregistrements(chemin, donnees)
    for i, e in enumerate(donnees):
        _exiger(_entier(e.get("limite")) and e["limite"] > 0, chemin, f"entrée {i} : « limite » : un entier de pixels")
        requis = ("comportement", "mod", "preuve") if contrainte_de_mod(e) else ("cle", "motif")
        for champ in requis:
            _exiger(isinstance(e.get(champ), str) and e[champ].strip(), chemin,
                    f"entrée {i} : « {champ} » manque ou n'est pas une chaîne")
        if not contrainte_de_mod(e):
            continue
        for champ, test, attendu in (("cle", _chaine, "une chaîne"), ("cles", _chaines, "une liste de clés"),
                                     ("motif", _regex, "une expression régulière valide"),
                                     ("lignes", lambda v: _entier(v) and v > 0, "un entier positif")):
            _exiger(champ not in e or test(e[champ]), chemin, f"entrée {i} : « {champ} » doit être {attendu}")
        _exiger(e.get("cle") or e.get("cles") or e.get("motif"), chemin,
                f"entrée {i} : « cle », « cles » ou « motif » est requis")


def _scripts_patches(chemin, donnees):
    _exiger(isinstance(donnees, dict), chemin, "un objet {chemin : {base, motif}} est attendu")
    for script, entree in donnees.items():
        _exiger(isinstance(entree, dict) and isinstance(entree.get("base"), str) and entree["base"].strip(), chemin,
                f"« {script} » : « base » (sha du blob amont patché) manque")


def _formes_interdites(chemin, donnees):
    _enregistrements(chemin, donnees, ("forme", "juste"), (("casse", _booleen, "true ou false"),
                                                           ("source", _chaine, "une chaîne")))


def _termes_imposes(chemin, donnees):
    _enregistrements(chemin, donnees, ("anglais",), (
        ("francais", lambda v: isinstance(v, str) and v.strip() or (_chaines(v) and v), "une forme ou une liste de formes"),
        ("portee", lambda v: v in PORTEES, f"l'une de {', '.join(PORTEES)}"), ("cles", _regex, "une expression régulière"),
        ("interdits", _chaines, "une liste de formes"), ("motif", _chaine, "une chaîne")))
    for i, e in enumerate(donnees):
        _exiger("francais" in e, chemin, f"entrée {i} : « francais » manque")
        _exiger(_regex(e["anglais"]), chemin, f"entrée {i} : « anglais » n'est pas une expression régulière valide")


def _regles(chemin, donnees):
    _exiger(isinstance(donnees, dict) and set(donnees) == set(DEFAUTS["regles"]), chemin,
            f"un objet avec exactement {', '.join(DEFAUTS['regles'])} est attendu")
    _exiger(_booleen(donnees["casse_textes"]), chemin, "« casse_textes » : true ou false")
    _exiger(_booleen(donnees["nombres"]), chemin, "« nombres » : true ou false")
    _exiger(_booleen(donnees["largeurs_mods"]), chemin, "« largeurs_mods » : true ou false")
    _exiger(_booleen(donnees["terminologie_interdits"]), chemin, "« terminologie_interdits » : true ou false")
    _exiger(donnees["pourcentages"] in POURCENTAGES, chemin,
            "« pourcentages » : \"\" (règle en attente), \"espace\" ou \"colle\"")


def _double_sens(chemin, donnees):
    _enregistrements(chemin, donnees, ("anglais", "motif"), (("justes", lambda v: _chaines(v) and v, "une liste de formes"),))
    for i, e in enumerate(donnees):
        _exiger(_regex(e["anglais"]) and "justes" in e, chemin,
                f"entrée {i} : « anglais » (expression régulière valide) et « justes » sont requis")


def _renvois(chemin, donnees):
    """Les entrées de dette renvoyées au sous-projet 3 (spec 2 §12) : {controle, cle, objet?, motif}."""
    _enregistrements(chemin, donnees, ("controle", "cle", "motif"), (("objet", _objet, "une clé ou une liste de clés"),))


VALIDER = {"exceptions": _exceptions, "dette": _dette, "familles": _familles, "gabarits": _gabarits,
           "largeurs": _largeurs, "scripts_patches": _scripts_patches, "mots_generiques": _motifs,
           "mods_retires": _motifs, "formes_interdites": _formes_interdites, "noms_propres": _motifs,
           "majuscules": _motifs, "termes_imposes": _termes_imposes, "regles": _regles, "double_sens": _double_sens,
           "homographes": _motifs, "renvois": _renvois}


def lire_dette(chemin) -> list:
    """Une dette de référence (--dette-base) : lue et vérifiée comme dette.json."""
    chemin = Path(chemin)
    donnees = _lire(chemin)
    _dette(chemin, donnees)
    return donnees


def ecrire(espace, nom: str, donnees) -> None:
    """Réécrit fr-workspace/coherence/<nom>.json : indentation 1, UTF-8 lisible, saut de ligne final."""
    chemin = Path(espace) / "coherence" / f"{nom}.json"
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(donnees, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
