#!/usr/bin/env python3
"""Télécharge les JARs listés dans pakku-lock.json. Cache + reprise (sha1)."""
import hashlib, json, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "society-sunlit-valley"
JARS = ROOT / "fr-workspace" / "jars"

def sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> None:
    JARS.mkdir(parents=True, exist_ok=True)
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    lock = json.loads((REPO / "pakku-lock.json").read_text())
    todo, cached, failed = [], 0, []
    for proj in lock["projects"]:
        for f in proj.get("files", []):
            url, name = f.get("url"), f.get("file_name", "")
            if not url or not name.endswith(".jar"):
                continue
            dest, want = JARS / name, (f.get("hashes") or {}).get("sha1")
            if dest.exists() and (not want or sha1(dest) == want):
                cached += 1
                continue
            todo.append((url, dest, want))
    todo = todo[:limit] if limit else todo
    print(f"{cached} en cache, {len(todo)} à télécharger")
    for url, dest, want in todo:
        try:
            req = urllib.request.Request(url.replace(" ", "%20"),
                                         headers={"User-Agent": "sunlit-fr-pipeline"})
            dest.write_bytes(urllib.request.urlopen(req, timeout=120).read())
            if want and sha1(dest) != want:
                dest.unlink()
                failed.append([dest.name, "sha1 mismatch"])
            else:
                print("ok", dest.name)
        except Exception as e:
            failed.append([dest.name, str(e)])
    (JARS / "_failed.json").write_text(json.dumps(failed, ensure_ascii=False, indent=1))
    print(f"échecs: {len(failed)}")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
