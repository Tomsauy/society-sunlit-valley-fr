#!/usr/bin/env python3
"""La chasse au reste (spec 3) : zones, tirages, paquets des agents, verdicts, lots, mesure, avancement.

    python3 fr-workspace/scripts/chasser.py zones                       # construit fr-workspace/chasse/zones.json
    python3 fr-workspace/scripts/chasser.py zones --verifier            # chaque texte dans exactement une zone
    python3 fr-workspace/scripts/chasser.py tirer --n 1000 --graine G --sortie fr-workspace/chasse/mesure-depart/tirage.json
    python3 fr-workspace/scripts/chasser.py paquets --filet F2 --zone Z --dossier fr-workspace/chasse/zones/Z/paquets
    python3 fr-workspace/scripts/chasser.py valider --dossier D --filet confirmation --relecteur A --preuves
    python3 fr-workspace/scripts/chasser.py signalements --dossier D --sortie fr-workspace/chasse/zones/Z/signalements.json
    python3 fr-workspace/scripts/chasser.py verdicts --dossier D --famille confirmation --sortie V
    python3 fr-workspace/scripts/chasser.py lot --verdicts V --base Z --source "chasse Z" --dossier-lots D
    python3 fr-workspace/scripts/chasser.py mesurer --tirage T --verdicts V --sortie R
    python3 fr-workspace/scripts/chasser.py avancement --sortie fr-workspace/chasse/avancement.json
    python3 fr-workspace/scripts/chasser.py compter --en "knuckle" --id "railways" --ajouter-a Q.json
    python3 fr-workspace/scripts/chasser.py voir <id>

Code de retour : 0 si tout va bien, 1 si un contrôle trouve un problème (couverture, sorties d'agents, critère), 2 si
une entrée manque ou est illisible.
"""
from __future__ import annotations

import argparse
import datetime
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import verifier  # noqa: E402
from chasse import avancement, avis, mesure, paquets, textes as textes_mod, tirage, vers_lot, zones as zones_mod  # noqa: E402
from coherence import config as config_mod  # noqa: E402
from coherence import corpus as corpus_mod  # noqa: E402
from coherence.regles_derivees import Familles  # noqa: E402
from corrections.applicateur import espaces_des_jars  # noqa: E402


def lire(chemin):
    return json.loads(Path(chemin).read_text(encoding="utf-8"))


def ecrire(chemin, donnees) -> None:
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(donnees, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


class Pack:
    """Le corpus, la configuration et l'inventaire des textes, chargés une fois."""

    def __init__(self, racine=None, espace=verifier.ESPACE, chasse=None):
        self.espace = Path(espace).resolve()
        self.racine = Path(racine or verifier.racine_par_defaut(self.espace)).resolve()
        self.corpus = corpus_mod.charger(self.racine, self.espace)
        self.config = config_mod.charger_config(self.espace)
        # Clés mortes : celles que provenance.json a écartées, et celles que la chasse a reconnues (mortes.json :
        # [{cle, motif}], un objet d'un mod absent du pack, prouvé par la confirmation).
        chasse = Path(chasse) if chasse else self.espace / "chasse"
        reconnues = lire(chasse / "mortes.json") if (chasse / "mortes.json").is_file() else []
        mortes = frozenset([e.get("key", "") for e in self.config.provenance.get("cles_mortes_ecartees", [])]
                           + [e["cle"] for e in reconnues])
        self.textes, self.exclus = textes_mod.inventaire(self.corpus, espaces_des_jars(self.espace), mortes)
        self.par_id = {t.id: t for t in self.textes}
        self._temoins = None

    def liens(self) -> list:
        return zones_mod.liens_de_familles(Familles(self.corpus, self.config))

    def temoins(self) -> dict:
        if self._temoins is None:
            self._temoins = textes_mod.temoins(self.corpus, self.espace)
        return self._temoins

    def element(self, i: str) -> dict:
        t = self.par_id[i]
        return {"id": t.id, "espace": t.espace, "en": t.en, "fr": t.fr, "temoins": self.temoins().get(t.id, {})}


def _zones(a):
    return lire(a.chasse / "zones.json")["zones"]


def cmd_zones(a) -> int:
    pack = Pack(a.racine, a.espace, a.chasse)
    themes = lire(a.themes or a.chasse / "themes.json")
    a.sortie = a.sortie or a.chasse / "zones.json"
    if a.verifier or a.completer:
        donnees = lire(a.sortie)
        if a.completer:
            donnees["zones"], rapport = zones_mod.completer(donnees["zones"], pack.textes, pack.liens(), themes)
            ecrire(a.sortie, donnees)
            print(f"complétées : {len(rapport['ajoutes'])} texte(s) ajouté(s), {len(rapport['retires'])} retiré(s)")
            for i, z in sorted(rapport["ajoutes"].items()):
                print(f"  + {i} → {z}")
        problemes = zones_mod.verifier_couverture(donnees["zones"], pack.par_id)
        for p in problemes[:50]:
            print(f"  {p}")
        print(f"couverture : {len(pack.textes)} textes, {len(donnees['zones'])} zones, "
              + ("chacun exactement une fois" if not problemes else f"{len(problemes)} problème(s)"))
        return 1 if problemes else 0
    zones = zones_mod.construire(pack.textes, pack.liens(), themes)
    ecrire(a.sortie, {"date": datetime.date.today().isoformat(), "plafond": zones_mod.PLAFOND,
                      "textes": len(pack.textes), "exclus": pack.exclus, "zones": zones})
    for z in zones:
        print(f"  {z['id']:<22}{len(z['textes']):>6}{'  indivisible' if z['indivisible'] else ''}")
    print(f"{len(zones)} zones, {len(pack.textes)} textes ; exclus : "
          + ", ".join(f"{k} {v}" for k, v in sorted(pack.exclus.items())) + f" → {a.sortie}")
    return 0


def cmd_cles(a) -> int:
    zone = next((z for z in _zones(a) if z["id"] == a.zone), None)
    if zone is None:
        print(f"chasser : zone inconnue : {a.zone}", file=sys.stderr)
        return 2
    cles = [i for i in zone["textes"] if not i.startswith("journal#")]
    Path(a.sortie).write_text("\n".join(cles) + "\n", encoding="utf-8")
    print(f"{a.zone} : {len(cles)} clé(s) écrite(s) sur {len(zone['textes'])} texte(s) (les lignes du journal n'ont pas "
          f"de clé de constat) → {a.sortie}")
    return 0


def cmd_tirer(a) -> int:
    pack = Pack(a.racine, a.espace, a.chasse)
    zones = _zones(a)
    problemes = zones_mod.verifier_couverture(zones, pack.par_id)
    if problemes:
        print(f"chasser : zones.json ne couvre pas l'inventaire ({problemes[0]}…) : lancer zones --completer",
              file=sys.stderr)
        return 1
    t = tirage.tirer(zones, a.n, a.graine)
    ecrire(a.sortie, {"graine": a.graine, "n": a.n, "date": datetime.date.today().isoformat(), "tirage": t})
    print(f"{len(t)} textes tirés dans {len({x['zone'] for x in t})} zones, graine « {a.graine} » → {a.sortie}")
    return 0


def _ids(a, pack) -> list:
    if a.zone:
        return next(z for z in _zones(a) if z["id"] == a.zone)["textes"]
    if a.tirage:
        return [x["id"] for x in lire(a.tirage)["tirage"]]
    donnees = lire(a.ids)
    return sorted(donnees["defauts"] + donnees["corrects"]) if isinstance(donnees, dict) else donnees


def cmd_paquets(a) -> int:
    pack = Pack(a.racine, a.espace, a.chasse)
    nom = a.nom or a.zone or Path(a.dossier).parent.name
    famille = paquets.famille_de(a.filet)
    if not (a.filet.startswith("tiers-") or a.filet == "confirmation" or a.zone or a.tirage or a.ids):
        print(f"chasser : le filet {a.filet} demande --zone, --tirage ou --ids", file=sys.stderr)
        return 2
    cible = Path(a.dossier) / a.filet
    anciens = sorted(cible.glob("*.json")) if cible.is_dir() else []
    if anciens and not a.remplacer:
        print(f"chasser : {cible} contient déjà {len(anciens)} fichier(s) ; --remplacer les efface avant d'écrire",
              file=sys.stderr)
        return 1
    if a.filet.startswith("tiers-"):
        rendus_a, pa = paquets.lire_sorties(a.dossier, famille, "A")
        rendus_b, pb = paquets.lire_sorties(a.dossier, famille, "B")
        if pa or pb:
            print("\n".join(pa + pb), file=sys.stderr)
            return 1
        ids = avis.desaccords(rendus_a, rendus_b)
    elif a.filet == "confirmation":
        ids = [s["id"] for s in lire(a.signalements)]
    else:
        ids = _ids(a, pack)
    notes = {s["id"]: s["notes"] for s in lire(a.signalements)} if a.signalements else {}
    retro = {}
    if a.filet == "F1-comparaison":
        retro, p = paquets.lire_sorties(a.dossier, "F1-retro")
        if p:
            print("\n".join(p), file=sys.stderr)
            return 1
    for f in anciens:
        f.unlink()
    elements = []
    for i in ids:
        e = pack.element(i)
        if i in notes:
            e["notes"] = notes[i]
        if i in retro:
            e["retro"] = retro[i]["retro"]
        if a.filet.startswith("tiers-"):
            e["avis"] = {"A": rendus_a[i], "B": rendus_b[i]}
        elements.append(e)
    chemins = paquets.ecrire_entrees(a.dossier, paquets.entrees(a.filet, nom, elements, a.taille))
    print(f"{a.filet} : {len(elements)} élément(s) en {len(chemins)} paquet(s) → {Path(a.dossier) / a.filet}")
    return 0


def cmd_valider(a) -> int:
    if not list((Path(a.dossier) / a.filet).glob(f"{a.paquet or '*'}.entree.json")):
        print(f"chasser : aucun paquet sous {Path(a.dossier) / a.filet}" + (f" ({a.paquet})" if a.paquet else ""),
              file=sys.stderr)
        return 2
    rendus, problemes = paquets.lire_sorties(a.dossier, a.filet, a.relecteur, a.paquet)
    if a.preuves:
        pack = Pack(a.racine, a.espace, a.chasse)
        cles = set(pack.corpus.fr) | set(pack.corpus.en) | set(pack.par_id)
        racines = [pack.espace.parent, pack.racine]
        problemes += [f"{i} : {p}" for i, x in sorted(rendus.items()) for p in
                      (paquets.verifier_preuve(pr, cles, racines) for pr in x.get("preuves", [])) if p]
    for p in problemes:
        print(f"  {p}")
    print(f"{a.filet}{'-' + a.relecteur if a.relecteur else ''} : {len(rendus)} élément(s) lus, "
          f"{len(problemes)} problème(s)")
    return 1 if problemes else 0


def cmd_signalements(a) -> int:
    comparaison, p1 = paquets.lire_sorties(a.dossier, "F1-comparaison")
    lecture, p2 = paquets.lire_sorties(a.dossier, "F2")
    retire = (a.sans_f1 and "F1") or (a.sans_f2 and "F2")
    problemes = (p2 if a.sans_f1 else p1 + p2) if not a.sans_f2 else p1
    if problemes:
        print("\n".join(problemes), file=sys.stderr)
        return 1
    s = avis.signalements({} if retire == "F1" else comparaison, {} if retire == "F2" else lecture)
    ecrire(a.sortie, s)
    print(f"{len(s)} signalement(s) : F1 {sum('F1' in x['filets'] for x in s)}, F2 {sum('F2' in x['filets'] for x in s)}"
          f", les deux {sum(len(x['filets']) == 2 for x in s)} → {a.sortie}")
    return 0


def cmd_verdicts(a) -> int:
    rendus_a, pa = paquets.lire_sorties(a.dossier, a.famille, "A")
    rendus_b, pb = paquets.lire_sorties(a.dossier, a.famille, "B")
    rendus_c, pc = ({}, []) if not (Path(a.dossier) / f"tiers-{a.famille}").is_dir() else \
        paquets.lire_sorties(a.dossier, f"tiers-{a.famille}", "C")
    problemes = pa + pb + pc
    if problemes:
        print("\n".join(problemes), file=sys.stderr)
        return 1
    v = avis.verdicts(rendus_a, rendus_b, rendus_c, paquets.textes_lus(a.dossier, a.famille))
    ecrire(a.sortie, v)
    b = avis.bilan(v)
    print(f"{len(v)} verdict(s) : " + ", ".join(f"{k} {n}" for k, n in sorted(b.items())) + f" → {a.sortie}")
    return 1 if b.get("en_attente") else 0


def cmd_lot(a) -> int:
    pack = Pack(a.racine, a.espace, a.chasse)
    liste, ecartes = vers_lot.actions(lire(a.verdicts), pack.par_id, pack.corpus.journal_fr, a.source)
    lots = vers_lot.lots(a.base, liste, {"verdicts": str(a.verdicts), "date": datetime.date.today().isoformat()})
    for lot in lots:
        ecrire(Path(a.dossier_lots) / lot["lot"] / "lot.json", lot)
    variantes = sum(1 for x in liste if "variante" in x)
    print(f"{len(liste)} correction(s) en {len(lots)} lot(s) ({', '.join(l['lot'] for l in lots) or 'aucun'}), "
          f"{variantes} variante(s) à départager ; écartés : {len(ecartes)}")
    for i in ecartes:
        print(f"  écarté : {i}")
    return 0


def cmd_mesurer(a) -> int:
    r = mesure.resultat(lire(a.tirage)["tirage"], lire(a.verdicts))
    ecrire(a.sortie, r)
    for z, x in r["par_zone"].items():
        print(f"  {z:<22}{x['n']:>6}{x['majeurs']:>4} majeur(s){x['mineurs']:>4} mineur(s)   borne {x['borne_texte']}")
    print(f"{r['majeurs']} défaut(s) majeur(s) sur {r['n']} : borne haute à 95 % {r['borne_texte']} ; "
          f"critère (< 0,5 %) {'tenu' if r['critere'] else 'NON TENU'} → {a.sortie}")
    return 0 if r["critere"] or not a.exiger else 1


def cmd_banc_choisir(a) -> int:
    b = mesure.choisir_banc(lire(a.verdicts), a.graine)
    ecrire(a.sortie, b)
    print(f"banc : {len(b['defauts'])} défaut(s) dont {len(b['majeurs'])} majeur(s), {len(b['corrects'])} correct(s) → {a.sortie}")
    return 0


def cmd_banc_rendement(a) -> int:
    b = lire(a.banc)
    comparaison, p1 = paquets.lire_sorties(a.dossier, "F1-comparaison")
    lecture, p2 = paquets.lire_sorties(a.dossier, "F2")
    if p1 or p2:
        print("\n".join(p1 + p2), file=sys.stderr)
        return 1
    f1 = {i for i, x in comparaison.items() if x["ecart"]}
    f2 = {i for i, x in lecture.items() if x["accroche"]}
    r = {"F1": mesure.rendement(f1, b), "F2": mesure.rendement(f2, b), "F1 + F2": mesure.rendement(f1 | f2, b)}
    d = mesure.decider(r["F1"], r["F2"], r["F1 + F2"])
    pc = mesure.pourcent
    lignes = ["| filet | signalés | vrais | précision | rappel | rappel des majeurs | fausses alertes "
              f"| signalements prévus sur {a.textes} textes |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for nom, x in r.items():
        prevus = f"{mesure.projection(x, a.textes, a.taux):,}".replace(",", " ")
        lignes.append(f"| {nom} | {x['signales']} | {x['vrais']} | {pc(x['precision'])} | {pc(x['rappel'])} | "
                      f"{pc(x['rappel_majeurs'])} | {pc(x['fausses_alertes'])} | {prevus} |")
    lignes += ["", *(f"- **{f}** : {dec} ({raison})" for f, (dec, raison) in sorted(d.items()))]
    texte = "\n".join(lignes) + "\n"
    print(texte, end="")
    if a.sortie:
        ajouter_section(a.sortie, f"{a.titre} (graine « {b['graine']} »)", texte)
    return 0


def ajouter_section(chemin, titre: str, texte: str) -> None:
    """Ajoute « ## <titre> » et son texte à filets.md, créé avec son titre s'il n'existe pas."""
    chemin = Path(chemin)
    debut = chemin.read_text(encoding="utf-8") if chemin.is_file() else "# Rendement des filets\n"
    chemin.write_text(debut + f"\n## {titre}\n\n" + texte, encoding="utf-8")


def cmd_filets_pack(a) -> int:
    """Rendement des filets sur tout le pack : signalements et verdicts de toutes les zones."""
    signalements, verdicts = [], {}
    for rep in sorted((a.chasse / "zones").iterdir()):
        if (rep / "signalements.json").is_file() and (rep / "verdicts.json").is_file():
            signalements += lire(rep / "signalements.json")
            verdicts.update(lire(rep / "verdicts.json"))
    r = mesure.rendement_pack(signalements, verdicts)
    lignes = ["| filet | signalés | défauts confirmés | dont majeurs | précision |", "|---|---:|---:|---:|---:|"]
    lignes += [f"| {nom} | {x['signales']} | {x['confirmes']} | {x['majeurs']} | {mesure.pourcent(x['precision'])} |"
               for nom, x in r.items()]
    texte = "\n".join(lignes) + "\n"
    print(texte, end="")
    if a.sortie:
        ajouter_section(a.sortie, "Sur tout le pack", texte)
    return 0


def cmd_juger(a) -> int:
    pack = Pack(a.racine, a.espace, a.chasse)
    t = lire(a.tirage)["tirage"]
    v = lire(a.verdicts)
    choisis = sorted(random.Random(a.graine).sample([x["id"] for x in t], min(a.n, len(t))))
    page = {"id": a.id, "titre": a.titre, "nature": "mesure", "statut": "echantillon", "attend_verdict": True,
            "dette_avant": 0, "dette_apres": 0, "actions": len(choisis), "exceptions": [],
            "resume": "Textes tirés dans la mesure finale. Chacun est bon par défaut ; « Pas bonne » si le joueur "
                      "comprendrait mal, avec ce que tu aurais écrit.",
            "echantillon": [{"n": n, "cle": i, "anglais": pack.par_id[i].en, "avant": pack.par_id[i].fr, "apres": "",
                             "type": "texte", "motif": f"relecteurs : {v[i]['classe']}" + (
                                 f" ; correction proposée : {v[i]['correction']}" if v[i].get("correction") else "")}
                            for n, i in enumerate(choisis, start=1)]}
    ecrire(a.sortie, page)
    print(f"{len(choisis)} texte(s) à juger, graine « {a.graine} » → {a.sortie}")
    return 0


def cmd_avancement(a) -> int:
    a.sortie = a.sortie or a.chasse / "avancement.json"
    e = avancement.etat(_zones(a), a.chasse)
    ecrire(a.sortie, e)
    faites = sum(1 for z in e["zones"] if z["statut"] == "faite")
    print(f"avancement : {faites} zone(s) faite(s) sur {len(e['zones'])} → {a.sortie}")
    return 0


def cmd_compter(a) -> int:
    """Les textes de l'inventaire qui répondent aux motifs (expressions régulières, sans casse) : leur nombre, leurs
    espaces de noms, des exemples ; avec --ajouter-a, leurs ids rejoignent les « cles » d'une question."""
    pack = Pack(a.racine, a.espace, a.chasse)
    motifs = [(champ, re.compile(v, re.I)) for champ, v in (("id", a.id), ("espace", a.espace_de_noms), ("en", a.en),
                                                                      ("fr", a.fr)) if v]
    sauf = re.compile(a.sauf_fr, re.I) if a.sauf_fr else None
    trouves = [t for t in pack.textes if all(m.search(getattr(t, champ)) for champ, m in motifs)
               and (not a.origine or t.origine == a.origine) and not (sauf and sauf.search(t.fr))]
    par_espace = Counter(t.espace for t in trouves)
    print(f"{len(trouves)} texte(s) ; " + ", ".join(f"{e} {n}" for e, n in par_espace.most_common(8)))
    for t in trouves[:a.montrer]:
        print(f"  {t.id} | {t.en} | {t.fr}")
    if a.ajouter_a:
        q = lire(a.ajouter_a)
        q["cles"] = sorted(set(q.get("cles", [])) | {t.id for t in trouves})
        ecrire(a.ajouter_a, q)
        print(f"{len(q['cles'])} clé(s) dans {a.ajouter_a}")
    return 0


def cmd_voir(a) -> int:
    pack = Pack(a.racine, a.espace, a.chasse)
    if a.id not in pack.par_id:
        print(f"chasser : {a.id} n'est pas un texte de l'inventaire "
              "(Mojang, clé morte, vide ou sans anglais : cherche avec grep, voir la consigne)", file=sys.stderr)
        return 2
    e = pack.element(a.id)
    t = pack.par_id[a.id]
    e.update(origine=t.origine, unite=t.unite, zone=next(
        (z["id"] for z in _zones(a) if a.id in z["textes"]), "") if (a.chasse / "zones.json").is_file() else "")
    quetes = [q for q in pack.corpus.quetes if a.id in q.cles]
    if quetes:
        e["quetes"] = [{"chapitre": q.chapitre, "icone": q.icone, "taches": [list(x.objets) for x in q.taches]} for q in quetes]
    champ = pack.corpus.champ(a.id) if "#" in a.id and not a.id.startswith("journal#") else None
    if champ:
        e["objets_du_livre"] = list(champ.objets)
    decisions = pack.config.provenance.get("cles", {}).get(a.id)
    if decisions:
        e["provenance"] = decisions[-3:]
    print(json.dumps(e, ensure_ascii=False, indent=1))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="La chasse au reste (spec 3).")
    p.add_argument("--racine", type=Path, help="arbre du pack (défaut : celui du vérificateur)")
    p.add_argument("--espace", type=Path, default=verifier.ESPACE, help="espace de travail (défaut : celui du script)")
    p.add_argument("--chasse", type=Path, help="dossier de la chasse (défaut : <espace>/chasse)")
    sp = p.add_subparsers(dest="commande", required=True)
    s = sp.add_parser("zones", help="construire, vérifier ou compléter zones.json")
    s.add_argument("--themes", type=Path, help="défaut : <chasse>/themes.json")
    s.add_argument("--sortie", type=Path, help="défaut : <chasse>/zones.json")
    s.add_argument("--verifier", action="store_true")
    s.add_argument("--completer", action="store_true")
    s.set_defaults(f=cmd_zones)
    s = sp.add_parser("cles", help="les clés d'une zone, une par ligne (pour mesurer_lot.py --cles)")
    s.add_argument("--zone", required=True)
    s.add_argument("--sortie", type=Path, required=True)
    s.set_defaults(f=cmd_cles)
    s = sp.add_parser("tirer", help="tirage stratifié d'une mesure")
    s.add_argument("--n", type=int, required=True)
    s.add_argument("--graine", required=True)
    s.add_argument("--sortie", type=Path, required=True)
    s.set_defaults(f=cmd_tirer)
    s = sp.add_parser("paquets", help="écrire les paquets d'un filet")
    s.add_argument("--filet", required=True, choices=sorted(paquets.VUS))
    quoi = s.add_mutually_exclusive_group()
    quoi.add_argument("--zone")
    quoi.add_argument("--tirage", type=Path)
    quoi.add_argument("--ids", type=Path, help="une liste d'ids, ou un banc (défauts et corrects)")
    s.add_argument("--signalements", type=Path)
    s.add_argument("--dossier", type=Path, required=True)
    s.add_argument("--nom")
    s.add_argument("--taille", type=int, default=0)
    s.add_argument("--remplacer", action="store_true", help="efface d'abord les entrées et sorties déjà là de ce filet")
    s.set_defaults(f=cmd_paquets)
    s = sp.add_parser("valider", help="valider les sorties d'un filet")
    s.add_argument("--dossier", type=Path, required=True)
    s.add_argument("--filet", required=True, choices=sorted(paquets.VUS))
    s.add_argument("--relecteur", default="")
    s.add_argument("--paquet", default="", help="ce seul paquet (« 007 ») ; défaut : tous")
    s.add_argument("--preuves", action="store_true", help="vérifier aussi que chaque preuve existe")
    s.set_defaults(f=cmd_valider)
    s = sp.add_parser("signalements", help="réunir les signalements de F1 et de F2")
    s.add_argument("--dossier", type=Path, required=True)
    s.add_argument("--sortie", type=Path, required=True)
    retrait = s.add_mutually_exclusive_group()
    retrait.add_argument("--sans-f1", action="store_true", help="F1 retiré par le banc")
    retrait.add_argument("--sans-f2", action="store_true", help="F2 retiré par le banc")
    s.set_defaults(f=cmd_signalements)
    s = sp.add_parser("verdicts", help="verdicts des avis A, B et du tiers C")
    s.add_argument("--dossier", type=Path, required=True)
    s.add_argument("--famille", required=True, choices=sorted(paquets.CLASSES))
    s.add_argument("--sortie", type=Path, required=True)
    s.set_defaults(f=cmd_verdicts)
    s = sp.add_parser("lot", help="lots de corrections des défauts confirmés")
    s.add_argument("--verdicts", type=Path, required=True)
    s.add_argument("--base", required=True)
    s.add_argument("--source", required=True)
    s.add_argument("--dossier-lots", type=Path, required=True)
    s.set_defaults(f=cmd_lot)
    s = sp.add_parser("mesurer", help="taux de défauts majeurs et borne haute")
    s.add_argument("--tirage", type=Path, required=True)
    s.add_argument("--verdicts", type=Path, required=True)
    s.add_argument("--sortie", type=Path, required=True)
    s.add_argument("--exiger", action="store_true", help="code 1 si le critère n'est pas tenu")
    s.set_defaults(f=cmd_mesurer)
    s = sp.add_parser("banc-choisir", help="les textes du banc des filets")
    s.add_argument("--verdicts", type=Path, required=True)
    s.add_argument("--graine", required=True)
    s.add_argument("--sortie", type=Path, required=True)
    s.set_defaults(f=cmd_banc_choisir)
    s = sp.add_parser("banc-rendement", help="précision et rappel des filets sur le banc")
    s.add_argument("--banc", type=Path, required=True)
    s.add_argument("--dossier", type=Path, required=True)
    s.add_argument("--textes", type=int, required=True, help="textes de l'inventaire, pour la projection")
    s.add_argument("--taux", type=float, required=True, help="taux de défauts (majeurs et mineurs) de la mesure")
    s.add_argument("--sortie", type=Path, help="filets.md, complété d'une section")
    s.add_argument("--titre", default="Sur le banc", help="titre de la section")
    s.set_defaults(f=cmd_banc_rendement)
    s = sp.add_parser("filets-pack", help="rendement des filets sur tout le pack (phase 2)")
    s.add_argument("--sortie", type=Path, help="filets.md, complété d'une section « Sur tout le pack »")
    s.set_defaults(f=cmd_filets_pack)
    s = sp.add_parser("juger", help="l'échantillon de la mesure finale pour l'utilisateur")
    s.add_argument("--tirage", type=Path, required=True)
    s.add_argument("--verdicts", type=Path, required=True)
    s.add_argument("--n", type=int, default=50)
    s.add_argument("--graine", required=True)
    s.add_argument("--id", default="mesure-finale")
    s.add_argument("--titre", default="Mesure finale : textes à juger")
    s.add_argument("--sortie", type=Path, required=True)
    s.set_defaults(f=cmd_juger)
    s = sp.add_parser("avancement", help="le document etat/chasse de la page")
    s.add_argument("--sortie", type=Path, help="défaut : <chasse>/avancement.json")
    s.set_defaults(f=cmd_avancement)
    s = sp.add_parser("compter", help="compter les textes qui répondent à des motifs (questions, fiche)")
    s.add_argument("--id")
    s.add_argument("--espace-de-noms", help="motif sur l'espace de noms du texte (« society », « livre:almanac »…)")
    s.add_argument("--en")
    s.add_argument("--fr")
    s.add_argument("--sauf-fr")
    s.add_argument("--origine", choices=["projet", "jar", "livre", "journal"])
    s.add_argument("--montrer", type=int, default=5)
    s.add_argument("--ajouter-a", type=Path, help="une question JSON dont les « cles » reçoivent les ids trouvés")
    s.set_defaults(f=cmd_compter)
    s = sp.add_parser("voir", help="tout ce qu'on sait d'un texte (pour la confirmation)")
    s.add_argument("id")
    s.set_defaults(f=cmd_voir)
    a = p.parse_args(argv)
    a.chasse = a.chasse or a.espace / "chasse"
    try:
        return a.f(a)
    except (corpus_mod.CorpusIncomplet, config_mod.ConfigInvalide, FileNotFoundError, json.JSONDecodeError,
            ValueError, KeyError) as e:
        print(f"chasser : {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
