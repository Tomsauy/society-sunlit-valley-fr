#!/usr/bin/env python3
"""État réel des workflows de traduction, toutes sessions confondues.
Usage : python3 fr-workspace/scripts/wf_status.py [--watch]
--watch : rafraîchit toutes les 10 s (Ctrl-C pour quitter)"""
import json, os, sys, time
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
OUT = Path(__file__).resolve().parents[1] / "out"

def main() -> None:
    runs = {}
    for j in PROJECTS.glob("-Users-thomas-IAPersoProjects-SunlitValley*/*/subagents/workflows/*/journal.jsonl"):
        run_id = j.parent.name
        r = runs.setdefault(run_id, {"started": set(), "done": set(), "activity": 0})
        for line in j.read_text().splitlines():
            try:
                rec = json.loads(line)
            except Exception:
                continue
            aid = rec.get("agentId", "")
            if rec.get("type") == "started":
                r["started"].add(aid)
            elif rec.get("type") == "result":
                r["done"].add(aid)
        for t in j.parent.glob("agent-*.jsonl"):
            r["activity"] = max(r["activity"], t.stat().st_mtime)
            aid = t.stem.replace("agent-", "")
            if aid in r["started"] and aid not in r["done"] and time.time() - t.stat().st_mtime < 180:
                r.setdefault("actifs", []).append(
                    f"{aid[:8]} ({sum(1 for _ in t.open())} évts, {int(time.time() - t.stat().st_mtime)}s)")
    now = time.time()
    for run_id, r in sorted(runs.items(), key=lambda kv: -kv[1]["activity"]):
        ns, nd = len(r["started"]), len(r["done"])
        age = int(now - r["activity"])
        if nd >= ns and ns > 0:
            state = "terminé"
        elif age < 180:
            state = f"ACTIF ({ns - nd} agent(s) en cours, dernière activité il y a {age}s)"
        else:
            state = f"bloqué ? (dernière activité il y a {age // 60} min)"
        print(f"{run_id}: {nd}/{ns} agents terminés — {state}")
        for a in r.get("actifs", []):
            print(f"    · agent {a}")
    outs = sorted(OUT.glob("*.json"), key=lambda p: -p.stat().st_mtime)
    print(f"\nsorties dans fr-workspace/out/ : {len(outs)}")
    for p in outs[:5]:
        print(f"  {p.name} (il y a {int(now - p.stat().st_mtime)}s)")

if __name__ == "__main__":
    if "--watch" in sys.argv:
        while True:
            os.system("clear")
            print(time.strftime("%H:%M:%S"), "— suivi des workflows (Ctrl-C pour quitter)\n")
            main()
            time.sleep(10)
    else:
        main()
