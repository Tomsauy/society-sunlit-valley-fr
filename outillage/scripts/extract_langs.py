#!/usr/bin/env python3
"""Extrait assets/<ns>/lang/<locale>.json de chaque JAR (y compris jarjar imbriqués)."""
import io, json, re, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JARS = ROOT / "fr-workspace" / "jars"
OUT = ROOT / "fr-workspace" / "extracted"
LOCALES = {"en_us", "fr_fr", "ko_kr", "zh_cn", "pt_br", "th_th", "es_es"}
PAT = re.compile(r"^assets/([^/]+)/lang/([a-z]{2}_[a-z]{2})\.json$")

def harvest(zf: zipfile.ZipFile, store: dict) -> None:
    for name in zf.namelist():
        m = PAT.match(name)
        if m and m.group(2) in LOCALES:
            try:
                data = json.loads(zf.read(name).decode("utf-8-sig"))
            except Exception:
                continue
            if isinstance(data, dict) and data:
                store.setdefault(m.group(1), {}).setdefault(m.group(2), {}).update(
                    {k: v for k, v in data.items() if isinstance(v, str)})
        elif name.startswith("META-INF/jarjar/") and name.endswith(".jar"):
            try:
                harvest(zipfile.ZipFile(io.BytesIO(zf.read(name))), store)
            except Exception:
                pass

def main() -> None:
    count = 0
    for jar in sorted(JARS.glob("*.jar")):
        store: dict = {}
        try:
            harvest(zipfile.ZipFile(jar), store)
        except zipfile.BadZipFile:
            print("BAD ZIP:", jar.name)
            continue
        for ns, locs in store.items():
            for loc, data in locs.items():
                dest = OUT / jar.stem / ns / f"{loc}.json"
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
                count += 1
    print(f"{count} fichiers lang extraits")

if __name__ == "__main__":
    main()
