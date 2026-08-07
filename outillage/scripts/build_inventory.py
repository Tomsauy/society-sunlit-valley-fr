#!/usr/bin/env python3
"""Construit inventaire.json : unités de traduction, skips, stats."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "society-sunlit-valley"
EXT = ROOT / "fr-workspace" / "extracted"
PATCHOULI_FIELDS = {"name", "text", "description", "title", "subtitle", "landing_text"}

def load(p: Path) -> dict:
    return json.loads(p.read_text()) if p.exists() else {}

def pointers(obj, prefix=""):
    """Extrait récursivement les champs textuels patchouli → {pointer: texte}."""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.strip() in PATCHOULI_FIELDS and isinstance(v, str) and v.strip():
                out[f"{prefix}{k}"] = v
            else:
                out.update(pointers(v, f"{prefix}{k}/"))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(pointers(v, f"{prefix}{i}/"))
    return out

def witness_path(ns: str, loc: str, ns_files: dict) -> str | None:
    """Chemin réel du témoin : kubejs du pack en priorité, sinon extrait du JAR."""
    kub = REPO / "kubejs" / "assets" / ns / "lang" / f"{loc}.json"
    if kub.exists():
        return str(kub)
    p = ns_files.get(loc)
    return str(p) if p else None

def main() -> None:
    units, skipped = [], []
    # -- namespaces extraits des jars, fusionnés multi-jars (data + chemin du fichier) --
    ns_map: dict = {}
    ns_paths: dict = {}
    for jar_dir in sorted(EXT.iterdir()) if EXT.exists() else []:
        if not jar_dir.is_dir():
            continue
        for ns_dir in sorted(jar_dir.iterdir()):
            entry = ns_map.setdefault(ns_dir.name, {})
            paths = ns_paths.setdefault(ns_dir.name, {})
            for loc_file in ns_dir.glob("*.json"):
                entry.setdefault(loc_file.stem, {}).update(load(loc_file))
                paths.setdefault(loc_file.stem, loc_file)
    override_ns = set()
    # -- overrides kubejs (prioritaires) --
    for lang_dir in sorted((REPO / "kubejs" / "assets").glob("*/lang")):
        ns = lang_dir.parent.name
        en = load(lang_dir / "en_us.json")
        if ns in {"society", "ftbquestlocalizer"} or not en:
            continue
        override_ns.add(ns)
        wit = {loc: (str(lang_dir / f"{loc}.json") if (lang_dir / f"{loc}.json").exists() else None)
               for loc in ("ko_kr", "zh_cn")}
        units.append({"id": f"override:{ns}", "kind": "override", "namespace": ns,
                      "en": en, "jar_fr_partial": None, "witnesses": wit,
                      "target": f"kubejs/assets/{ns}/lang/fr_fr.json"})
    # -- mods --
    for ns, locs in sorted(ns_map.items()):
        en, fr = locs.get("en_us", {}), locs.get("fr_fr", {})
        todo = {k: v for k, v in en.items() if k not in fr}
        if ns in override_ns:  # les clés overridées sont déjà couvertes par l'unité override
            ov = load(REPO / "kubejs" / "assets" / ns / "lang" / "en_us.json")
            todo = {k: v for k, v in todo.items() if k not in ov}
        if not en:
            continue
        if not todo:
            skipped.append({"namespace": ns, "reason": "fr_complet" if fr else "sans_texte"})
            continue
        kind = "mod_delta" if fr else "mod"
        wit = {loc: witness_path(ns, loc, ns_paths.get(ns, {})) for loc in ("ko_kr", "zh_cn")}
        units.append({"id": f"mod:{ns}", "kind": kind, "namespace": ns,
                      "en": todo, "jar_fr_partial": fr or None, "witnesses": wit,
                      "target": f"kubejs/assets/{ns}/lang/fr_fr.json"})
    # -- society (template ∪ en_us ; valeurs vides du template remplacées par les
    #    displayName réels extraits des scripts KubeJS, cf. society-corrected-en.json) --
    sdir = REPO / "kubejs" / "assets" / "society" / "lang"
    sen = {**load(sdir / "en_us.json"), **load(sdir / "en_us_template.json")}
    corrected = load(ROOT / "fr-workspace" / "society-corrected-en.json")
    for k, v in sen.items():
        if not v.strip() and corrected.get(k, "").strip():
            sen[k] = corrected[k]
    units.append({"id": "society", "kind": "society", "namespace": "society",
                  "en": sen, "jar_fr_partial": None,
                  "witnesses": {"ko_kr": str(sdir / "ko_kr.json"), "zh_cn": str(sdir / "zh_cn.json")},
                  "target": "kubejs/assets/society/lang/fr_fr.json"})
    # -- quêtes --
    qdir = REPO / "kubejs" / "assets" / "ftbquestlocalizer" / "lang"
    units.append({"id": "quests", "kind": "quests", "namespace": "ftbquestlocalizer",
                  "en": load(qdir / "en_us.json"), "jar_fr_partial": None,
                  "witnesses": {"ko_kr": str(qdir / "ko_kr.json"), "zh_cn": str(qdir / "zh_cn.json")},
                  "target": "kubejs/assets/ftbquestlocalizer/lang/fr_fr.json"})
    # -- patchouli --
    for book_dir in sorted((REPO / "patchouli_books").iterdir()):
        if not (book_dir / "en_us").is_dir():
            continue
        for f in sorted((book_dir / "en_us").rglob("*.json")):
            en = pointers(json.loads(f.read_text()))
            if not en:
                continue
            rel = f.relative_to(book_dir / "en_us")
            ko = book_dir / "ko_kr" / rel
            units.append({"id": f"patchouli:{book_dir.name}/{rel}", "kind": "patchouli",
                          "namespace": book_dir.name, "en": en, "jar_fr_partial": None,
                          "witnesses": {"ko_kr": str(ko) if ko.exists() else None, "zh_cn": None},
                          "target": f"patchouli_books/{book_dir.name}/fr_fr/{rel}"})
    failed = load(ROOT / "fr-workspace" / "jars" / "_failed.json") or []
    stats = {"units": len(units),
             "keys_total": sum(len(u["en"]) for u in units),
             "par_kind": {}}
    for u in units:
        k = stats["par_kind"].setdefault(u["kind"], {"units": 0, "keys": 0})
        k["units"] += 1
        k["keys"] += len(u["en"])
    inv = {"units": units, "skipped": skipped,
           "unanalyzed": [f[0] for f in failed], "stats": stats}
    (ROOT / "fr-workspace" / "inventaire.json").write_text(
        json.dumps(inv, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(stats, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
