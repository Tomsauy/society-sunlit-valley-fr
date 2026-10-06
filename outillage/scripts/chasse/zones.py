"""Les zones de la chasse (spec 3 §4, phase 2) : le pack découpé en zones d'au plus ~1 500 textes, qui ne coupent
pas une famille de noms et couvrent chaque texte exactement une fois.

Construction, en trois temps :
1. Chaque texte a une unité (textes.unite_de). Une unité plus grande que le plafond se coupe en sous-unités : les
   noms (`item.<ns>.…`, `block.<ns>.…`, toute clé du registre des noms) restent ensemble, le reste se range par ses
   deux premiers segments (`create.ponder`, `tag.item`…).
2. Les membres d'une même famille de familles.json restent ensemble : leurs unités ne font qu'un bloc (union-find).
   Un bloc est indivisible ; plus grand que le plafond, il fait une zone à lui seul, marquée `"indivisible": true`.
3. Les blocs se rangent par thème (themes.json : {thème : [espaces]}, « divers » à défaut). Un espace de noms d'au
   moins GROS textes forme ses propres zones ; les autres blocs d'un même thème se rangent, du plus grand au plus
   petit, dans la première zone du thème où ils tiennent."""
from __future__ import annotations

from coherence.registre import CLE_OBJET

PLAFOND = 1500
GROS = 750          # un mod d'au moins 750 textes a sa ou ses zones à lui (« les gros mods seuls »)
TOLERANCE = 100     # un bloc d'au plus 100 textes qui ne tient nulle part rejoint la plus petite zone de son groupe,
                    # tant qu'elle ne dépasse pas plafond + TOLERANCE (ou qu'elle est indivisible)
DIVERS = "divers"


class ZonesInvalides(Exception):
    pass


def sous_unite(cle: str, unite: str) -> str:
    """La sous-unité d'une clé d'une unité trop grande : « <unité>/noms » pour un nom d'objet, sinon les deux premiers
    segments de la clé."""
    if CLE_OBJET.match(cle):
        return f"{unite}/noms"
    return f"{unite}/" + ".".join(cle.split(".")[:2])


class _Ensembles:
    def __init__(self):
        self.parent = {}

    def trouver(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def unir(self, a, b):
        ra, rb = self.trouver(a), self.trouver(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def blocs(textes, liens=(), plafond=PLAFOND) -> dict:
    """{bloc : [ids des textes]} : unités, coupées si trop grandes, puis réunies par les liens de familles
    (paires de clés d'une même famille)."""
    par_unite = {}
    for t in textes:
        par_unite.setdefault(t.unite, []).append(t)
    unite_fine = {}
    for unite, liste in par_unite.items():
        for t in liste:
            unite_fine[t.id] = sous_unite(t.id, unite) if len(liste) > plafond else unite
    ens = _Ensembles()
    for u in unite_fine.values():
        ens.trouver(u)
    for a, b in liens:
        if a in unite_fine and b in unite_fine:
            ens.unir(unite_fine[a], unite_fine[b])
    resultat = {}
    for t in textes:
        resultat.setdefault(ens.trouver(unite_fine[t.id]), []).append(t.id)
    return {b: sorted(ids) for b, ids in sorted(resultat.items())}


def theme_de(bloc: str, themes: dict) -> str:
    """Le thème d'un bloc : celui de son espace de noms (avant « / »), « quetes », « livres », ou « divers »."""
    racine = bloc.split("/", 1)[0]
    if racine.startswith("quetes:"):
        return "quetes"
    if racine.startswith("livre:") or racine == "journal":
        return "livres"
    for theme, espaces in themes.items():
        if racine in espaces:
            return theme
    return DIVERS


def construire(textes, liens, themes, plafond=PLAFOND, gros=GROS, tolerance=TOLERANCE) -> list:
    """Les zones, dans leur ordre de passage : [{id, theme, blocs, textes, indivisible}]."""
    tous = blocs(textes, liens, plafond)
    taille_espace = {}
    for b, ids in tous.items():
        racine = b.split("/", 1)[0]
        taille_espace[racine] = taille_espace.get(racine, 0) + len(ids)
    groupes = {}  # nom du groupe -> blocs ; un gros espace est son propre groupe
    for b in tous:
        racine = b.split("/", 1)[0]
        nom = racine if taille_espace[racine] >= gros and ":" not in racine else theme_de(b, themes)
        groupes.setdefault(nom, []).append(b)
    zones = []
    for nom in sorted(groupes):
        du_groupe = []
        # Premier rangement décroissant : chaque bloc, du plus grand au plus petit, va dans la première zone du groupe
        # où il tient ; un petit bloc qui ne tient nulle part rejoint la plus petite zone du groupe (« environ 1 500 »),
        # plutôt que de faire une zone de quelques textes ; un bloc plus grand que le plafond ouvre sa propre zone.
        for b in sorted(groupes[nom], key=lambda b: (-len(tous[b]), b)):
            n = len(tous[b])
            zone = next((z for z in du_groupe if len(z["textes"]) + n <= plafond), None)
            if zone is None and n <= tolerance and du_groupe:
                petite = min(du_groupe, key=lambda z: len(z["textes"]))
                zone = petite if petite["indivisible"] or len(petite["textes"]) + n <= plafond + tolerance else None
            if zone is None:
                zone = {"id": "", "theme": nom, "blocs": [], "textes": [], "indivisible": n > plafond}
                du_groupe.append(zone)
            zone["blocs"].append(b)
            zone["textes"].extend(tous[b])
        zones += du_groupe
    compte = {}
    for z in zones:
        compte[z["theme"]] = compte.get(z["theme"], 0) + 1
    rang = {}
    for z in zones:
        rang[z["theme"]] = rang.get(z["theme"], 0) + 1
        z["id"] = z["theme"] if compte[z["theme"]] == 1 else f"{z['theme']}-{rang[z['theme']]}"
        z["id"] = z["id"].replace(":", "-").replace("_", "-")
        z["textes"] = sorted(z["textes"])
    return zones


def verifier_couverture(zones, ids, plafond=PLAFOND, tolerance=TOLERANCE) -> list:
    """Les problèmes d'une liste de zones face aux ids de l'inventaire : texte absent, texte dans deux zones, id
    inconnu, zone vide, zone de plus de plafond + tolérance textes sans bloc indivisible, identifiant de zone en
    double. Vide si tout va bien."""
    problemes, vus = [], {}
    ids = set(ids)
    noms = [z["id"] for z in zones]
    for nom in sorted({n for n in noms if noms.count(n) > 1}):
        problemes.append(f"zone {nom} : identifiant en double")
    for z in zones:
        if not z["textes"]:
            problemes.append(f"zone {z['id']} : vide")
        if len(z["textes"]) > plafond + tolerance and not z.get("indivisible"):
            problemes.append(f"zone {z['id']} : {len(z['textes'])} textes, plus que {plafond + tolerance}, "
                             "sans bloc indivisible")
        for t in z["textes"]:
            if t in vus:
                problemes.append(f"{t} : dans les zones {vus[t]} et {z['id']}")
            else:
                vus[t] = z["id"]
    for t in sorted(set(vus) - ids):
        problemes.append(f"{t} : dans la zone {vus[t]}, absent de l'inventaire")
    for t in sorted(ids - set(vus)):
        problemes.append(f"{t} : dans aucune zone")
    return problemes


def liens_de_familles(familles_obj) -> list:
    """(premier membre, autre membre) pour chaque famille de familles.json : les membres d'une même famille restent
    dans une même zone. La source d'une famille (le poisson des « Oeufs de … ») n'est pas liée : elle appartient à son
    propre mod, et le contrôle `familles` tient déjà l'accord entre le membre et sa source.
    `familles_obj` : coherence.regles_derivees.Familles(corpus, config)."""
    par_famille = {}
    for cle, (famille, _) in sorted(familles_obj.membres.items()):
        par_famille.setdefault(famille["nom"], []).append(cle)
    return [(membres[0], autre) for _, membres in sorted(par_famille.items()) for autre in membres[1:]]


def completer(zones: list, textes: list, liens, themes: dict) -> tuple:
    """Zones figées face à un inventaire qui a changé (nouvelle version du pack) : les ids disparus sortent, chaque
    nouveau texte rejoint la zone d'un membre de sa famille, sinon celle d'un texte de même unité, sinon la plus petite
    zone de son thème, sinon une zone nouvelle à son thème. Rend (zones, {ajoutes : {id : zone}, retires : [ids]})."""
    par_id = {t.id: t for t in textes}
    retires = sorted(i for z in zones for i in z["textes"] if i not in par_id)
    zones = [dict(z, textes=[i for i in z["textes"] if i in par_id]) for z in zones]
    zone_de = {i: z for z in zones for i in z["textes"]}
    unite_zone = {par_id[i].unite: z for i, z in zone_de.items()}
    voisins = {}
    for a, b in liens:
        voisins.setdefault(a, []).append(b)
        voisins.setdefault(b, []).append(a)
    ajoutes = {}
    for t in sorted(textes, key=lambda t: t.id):
        if t.id in zone_de:
            continue
        theme = theme_de(t.unite, themes)
        zone = (next((zone_de[v] for v in voisins.get(t.id, ()) if v in zone_de), None) or unite_zone.get(t.unite)
                or min((z for z in zones if z.get("theme") == theme), key=lambda z: len(z["textes"]), default=None))
        if zone is None:
            pris = {z["id"] for z in zones}
            nom = next(n for n in [theme] + [f"{theme}-{k}" for k in range(2, 1000)] if n not in pris)
            zone = {"id": nom, "theme": theme, "blocs": [t.unite], "textes": [], "indivisible": False}
            zones.append(zone)
        zone["textes"] = sorted(zone["textes"] + [t.id])
        zone_de[t.id], unite_zone[t.unite] = zone, zone
        ajoutes[t.id] = zone["id"]
    return zones, {"ajoutes": ajoutes, "retires": retires}
