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

def elaguer(ecrits: set) -> list:
    """Retire les extraits que les JARS présents ne produisent plus.

    Un mod sorti du pack, ou une version qui abandonne une langue, laisse derrière
    lui un extrait que plus rien ne recouvre : le corpus continue alors de servir
    un anglais pour des clés qui n'existent plus. C'est ainsi que 86 clés d'EMI++,
    retiré à la 4.1.5, sont restées visibles dans l'Atelier comme des lacunes de
    traduction — alors que leur français avait été supprimé avec le mod.
    """
    retires = []
    for f in sorted(OUT.rglob("*.json")):
        if f not in ecrits:
            f.unlink()
            retires.append(f.relative_to(OUT))
    # En partant des feuilles, un dossier vidé libère son parent à son tour.
    for d in sorted((d for d in OUT.rglob("*") if d.is_dir()), reverse=True):
        if not any(d.iterdir()):
            d.rmdir()
    return retires


def main() -> None:
    count, all_failures, ecrits = 0, [], set()
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
                ecrits.add(dest)
                count += 1
    retires = elaguer(ecrits)
    print(f"{count} fichiers lang extraits")
    if retires:
        print(f"{len(retires)} extraits périmés retirés (JAR disparu ou langue abandonnée) :")
        for f in retires[:20]:
            print("   ", f)
        if len(retires) > 20:
            print(f"    … et {len(retires) - 20} autres")
    if all_failures:
        print(f"ILLISIBLES ({len(all_failures)}) — à examiner, un mod entier peut manquer :")
        for f in all_failures:
            print("   ", f)

if __name__ == "__main__":
    main()
