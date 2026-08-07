#!/usr/bin/env python3
"""Récupère en_us (client.jar) et fr_fr (assets Mojang) officiels de Minecraft 1.20.1."""
import io, json, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "fr-workspace" / "references"

def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "sunlit-fr-pipeline"})
    return urllib.request.urlopen(req, timeout=180).read()

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    man = json.loads(get("https://launchermeta.mojang.com/mc/game/version_manifest_v2.json"))
    meta = json.loads(get(next(v["url"] for v in man["versions"] if v["id"] == "1.20.1")))
    client = zipfile.ZipFile(io.BytesIO(get(meta["downloads"]["client"]["url"])))
    (OUT / "mc_en_us.json").write_bytes(client.read("assets/minecraft/lang/en_us.json"))
    idx = json.loads(get(meta["assetIndex"]["url"]))
    h = idx["objects"]["minecraft/lang/fr_fr.json"]["hash"]
    (OUT / "mc_fr_fr.json").write_bytes(get(f"https://resources.download.minecraft.net/{h[:2]}/{h}"))
    en = json.loads((OUT / "mc_en_us.json").read_text())
    fr = json.loads((OUT / "mc_fr_fr.json").read_text())
    print(f"vanilla en_us: {len(en)} clés, fr_fr: {len(fr)} clés")

if __name__ == "__main__":
    main()
