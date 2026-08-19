import { test, expect } from "vitest";
import { join } from "node:path";
import { buildKeyIndex } from "./index-build.js";
import { readPack } from "./read-pack.js";
import { readMods } from "./read-mods.js";
import { PACK } from "./paths.js";

const idx = buildKeyIndex();

test("indexe des dizaines de milliers de clés", () => {
  expect(idx.entrees.length).toBeGreaterThan(40000);
});

test("une clé du pack porte son anglais et son français", () => {
  const e = idx.parId.get("lang:society:item.society.sparkstone");
  expect(e.traductions.fr_fr).toBe("Sparkstone");
  expect(e.emplacement.fichier).toMatch(/society\/lang\/fr_fr\.json$/);
});

test("origine jar quand l'anglais vient du mod", () => {
  const e = idx.parId.get("lang:create:block.create.andesite_casing");
  expect(e.source.origine).toBe("jar");
  expect(e.contexte.version).toMatch(/^create-/);
});

test("origine aucune quand aucun anglais n'existe — cas hop_trellis_seed", () => {
  const e = idx.parId.get("lang:brewery:item.brewery.hop_trellis_seed");
  expect(e.source.en).toBe(null);
  expect(e.source.origine).toBe("aucune");
  expect(e.traductions.fr_fr).toBe("Graines de houblon");
  expect(e.traductions.ko_kr).toBeTruthy();
});

test("l'override du pack prime sur l'anglais du jar", () => {
  const e = idx.parId.get("lang:farmersdelight:farmersdelight.advancement.harvest_ropelogged_tomato.desc");
  expect(e.source.origine).toBe("override");
});

test("les locales découvertes couvrent bien plus que les langues du pack", () => {
  expect(idx.locales.length).toBeGreaterThan(50);
  expect(idx.locales).toContain("fr_fr");
  expect(idx.locales).toContain("es_es");
});

// Correctif : l'anglais était exclu des boucles qui alimentent `locales`/`presentDans`,
// rendant /api/locales, le sélecteur « + langue » et le filtre avec/sans incapables de
// le nommer. Il reste hors de `traductions` (c'est la SOURCE, pas une traduction —
// DetailPanel.svelte l'affiche déjà séparément) mais doit apparaître dans `locales` et
// `presentDans`, sur les mêmes conditions que `source.origine` (override → pack,
// jar → mods).
test("l'anglais est nommable (locales, presentDans) mais reste hors de `traductions`", () => {
  expect(idx.locales).toContain("en_us");

  const jar = idx.entrees.find((e) => e.source.origine === "jar");
  expect(jar.presentDans.mods).toContain("en_us");
  expect(jar.traductions.en_us).toBeUndefined();

  const override = idx.entrees.find((e) => e.source.origine === "override");
  expect(override.presentDans.pack).toContain("en_us");
  expect(override.traductions.en_us).toBeUndefined();

  const aucune = idx.entrees.find((e) => e.source.origine === "aucune");
  expect(aucune.presentDans.pack).not.toContain("en_us");
  expect(aucune.presentDans.mods).not.toContain("en_us");
});

test("illisibles agrège les fichiers illisibles du pack et des mods, dans cet ordre", () => {
  // readPack() et readMods() collectent chacun leur propre `illisibles` ; buildKeyIndex()
  // les regroupe pour que /api/sante n'ait qu'une seule liste à exposer pour tout ce qui a
  // contribué à l'index — c'est le signal qui distingue « aucune décision connue » d'un
  // fichier réellement corrompu.
  const pack = readPack();
  const mods = readMods();
  expect(idx.illisibles).toEqual([...pack.illisibles, ...mods.illisibles]);
});

test("manquantes agrège les racines absentes du pack et des mods — vide sur le corpus réel", () => {
  // Même principe que illisibles ci-dessus, pour une racine absente (PACK/EXTRACTED)
  // plutôt qu'un fichier corrompu — voir read-pack.js/read-mods.js. Sur le corpus réel,
  // les deux racines existent : la liste agrégée doit donc rester vide.
  expect(idx.manquantes).toEqual([]);
});

test("manquantes signale un pack absent sans lever, avec le message de readPack()", () => {
  const pack = readPack("/chemin/qui-n-existe-vraiment-pas");
  expect(pack.manquantes).toHaveLength(1);
  expect(pack.illisibles).toEqual([]);
});

test("parCle regroupe les entrées qui partagent une clé nue entre namespaces — cas réel jeed/windswept", () => {
  // provenance.json indexe par clé nue, sans namespace : quand deux mods choisissent le
  // même identifiant, une seule entrée de provenance existe pour les deux. parCle est le
  // signal qui permet de détecter cette ambiguïté depuis l'index des clés lui-même.
  const groupe = idx.parCle.get("effect.windswept.thorns.description");
  expect(groupe.map(e => e.ns).sort()).toEqual(["jeed", "windswept"]);
  expect(new Set(groupe.map(e => e.source.en)).size).toBe(2);
});

test("emplacement.fichier n'est jamais null — un namespace côté mods sans fichier côté pack reçoit quand même un chemin cible", () => {
  // On cherche un vrai namespace présent chez les mods mais absent du pack :
  // c'est justement le cas où le brief original renvoyait null.
  const pack = readPack();
  const mods = readMods();
  const nsSansPack = [...mods.keys()].find((ns) => !pack.has(ns));
  expect(nsSansPack).toBeTruthy();

  const attendu = join(PACK, "kubejs/assets", nsSansPack, "lang/fr_fr.json");
  const entreeDuNs = idx.entrees.find((entree) => entree.ns === nsSansPack);
  expect(entreeDuNs).toBeTruthy();
  expect(entreeDuNs.emplacement.fichier).toBe(attendu);

  // Plus généralement, aucune entrée de l'index n'a un emplacement.fichier nul.
  for (const entree of idx.entrees) {
    expect(entree.emplacement.fichier).not.toBe(null);
  }
});
