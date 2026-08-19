import { test, expect } from "vitest";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { readPack } from "./read-pack.js";

const pack = readPack();

test("lit tous les namespaces du pack", () => {
  expect(pack.size).toBeGreaterThan(250);
  expect(pack.has("society")).toBe(true);
  expect(pack.has("brewery")).toBe(true);
});

test("society a le français et le coréen", () => {
  const s = pack.get("society");
  expect(s.locales.get("fr_fr")["item.society.sparkstone"]).toBe("Sparkstone");
  expect(s.locales.has("ko_kr")).toBe(true);
});

test("en_us_template n'est pas traité comme une locale", () => {
  expect(pack.get("society").locales.has("en_us_template")).toBe(false);
});

test("chemin du fichier conservé pour l'écriture", () => {
  expect(pack.get("brewery").fichiers.get("fr_fr")).toMatch(/kubejs\/assets\/brewery\/lang\/fr_fr\.json$/);
});

test("un fichier illisible même après tolérance aux commentaires est signalé, pas ignoré", () => {
  const tmp = mkdtempSync(join(tmpdir(), "read-pack-illisible-"));
  try {
    const dir = join(tmp, "kubejs/assets/faux/lang");
    mkdirSync(dir, { recursive: true });
    // JSON tronqué : aucun commentaire à retirer, reste invalide après tolérance.
    writeFileSync(join(dir, "fr_fr.json"), '{"a": "b"');
    writeFileSync(join(dir, "en_us.json"), '{"a": "b"}');

    const p = readPack(tmp);
    const chemin = join(dir, "fr_fr.json");

    expect(p.illisibles).toContain(chemin);
    expect(p.get("faux").locales.has("fr_fr")).toBe(false);
    expect(p.get("faux").locales.has("en_us")).toBe(true);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

// Le vrai défaut corrigé ici : un `pack` absent du disque (dépôt qui ne l'a jamais cloné,
// configuration qui pointe à côté) faisait lever readdirSync(assets) — une ENOENT non
// rattrapée qui faisait tomber /api/sante ET la vue Clés en 500, avant même d'atteindre
// le moindre fichier. Un résultat vide et un signalement dans `manquantes`, jamais une
// exception — et surtout pas confondu avec `illisibles` (fichier PRÉSENT mais corrompu) :
// il n'y a ici aucun fichier à lire.
test("un pack absent du disque ne lève pas — résultat vide, signalé dans manquantes", () => {
  const tmp = mkdtempSync(join(tmpdir(), "read-pack-absent-"));
  rmSync(tmp, { recursive: true, force: true }); // le dossier lui-même n'existe pas
  const p = readPack(tmp);
  expect(p.size).toBe(0);
  expect(p.illisibles).toEqual([]);
  expect(p.manquantes).toHaveLength(1);
  expect(p.manquantes[0]).toContain(tmp);
});
