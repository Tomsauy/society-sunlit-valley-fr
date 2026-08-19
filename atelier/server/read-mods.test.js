import { test, expect } from "vitest";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { readMods } from "./read-mods.js";

const mods = readMods();

test("lit les langues des mods extraits", () => {
  expect(mods.size).toBeGreaterThan(200);
  expect(mods.get("create").locales.has("en_us")).toBe(true);
});

test("la version du mod vient du nom du dossier", () => {
  expect(mods.get("create").jar).toMatch(/^create-/);
});

test("vintagedelight est présent — il manquait avant la correction de l'extracteur", () => {
  expect(mods.get("vintagedelight").locales.get("en_us")["block.vintagedelight.cheese_mold"])
    .toBe("Cheese Mold");
});

test("jar suit le dernier contributeur pour un namespace fusionné (flywheel : create + ponderjs)", () => {
  const fw = mods.get("flywheel");
  expect(fw.jars).toEqual(expect.arrayContaining(["create-1.20.1-6.0.8", "ponderjs-1.20.1-2.1.0"]));
  expect(fw.jars.length).toBe(2);
  // cohérent avec la fusion des clés : le dernier jar traité l'emporte pour le contenu comme pour l'étiquette
  expect(fw.jar).toBe(fw.jars[fw.jars.length - 1]);
});

test("un fichier illisible même après tolérance aux commentaires est signalé, pas ignoré", () => {
  const tmp = mkdtempSync(join(tmpdir(), "read-mods-illisible-"));
  try {
    const dir = join(tmp, "faux-1.0.0", "faux");
    mkdirSync(dir, { recursive: true });
    // JSON tronqué : aucun commentaire à retirer, reste invalide après tolérance.
    writeFileSync(join(dir, "fr_fr.json"), '{"a": "b"');
    writeFileSync(join(dir, "en_us.json"), '{"a": "b"}');

    const m = readMods(tmp);
    const chemin = join(dir, "fr_fr.json");

    expect(m.illisibles).toContain(chemin);
    expect(m.get("faux").locales.has("fr_fr")).toBe(false);
    expect(m.get("faux").locales.has("en_us")).toBe(true);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

// Même défaut que read-pack.js, pour EXTRACTED : un environnement qui n'a jamais extrait
// les JARs (le cas courant d'un dépôt publié — fr-workspace/extracted/ n'est pas suivi
// par git) faisait lever readdirSync(extracted). Résultat vide, signalé dans
// `manquantes`, jamais une exception.
test("des langues extraites absentes du disque ne lèvent pas — résultat vide, signalé dans manquantes", () => {
  const tmp = mkdtempSync(join(tmpdir(), "read-mods-absent-"));
  rmSync(tmp, { recursive: true, force: true });
  const m = readMods(tmp);
  expect(m.size).toBe(0);
  expect(m.illisibles).toEqual([]);
  expect(m.manquantes).toHaveLength(1);
  expect(m.manquantes[0]).toContain(tmp);
});

test("une racine qui désigne un fichier est signalée, pas fatale", () => {
  // Un ATELIER_EXTRACTED mal configuré pointant sur un fichier passait `existsSync`
  // puis levait ENOTDIR sur readdirSync : /api/sante et la vue Clés retombaient en 500,
  // exactement le défaut que le signalement des sources absentes devait supprimer.
  const d = mkdtempSync(join(tmpdir(), "atelier-mods-"));
  const f = join(d, "pas-un-dossier.txt");
  writeFileSync(f, "coucou");
  const r = readMods(f);
  expect(r.size).toBe(0);
  expect(r.manquantes).toHaveLength(1);
  expect(r.manquantes[0]).toContain("ATELIER_EXTRACTED");
  rmSync(d, { recursive: true, force: true });
});
