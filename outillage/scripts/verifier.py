#!/usr/bin/env python3
"""Vérifie la traduction française de Society: Sunlit Valley.

    python3 fr-workspace/scripts/verifier.py                    # tous les contrôles
    python3 fr-workspace/scripts/verifier.py --controle codes   # un seul (répétable)
    python3 fr-workspace/scripts/verifier.py --json > rapport.json
    python3 fr-workspace/scripts/verifier.py --ecrire-instantane fr-workspace/instantane/4.1.5.json.gz
    python3 outillage/scripts/verifier.py --racine . --instantane outillage/instantane/4.1.5.json.gz
    python3 outillage/scripts/verifier.py --dette-base base.json  # échoue si la dette a crû ou changé (Action du fork)

Code de retour : 0 si aucun constat bloquant n'échappe aux exceptions et à la dette, 1 sinon,
2 si le corpus ou les données de cohérence manquent, sont illisibles ou mal formés.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ESPACE = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from coherence import config as config_mod  # noqa: E402
from coherence import corpus as corpus_mod  # noqa: E402
from coherence import rapport  # noqa: E402
from coherence.controles import CONTROLES  # noqa: E402
from coherence.controles.orthographe import LanguageToolIndisponible  # noqa: E402
from coherence.modele import Options  # noqa: E402
from coherence.registre import Registre  # noqa: E402

SIGNALES_AFFICHES = 20


def racine_par_defaut(espace: Path) -> Path:
    """Le clone du pack s'il est là (dépôt de travail), sinon le dossier parent (fork)."""
    clone = espace.parent / "society-sunlit-valley"
    return clone if clone.is_dir() else espace.parent


def compteurs(config) -> dict:
    cles = config.provenance.get("cles", {})
    return {"cles_tracees": len(cles),
            "decisions": sum(len(v) for v in cles.values() if isinstance(v, list)),
            "termes_glossaire": len(config.provenance.get("glossaire", {}))}


def analyser(racine, espace, instantane=None, controles=None, options=Options(), regles=None):
    """Charge, contrôle, puis applique exceptions et dette ; `regles` active des règles en attente pour ce seul
    passage (mesurer_lot.py --regle)."""
    config = config_mod.charger_config(espace)
    config.regles.update(regles or {})
    debut = time.time()
    corpus = corpus_mod.charger(racine, espace, instantane)
    registre = Registre(corpus, config)
    durees = {"corpus": time.time() - debut}
    noms = list(controles or sorted(CONTROLES))
    constats = []
    for nom in noms:
        debut = time.time()
        constats += CONTROLES[nom](corpus, registre, config, options)
        durees[nom] = time.time() - debut
    resultat = rapport.appliquer(constats, config.exceptions, config.dette, corpus.texte, noms, config.renvois)
    return corpus, config, resultat, durees


def garde_fou(racine=None, espace=ESPACE) -> bool:
    """Pour les scripts de construction : True si aucun constat bloquant n'échappe à la dette ni
    aux exceptions ; sinon, affiche les premiers sur la sortie d'erreur et rend False."""
    try:
        _, _, resultat, _ = analyser(racine or racine_par_defaut(espace), espace)
    except (corpus_mod.CorpusIncomplet, config_mod.ConfigInvalide) as e:
        print(f"vérificateur : {e}", file=sys.stderr)
        return False
    if resultat.code == 0:
        return True
    for c in resultat.bloquants[:SIGNALES_AFFICHES]:
        print(_ligne(c), file=sys.stderr)
    print(f"construction refusée : {len(resultat.bloquants)} constat(s) bloquant(s), "
          f"{len(resultat.sans_motif)} exception(s) sans motif ; détail : python3 fr-workspace/scripts/verifier.py",
          file=sys.stderr)
    return False


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Vérifie la traduction française du pack.")
    p.add_argument("--racine", type=Path, help="arbre du pack (défaut : le clone, sinon le dossier parent)")
    p.add_argument("--espace", type=Path, default=ESPACE, help="espace de travail (défaut : celui du script)")
    p.add_argument("--instantane", type=Path, help="lire anglais, jars et scripts dans cet instantané")
    p.add_argument("--controle", action="append", choices=sorted(CONTROLES), help="ce contrôle seulement")
    p.add_argument("--cloture", action="store_true",
                   help="échouer tant que le sous-projet 2 n'est pas clos (spec 2 §13)")
    p.add_argument("--json", action="store_true", help="rapport complet en JSON")
    p.add_argument("--languagetool", action="store_true", help="passe LanguageTool locale (orthographe)")
    p.add_argument("--url-languagetool", default=Options().url_languagetool)
    p.add_argument("--dette-retirer-resolus", action="store_true", help="retirer de la dette les entrées résolues")
    p.add_argument("--ecrire-instantane", type=Path, metavar="FICHIER", help="écrire l'instantané et s'arrêter")
    p.add_argument("--dette-base", type=Path, metavar="FICHIER",
                   help="échouer si dette.json contient une entrée absente de cette dette de référence, "
                        "ou gardée avec une empreinte différente")
    a = p.parse_args(argv)
    espace = a.espace.resolve()
    racine = (a.racine or racine_par_defaut(espace)).resolve()
    options = Options(languagetool=a.languagetool, url_languagetool=a.url_languagetool)
    try:
        if a.ecrire_instantane:
            corpus = corpus_mod.charger(racine, espace, a.instantane)
            if corpus.scripts_amont is None and config_mod.charger_config(espace).scripts_patches:
                print(f"verifier : instantané non écrit : git n'a pas lu les hashs amont des scripts ({racine}), "
                      "et scripts_patches.json en attend ; le lancer dans le clone du pack", file=sys.stderr)
                return 2
            corpus_mod.ecrire_instantane(corpus, a.ecrire_instantane)
            print(f"instantané de la version {corpus.version} écrit : {a.ecrire_instantane}")
            return 0
        corpus, config, resultat, durees = analyser(racine, espace, a.instantane, a.controle, options)
        base = config_mod.lire_dette(a.dette_base) if a.dette_base else None
    except (corpus_mod.CorpusIncomplet, config_mod.ConfigInvalide, LanguageToolIndisponible) as e:
        print(f"verifier : {e}", file=sys.stderr)
        return 2
    # La dette ne fait que décroître (spec §10) : face à la dette de référence, une entrée nouvelle fait échouer,
    # de même qu'une entrée gardée mais dont l'empreinte a changé (qui touche une clé la corrige).
    hausse = rapport.dette_en_hausse(config.dette, base) if base is not None else None
    modifiee = rapport.dette_modifiee(config.dette, base) if base is not None else None
    code = resultat.code or (1 if (hausse or modifiee) else 0)
    obstacles = rapport.obstacles_a_la_cloture(resultat, config.dette, config.renvois) if a.cloture else None
    if obstacles:
        code = code or 1
    retirees = []
    if a.dette_retirer_resolus and resultat.dette_resolue:
        if resultat.code:
            # Sur un passage en échec, ce qui semble résolu peut venir d'un contrôle vidé : rien ne se retire.
            print(f"verifier : --dette-retirer-resolus refusé : le passage échoue (code {resultat.code}) ; "
                  "corriger d'abord, rien n'est retiré de dette.json", file=sys.stderr)
        else:
            resolues = {id(e) for e in resultat.dette_resolue}
            config_mod.ecrire(espace, "dette", [e for e in config.dette if id(e) not in resolues])
            retirees = resultat.dette_resolue
    if a.json:
        rapport_json = _en_json(corpus, config, resultat, durees)
        if hausse is not None:
            rapport_json["dette_en_hausse"] = hausse
        if modifiee is not None:
            rapport_json["dette_modifiee"] = modifiee
        if obstacles is not None:
            rapport_json["cloture"] = obstacles
        rapport_json["code"] = code
        print(json.dumps(rapport_json, ensure_ascii=False, indent=1))
    else:
        _afficher(corpus, config, resultat, durees, retirees, hausse, modifiee, a.dette_base, code, obstacles)
    return code


def _en_json(corpus, config, r, durees) -> dict:
    return {
        "version": corpus.version,
        "compteurs": compteurs(config),
        "durees": {k: round(v, 2) for k, v in durees.items()},
        "bloquants": [c.en_dict() for c in r.bloquants],
        "signales": [c.en_dict() for c in r.signales],
        "en_dette": [c.en_dict() for c in r.en_dette],
        "couverts": [dict(c.en_dict(), exception=e) for c, e in r.couverts],
        "orphelines": r.orphelines,
        "sans_motif": r.sans_motif,
        "dette_resolue": r.dette_resolue,
        "provisoires": r.provisoires,
        "renvoyees": r.renvoyees,
        "renvois_orphelins": r.renvois_orphelins,
        "code": r.code,
    }


def _entree(e) -> str:
    objet = rapport.objet_de(e.get("objet"))
    objet = ", ".join(objet) if isinstance(objet, tuple) else objet
    return f"  [{e.get('controle')}] {e.get('cle')}" + (f" ({objet})" if objet else "")


def _ligne(c) -> str:
    objet = ", ".join(c.objet) if isinstance(c.objet, tuple) else c.objet
    texte = f"  [{c.controle}] {c.cle}" + (f" ({objet})" if objet else "") + f" : {c.detail}"
    if c.actuel:
        texte += f"\n      actuel  : {c.actuel}"
    if c.attendu:
        texte += f"\n      attendu : {c.attendu}"
    return texte


def _afficher(corpus, config, r, durees, retirees, hausse=None, modifiee=None, base=None, code=None, obstacles=None) -> None:
    n = compteurs(config)
    print(f"Society: Sunlit Valley {corpus.version or '?'} : {len(corpus.fr)} clés françaises, "
          f"dont {len(corpus.ns_projet)} du projet ; {len(corpus.livres)} champs de livres ; "
          f"{len(corpus.quetes)} quêtes ({durees['corpus']:.1f} s)")
    print(f"provenance : {n['cles_tracees']} clés tracées, {n['decisions']} décisions, "
          f"{n['termes_glossaire']} termes au glossaire")
    print(f"\n{'contrôle':<18}{'bloquants':>10}{'signalés':>10}{'dette':>8}{'exceptions':>12}{'durée':>9}")
    for nom in (k for k in durees if k != "corpus"):
        compte = lambda liste: sum(1 for c in liste if c.controle == nom)
        print(f"{nom:<18}{compte(r.bloquants):>10}{compte(r.signales):>10}{compte(r.en_dette):>8}"
              f"{sum(1 for c, _ in r.couverts if c.controle == nom):>12}{durees[nom]:>8.1f}s")
    if r.bloquants:
        print(f"\nBLOQUANTS ({len(r.bloquants)})")
        for c in r.bloquants:
            print(_ligne(c))
    if r.signales:
        print(f"\nSIGNALÉS ({len(r.signales)}) — les {SIGNALES_AFFICHES} premiers par contrôle ; --json pour tout")
        vus = {}
        for c in r.signales:
            vus[c.controle] = vus.get(c.controle, 0) + 1
            if vus[c.controle] <= SIGNALES_AFFICHES:
                print(_ligne(c))
    if r.sans_motif:
        print(f"\nEXCEPTIONS SANS MOTIF ({len(r.sans_motif)}) — refusées")
        for e in r.sans_motif:
            print(f"  [{e.get('controle')}] {e.get('cle')}")
    if r.orphelines:
        print(f"\nEXCEPTIONS ORPHELINES ({len(r.orphelines)}) — ne couvrent plus rien, à retirer")
        for e in r.orphelines:
            print(f"  [{e.get('controle')}] {e.get('cle')} : {e.get('motif')}")
    if retirees:
        print(f"\nDETTE : {len(retirees)} entrée(s) retirée(s) de dette.json")
    elif r.dette_resolue:
        print(f"\nDETTE RÉSOLUE ({len(r.dette_resolue)}) — à retirer avec --dette-retirer-resolus")
    for e in retirees or r.dette_resolue:
        print(_entree(e))
    if hausse:
        print(f"\nDETTE EN HAUSSE ({len(hausse)}) — absente de {base} : la dette ne fait que décroître ; "
              "un écart voulu va dans exceptions.json, avec son motif")
        for e in hausse:
            print(_entree(e))
    if modifiee:
        print(f"\nDETTE MODIFIÉE ({len(modifiee)}) — empreinte différente de {base} : qui touche une clé "
              "en corrige le défaut (spec §10)")
        for e in modifiee:
            print(_entree(e))
    code = r.code if code is None else code
    if r.provisoires:
        print(f"\nEXCEPTIONS PROVISOIRES ({len(r.provisoires)}) — en attente d'une réponse sur la page de relecture")
        for e in r.provisoires:
            print(f"  [{e.get('controle')}] {e.get('cle')} : question {e.get('question')}")
    if r.renvois_orphelins:
        print(f"\nRENVOIS ORPHELINS ({len(r.renvois_orphelins)}) — sans entrée de dette, à retirer de renvois.json")
        for e in r.renvois_orphelins:
            print(_entree(e))
    if r.renvoyees:
        print(f"\nRENVOYÉES AU SOUS-PROJET 3 : {len(r.renvoyees)} entrée(s) de dette")
    if obstacles is not None:
        print(f"\nCLÔTURE : {'possible' if not obstacles else 'impossible'}")
        for o in obstacles:
            print(f"  {o}")
    print(f"\nverdict : {'ÉCHEC' if code else 'OK'} ({len(r.bloquants)} bloquant(s), "
          f"{len(r.en_dette)} en dette, {len(r.signales)} signalé(s))")


if __name__ == "__main__":
    sys.exit(main())
