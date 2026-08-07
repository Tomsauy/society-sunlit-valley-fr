#!/usr/bin/env python3
"""Recense les items/blocs créés par les scripts KubeJS du pack dont le nom est
auto-dérivé de l'identifiant (aucune clé de lang nulle part) → non traduits en jeu.

KubeJS génère `item.<ns>.<path>` / `block.<ns>.<path>` et, faute d'entrée lang,
affiche un title-case de l'identifiant ("hop_trellis_seed" → "Hop Trellis Seed").
"""
import json, re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "society-sunlit-valley"
WS = ROOT / "fr-workspace"

CREATE = re.compile(r"""\.create\(\s*["'`]([a-z0-9_]+):([a-z0-9_/]+)["'`]\s*(?:,\s*["'`]([a-z_]+)["'`])?""")

def title(path: str) -> str:
    return " ".join(w.capitalize() for w in path.split("/")[-1].split("_"))

def main() -> None:
    # 1. tous les identifiants créés par les scripts
    created = defaultdict(set)  # ns -> {(kind, path)}
    for js in (REPO / "kubejs" / "startup_scripts").rglob("*.js"):
        src = js.read_text(errors="ignore")
        # type de l'event : block ou item selon le fichier/appel
        is_block_file = re.search(r"BlockEvents\.modification|StartupEvents\.registry\(\s*[\"'`]block", src) is not None
        for m in CREATE.finditer(src):
            ns, path, typ = m.group(1), m.group(2), m.group(3)
            if typ in ("crop", "cardinal", "basic", "detector", "wall", "slab", "stairs", "fence") or is_block_file:
                created[ns].add(("block", path))
                if typ == "crop":
                    created[ns].add(("item", path + "_seed"))
            else:
                created[ns].add(("item", path))

    # 2. clés déjà connues (JAR en_us, overrides EN du pack, nos FR)
    known = set()
    for f in (WS / "extracted").glob("*/*/en_us.json"):
        try:
            known |= set(json.loads(f.read_text()))
        except Exception:
            pass
    for f in (REPO / "kubejs" / "assets").glob("*/lang/*.json"):
        try:
            known |= set(json.loads(f.read_text()))
        except Exception:
            pass

    missing = []
    for ns, entries in sorted(created.items()):
        for kind, path in sorted(entries):
            key = f"{kind}.{ns}.{path.replace('/', '.')}"
            if key not in known:
                missing.append({"key": key, "namespace": ns, "en": title(path)})
    out = WS / "kubejs-derived-names.json"
    out.write_text(json.dumps(missing, ensure_ascii=False, indent=1) + "\n")
    per_ns = defaultdict(int)
    for m in missing:
        per_ns[m["namespace"]] += 1
    print(f"{len(missing)} noms auto-dérivés sans clé de lang")
    for ns, n in sorted(per_ns.items(), key=lambda kv: -kv[1]):
        print(f"  {ns}: {n}")

if __name__ == "__main__":
    main()
