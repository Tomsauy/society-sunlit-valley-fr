#!/usr/bin/env python3
"""Extrait assets/<ns>/lang/<locale>.json de chaque JAR (y compris jarjar imbriqués)."""
import io, json, re, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JARS = ROOT / "fr-workspace" / "jars"
OUT = ROOT / "fr-workspace" / "extracted"
# Aucune liste de langues figée : toute locale au format xx_yy est extraite,
# y compris celles ajoutées par une future mise à jour d'un mod.
PAT = re.compile(r"^assets/([^/]+)/lang/([a-z]{2}_[a-z]{2})\.json$")
COMMENT = re.compile(r'(^|[^:"])//[^"\n]*$', re.M)

def parse_lang(raw: bytes):
    """Minecraft tolère les commentaires // dans les fichiers lang ; json non.
    On réessaie après les avoir retirés plutôt que d'ignorer le fichier."""
    txt = raw.decode("utf-8-sig", errors="replace")
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        pass
    try:
        return json.loads(COMMENT.sub(r"\1", txt))
    except json.JSONDecodeError:
        return None

def harvest(zf: zipfile.ZipFile, store: dict, failures: list) -> None:
    for name in zf.namelist():
        m = PAT.match(name)
        if m:
            data = parse_lang(zf.read(name))
            if data is None:
                failures.append(name)
                continue
            if isinstance(data, dict) and data:
                store.setdefault(m.group(1), {}).setdefault(m.group(2), {}).update(
                    {k: v for k, v in data.items() if isinstance(v, str)})
        elif name.startswith("META-INF/jarjar/") and name.endswith(".jar"):
            try:
                harvest(zipfile.ZipFile(io.BytesIO(zf.read(name))), store, failures)
            except Exception:
                pass

def main() -> None:
    count, all_failures = 0, []
    for jar in sorted(JARS.glob("*.jar")):
        store: dict = {}
        failures: list = []
        try:
            harvest(zipfile.ZipFile(jar), store, failures)
        except zipfile.BadZipFile:
            print("BAD ZIP:", jar.name)
            continue
        for f in failures:
            all_failures.append(f"{jar.stem}:{f}")
        for ns, locs in store.items():
            for loc, data in locs.items():
                dest = OUT / jar.stem / ns / f"{loc}.json"
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
                count += 1
    print(f"{count} fichiers lang extraits")
    if all_failures:
        print(f"ILLISIBLES ({len(all_failures)}) — à examiner, un mod entier peut manquer :")
        for f in all_failures:
            print("   ", f)

if __name__ == "__main__":
    main()
