"""Ce que disent les scripts KubeJS : quel objet affiche quelle infobulle, ce que reçoit chaque %s."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ID = re.compile(r"[a-z0-9_.-]+:[a-z0-9_/.-]+")
CHAINE = re.compile(r"""(["'`])((?:\\.|(?!\1).)*)\1""", re.S)
CLE_TRADUITE = re.compile(r"""Text\.translatable\(\s*(["'`])([A-Za-z0-9_.\-]+)\1""")
APPELS_INFOBULLE = ("tooltip.add", "tooltip.addAdvanced", "ajouterLignes")
PREFIXES_NOM = ("item.", "block.", "entity.", "fluid.", "effect.", "enchantment.", "biome.")


def sans_commentaires(source: str) -> str:
    """Le source sans commentaires // ni /* */ ; les chaînes sont respectées."""
    sortie, i, n = [], 0, len(source)
    while i < n:
        if source[i] in "\"'`":
            j = _fin_chaine(source, i)
            sortie.append(source[i:j])
            i = j
        elif source.startswith("//", i):
            j = source.find("\n", i)
            i = n if j == -1 else j
        elif source.startswith("/*", i):
            j = source.find("*/", i + 2)
            i = n if j == -1 else j + 2
        else:
            sortie.append(source[i])
            i += 1
    return "".join(sortie)


def _fin_chaine(s: str, i: int) -> int:
    """L'indice qui suit la chaîne ouverte en i."""
    fin, i = s[i], i + 1
    while i < len(s):
        if s[i] == "\\":
            i += 2
        elif s[i] == fin:
            return i + 1
        else:
            i += 1
    return len(s)


def _fermante(s: str, i: int):
    profondeur = 1
    while i < len(s):
        if s[i] in "\"'`":
            i = _fin_chaine(s, i)
            continue
        if s[i] in "([{":
            profondeur += 1
        elif s[i] in ")]}":
            profondeur -= 1
            if profondeur == 0:
                return i
        i += 1
    return None


def appels(source: str, nom: str) -> list:
    """Le texte entre parenthèses de chaque appel `nom(…)`, appels imbriqués compris."""
    resultats, motif = [], nom + "("
    i = source.find(motif)
    while i != -1:
        debut = i + len(motif)
        fin = _fermante(source, debut)
        if fin is not None:
            resultats.append(source[debut:fin])
        i = source.find(motif, debut)
    return resultats


def arguments(texte: str) -> list:
    """Les arguments d'un appel, coupés aux virgules de premier niveau."""
    parties, profondeur, debut, i = [], 0, 0, 0
    while i < len(texte):
        c = texte[i]
        if c in "\"'`":
            i = _fin_chaine(texte, i)
            continue
        if c in "([{":
            profondeur += 1
        elif c in ")]}":
            profondeur -= 1
        elif c == "," and profondeur == 0:
            parties.append(texte[debut:i].strip())
            debut = i + 1
        i += 1
    if texte[debut:].strip():
        parties.append(texte[debut:].strip())
    return parties


def infobulles(sources) -> dict:
    """Clé de texte -> identifiants des objets dont l'infobulle affiche ce texte."""
    resultat = {}
    for source in sources:
        for nom in APPELS_INFOBULLE:
            for appel in appels(source, nom):
                parties = arguments(appel)
                if len(parties) < 2:
                    continue
                ids = [m.group(2) for m in CHAINE.finditer(parties[0]) if ID.fullmatch(m.group(2))]
                if not ids:
                    continue
                for m in CLE_TRADUITE.finditer(",".join(parties[1:])):
                    if not m.group(2).startswith(PREFIXES_NOM):
                        resultat.setdefault(m.group(2), set()).update(ids)
    return resultat


def type_argument(argument: str) -> str:
    m = CLE_TRADUITE.match(argument.strip())
    if m:
        if m.group(2).startswith(PREFIXES_NOM):
            return "nom_objet"
        return "saison" if m.group(2).startswith("desc.sereneseasons.") else "autre"
    if re.search(r"getHoverName|getDisplayName|getDescriptionId|displayName", argument):
        return "nom_objet"
    return "autre"


def arguments_gabarits(sources) -> dict:
    """Clé -> types des arguments par position, d'après les appels Text.translatable(clé, …)."""
    resultat = {}
    for source in sources:
        for appel in appels(source, "Text.translatable"):
            parties = arguments(appel)
            m = CHAINE.fullmatch(parties[0]) if parties else None
            if not m or len(parties) < 2:
                continue
            positions = resultat.setdefault(m.group(2), [])
            for rang, argument in enumerate(parties[1:]):
                while len(positions) <= rang:
                    positions.append(set())
                positions[rang].add(type_argument(argument))
    return {cle: [sorted(p) for p in positions] for cle, positions in sorted(resultat.items())}


def lire_scripts(racine: Path) -> list:
    return [sans_commentaires(p.read_text(encoding="utf-8", errors="replace"))
            for p in sorted((Path(racine) / "kubejs").rglob("*.js"))]


def blobs_amont(racine: Path):
    """Chemin -> sha du blob de chaque script KubeJS dans origin/master ; None si git échoue (hors d'un clone, sans
    origin/master) : un amont illisible ne doit pas passer pour un amont sans script."""
    try:
        sortie = subprocess.run(["git", "-C", str(racine), "ls-tree", "-r", "origin/master", "--", "kubejs"],
                                capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    blobs = {}
    for ligne in sortie.splitlines():
        meta, _, chemin = ligne.partition("\t")
        if chemin.endswith(".js"):
            blobs[chemin] = meta.split()[2]
    return blobs
