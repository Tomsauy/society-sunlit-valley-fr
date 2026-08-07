#!/usr/bin/env python3
"""Consolide la traçabilité des traductions en un index unique.

Rassemble, pour chaque clé, le « pourquoi » de sa traduction : décisions d'arbitrage,
corrections de relecture avec leur motif, unifications de cohérence, verdicts sur les
clés sans source anglaise. Produit fr-workspace/provenance.json, destiné à alimenter
une interface de consultation — et à rendre jetable le matériau brut des workflows.
"""
import json
from collections import defaultdict
from pathlib import Path

WS = Path(__file__).resolve().parents[1]

def load(name, default=None):
    p = WS / name
    if not p.exists():
        return default if default is not None else []
    try:
        return json.loads(p.read_text())
    except Exception:
        return default if default is not None else []

def main() -> None:
    events = defaultdict(list)
    stats = defaultdict(int)

    # 1. arbitrages « valeur identique à l'anglais » (vagues mods 4.1 → 4.4)
    for n in ("4.1", "4.2", "4.3", "4.4"):
        arb = load(f"wave{n}-arbitrage.json")
        flag = {f["key"]: f for f in load(f"wave{n}-flagged.json") if isinstance(f, dict)}
        for a in arb:
            if not isinstance(a, dict) or "key" not in a:
                continue
            ev = {"type": "arbitrage_identique",
                  "decision": "garde_anglais" if a.get("keep") else "traduit",
                  "en": a.get("en")}
            if not a.get("keep") and a.get("fr"):
                ev["fr"] = a["fr"]
            if a["key"] in flag:
                ev["lot"] = flag[a["key"]].get("batch", "").split("/")[-1]
            events[a["key"]].append(ev)
            stats["arbitrages"] += 1

    # 2. corrections de relecture qualité (avec motif)
    for f in sorted((WS / "batches").glob("review-out-*.json")):
        try: data = json.loads(f.read_text())
        except Exception: continue
        for c in data.get("corrections", []):
            if not c.get("key"):
                continue
            events[c["key"]].append({"type": "relecture", "fr": c.get("fr"),
                                     "raison": c.get("reason"), "fichier": c.get("file")})
            stats["corrections_relecture"] += 1

    # 3. clés sans source anglaise : certitude + vérification adverse
    enrichi = {e["key"]: e for e in load("orphans-enrichi.json")}
    for o in load("orphans-final.json"):
        k = o.get("key")
        if not k:
            continue
        ctx = enrichi.get(k, {})
        ev = {"type": "sans_source_anglaise", "fr": o.get("fr"),
              "nom_affiche_en_jeu": ctx.get("nom_derive"),
              "certitude": o.get("certitude"), "raison": o.get("pourquoi"),
              "temoins": ctx.get("temoins") or None}
        if o.get("verif"):
            ev["verification_adverse"] = {"verdict": o["verif"], "raison": o.get("pourquoi_verif")}
        events[k].append(ev)
        stats["cles_sans_anglais"] += 1

    # 4. unifications de cohérence (indexées par chaîne anglaise, pas par clé)
    reconciliation = []
    div = {d["en"]: d for d in load("divergences.json")}
    for c in load("choix-reconciliation.json"):
        if not isinstance(c, dict) or "en" not in c:
            continue
        entry = {"en": c["en"], "raison": c.get("why"),
                 "decision": "variantes_conservees" if c.get("keep_distinct") else "unifie"}
        if not c.get("keep_distinct"):
            entry["fr_retenu"] = c.get("chosen_fr")
        if c["en"] in div:
            entry["variantes"] = sorted(div[c["en"]]["variants"])
        reconciliation.append(entry)
        stats["reconciliations"] += 1

    # 5. provenance terminologique du glossaire
    ORIGINES = {"vanilla": "Minecraft vanilla (officiel Mojang)",
                "jar": "traduction officielle du mod",
                "sdv": "terminologie Stardew Valley FR",
                "agent": "arbitrage de traduction",
                "technique": "placeholder technique"}
    glossaire = []
    for e in load("glossaire.json", {}).get("entries", []):
        glossaire.append({"en": e["en"], "fr": e.get("fr"),
                          "garde_anglais": bool(e.get("keep_english")),
                          "origine": ORIGINES.get(e.get("origin"), e.get("origin")),
                          "raison": e.get("rationale")})
    stats["termes_glossaire"] = len(glossaire)

    # 6. clés retirées parce que mortes
    mortes = [{"ns": s["ns"], "key": s["key"]} for s in load("dead-keys-final.json", {}).get("suspect", [])]

    out = {
        "_a_propos": "Traçabilité des décisions de traduction FR — Society: Sunlit Valley",
        "_statistiques": dict(stats),
        "cles": {k: v for k, v in sorted(events.items())},
        "reconciliation_par_chaine_anglaise": reconciliation,
        "glossaire": glossaire,
        "cles_mortes_ecartees": mortes,
    }
    dest = WS / "provenance.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(f"provenance.json : {len(events)} clés documentées, {dest.stat().st_size // 1024} Ko")
    for k, v in sorted(stats.items()):
        print(f"   {k}: {v}")

if __name__ == "__main__":
    main()
