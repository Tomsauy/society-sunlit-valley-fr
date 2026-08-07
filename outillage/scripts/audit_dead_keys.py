#!/usr/bin/env python3
"""Détecte les clés mortes : traduites mais jamais affichées en jeu.

Une clé est VIVANTE si son littéral apparaît dans les fichiers du pack (scripts KubeJS,
données, config) ou dans le JAR du mod de son namespace. Sinon elle peut encore être
composée à l'exécution (KubeJS génère item.<ns>.<path> pour tout objet enregistré,
EveryCompat assemble wood_type + block_type…) : ces cas sont reclassés par famille.
Écrit fr-workspace/dead-keys.json.
"""
import json, re, zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "society-sunlit-valley"
WS = ROOT / "fr-workspace"

# familles composées à l'exécution : la clé n'apparaît jamais en dur
RUNTIME = ("wood_type.", "block_type.", "biome.", "effect.", "enchantment.",
           "subtitles.", "death.", "advancement.", "advancements.", "key.",
           "itemGroup.", "creativetab.", "stackgroup.", "painting.")

def pack_corpus() -> str:
    parts = []
    for sub in ("kubejs", "config", "data", "defaultconfigs", "patchouli_books"):
        base = REPO / sub
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix in (".js", ".json", ".snbt", ".toml", ".txt", ".mcfunction"):
                if "/lang/" in str(p):
                    continue
                try: parts.append(p.read_text(errors="ignore"))
                except Exception: pass
    for p in (REPO / "config" / "ftbquests").rglob("*.snbt"):
        try: parts.append(p.read_text(errors="ignore"))
        except Exception: pass
    return "\n".join(parts)

def ns_to_jars() -> dict:
    m = defaultdict(set)
    ext = WS / "extracted"
    for jar_dir in ext.iterdir() if ext.exists() else []:
        if not jar_dir.is_dir():
            continue
        for ns_dir in jar_dir.iterdir():
            m[ns_dir.name].add(jar_dir.name)
    return m

def jar_text(stem: str, cache: dict) -> str:
    if stem in cache:
        return cache[stem]
    txt = ""
    for jar in (WS / "jars").glob(f"{stem}.jar"):
        try:
            z = zipfile.ZipFile(jar)
            buf = []
            for n in z.namelist():
                if n.endswith("/"):
                    continue
                try: data = z.read(n)
                except Exception: continue
                buf.append(" ".join(s.decode(errors="ignore") for s in re.findall(rb"[ -~]{4,}", data)))
            txt = "\n".join(buf)
        except Exception:
            pass
    cache[stem] = txt
    return txt

def main() -> None:
    orphan_keys = []
    for src in ("orphan-live.json", "orphan-check.json"):
        d = json.loads((WS / src).read_text())
        for ns, keys in d.items():
            for k in keys:
                orphan_keys.append((ns, k))
    corpus = pack_corpus()
    jars = ns_to_jars()
    cache = {}
    live_pack, live_jar, runtime, suspect = [], [], [], []
    for ns, key in orphan_keys:
        if key in corpus:
            live_pack.append({"ns": ns, "key": key}); continue
        found = False
        for stem in jars.get(ns, ()):
            if key in jar_text(stem, cache):
                live_jar.append({"ns": ns, "key": key, "jar": stem}); found = True; break
        if found:
            continue
        if key.startswith(RUNTIME):
            runtime.append({"ns": ns, "key": key})
        else:
            suspect.append({"ns": ns, "key": key})
    out = {"live_pack": live_pack, "live_jar": live_jar, "runtime": runtime, "suspect": suspect}
    (WS / "dead-keys.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"{len(orphan_keys)} clés analysées")
    print(f"  référencées dans le pack      : {len(live_pack)}")
    print(f"  présentes dans le JAR du mod  : {len(live_jar)}")
    print(f"  composées à l'exécution        : {len(runtime)}")
    print(f"  SUSPECTES (introuvables)       : {len(suspect)}")
    per_ns = defaultdict(int)
    for s in suspect:
        per_ns[s["ns"]] += 1
    for ns, n in sorted(per_ns.items(), key=lambda kv: -kv[1]):
        print(f"     {ns}: {n}")

if __name__ == "__main__":
    main()
