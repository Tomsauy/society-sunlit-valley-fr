#!/usr/bin/env python3
"""Réconcilie provenance.json avec la traduction, une fois, au sous-projet 1.

    python3 fr-workspace/scripts/reconcilier_provenance.py              # bilan ; rien n'est écrit
    python3 fr-workspace/scripts/reconcilier_provenance.py --appliquer  # accents seuls et clés absentes

Classe chaque clé tracée — clé de langue ou champ de livre (« <livre>/<fichier>#/<pointeur> ») : conforme,
écart d'accents seuls, écart de la seule ligature, vrai écart, absente du français mais affichée en jeu (à
écrire : essence Every Compat activée, anglais présent), absente et morte, sans valeur décidée.
--appliquer trace une décision « reaccentuation » (chantier du 14/09, d22ca17ef) pour chaque écart
d'accents seuls, une décision « ligature » (convention « oe » de CLAUDE.md, appliquée par le fork 01708c67
le 09/09) pour chaque écart de la seule ligature, déplace les clés mortes dans cles_mortes_ecartees et
retire _statistiques, recopie périmée des compteurs que verifier.py affiche désormais. Les vrais écarts
se traitent un par un ; les clés à écrire gardent leur décision, que le sous-projet 2 appliquera.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import unicodedata
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ESPACE = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from coherence import config as config_mod  # noqa: E402
from coherence import corpus as corpus_mod  # noqa: E402
from coherence.controles.decisions import valeur_actuelle, valeur_decidee  # noqa: E402
from coherence.registre import CLE_OBJET  # noqa: E402
from verifier import racine_par_defaut  # noqa: E402

CLASSES = ("conformes", "accents", "ligature", "ecarts", "a_ecrire", "absentes", "sans_valeur")


def sans_diacritiques(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")


def sans_ligature(texte: str) -> str:
    """Convention « oe » de CLAUDE.md : « œ » s'écrit « oe », « Œ » « Oe » (« OE » en capitales)."""
    return re.sub("Œ(?=[a-zé])", "Oe", texte).replace("Œ", "OE").replace("œ", "oe")


def classer(provenance: dict, corpus, en_attente=frozenset()) -> dict:
    """Les clés tracées par classe. Une clé que la dette tient en attente de décision (`en_attente`) reste un vrai
    écart : un arbitrage ne se résout jamais mécaniquement, même quand seuls les accents ou la ligature diffèrent."""
    classes = {nom: [] for nom in CLASSES}
    for cle, decisions in provenance["cles"].items():
        decidee, actuelle = valeur_decidee(decisions), valeur_actuelle(corpus, cle)
        if decidee is None:
            classes["sans_valeur"].append(cle)
        elif actuelle is None:
            affichee = "#" not in cle and (cle in corpus.essences or bool(corpus.anglais(cle)))
            classes["a_ecrire" if affichee else "absentes"].append(cle)
        elif actuelle == decidee:
            classes["conformes"].append(cle)
        elif cle in en_attente:
            classes["ecarts"].append(cle)
        elif sans_ligature(decidee) == actuelle:
            classes["ligature"].append(cle)
        elif sans_diacritiques(actuelle) == sans_diacritiques(decidee):
            classes["accents"].append(cle)
        else:
            classes["ecarts"].append(cle)
    return classes


def _namespace(cle: str, decisions: list) -> str:
    """Le namespace d'une clé morte : celui de la clé d'objet, sinon celui du fichier tracé ; pour un champ de livre,
    le livre."""
    m = CLE_OBJET.match(cle)
    if m:
        return m.group(2)
    if "#" in cle:
        return cle.split("/", 1)[0]
    fichier = next((d.get("fichier", "") for d in decisions if isinstance(d, dict) and d.get("fichier")), "")
    m = re.search(r"assets/([^/]+)/lang", fichier)
    return m.group(1) if m else ""


def appliquer(provenance: dict, corpus, classes: dict) -> None:
    aujourdhui = datetime.date.today().isoformat()
    for cle in classes["accents"]:
        provenance["cles"][cle].append({
            "type": "reaccentuation", "fr": valeur_actuelle(corpus, cle), "date": "2026-09-14", "commit": "d22ca17ef",
            "raison": "chantier des accents : même valeur, accentuée ; tracé à la réconciliation du 28/09"})
    for cle in classes["ligature"]:
        provenance["cles"][cle].append({
            "type": "ligature", "fr": valeur_actuelle(corpus, cle), "date": "2026-09-09", "commit": "01708c67",
            "raison": "convention « oe », jamais la ligature « œ » (CLAUDE.md ; arbitrage de l'utilisateur du 29/08, "
                      "__convention_ligature) : même valeur, sans ligature, appliquée par le fork 01708c67 (#5) ; "
                      f"tracé à la réconciliation du {aujourdhui[8:10]}/{aujourdhui[5:7]}"})
    for cle in classes["absentes"]:
        decisions = provenance["cles"].pop(cle)
        provenance.setdefault("cles_mortes_ecartees", []).append({
            "ns": _namespace(cle, decisions), "key": cle, "date": aujourdhui,
            "raison": "clé tracée absente du français à la réconciliation", "decisions": decisions})
    provenance.pop("_statistiques", None)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Réconcilie provenance.json avec la traduction.")
    p.add_argument("--racine", type=Path)
    p.add_argument("--espace", type=Path, default=ESPACE)
    p.add_argument("--appliquer", action="store_true")
    a = p.parse_args(argv)
    espace = a.espace.resolve()
    try:
        corpus = corpus_mod.charger((a.racine or racine_par_defaut(espace)).resolve(), espace)
        config = config_mod.charger_config(espace)
    except (corpus_mod.CorpusIncomplet, config_mod.ConfigInvalide) as e:
        print(f"reconcilier_provenance : {e}", file=sys.stderr)
        return 2
    en_attente = {e.get("cle") for e in config.dette if e.get("en_attente_de_decision")}
    chemin = espace / "provenance.json"
    provenance = json.loads(chemin.read_text(encoding="utf-8"))
    classes = classer(provenance, corpus, en_attente)
    for nom in CLASSES:
        print(f"{nom:<12}{len(classes[nom]):>6}")
    print("\nVRAIS ÉCARTS — à traiter un par un")
    for cle in sorted(classes["ecarts"]):
        print(f"  {cle}\n    décidée : {valeur_decidee(provenance['cles'][cle])}\n"
              f"    actuelle : {valeur_actuelle(corpus, cle)}")
    if a.appliquer:
        appliquer(provenance, corpus, classes)
        chemin.write_text(json.dumps(provenance, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"\nappliqué : {len(classes['accents'])} réaccentuations, {len(classes['ligature'])} ligatures, "
              f"{len(classes['absentes'])} clés écartées")
    return 0


if __name__ == "__main__":
    sys.exit(main())
