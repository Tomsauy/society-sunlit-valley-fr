import { test, expect } from "vitest";
import { buildKeyIndex } from "./index-build.js";
import { search } from "./search.js";

const idx = buildKeyIndex();

// Ancrage de non-régression : quatre lacunes réelles et connues (espagnol, coréen et
// portugais les ont, le français non), toutes dans le namespace "society". Si ce nombre
// bouge, c'est que le filtre — ou les données sources — a changé de comportement.
test("avec espagnol, sans français, portée pack : les lacunes réelles", () => {
  const r = search(idx, { avec: ["es_es"], sans: ["fr_fr"], portee: "pack", limite: 500 });
  expect(r.total).toBe(4);
  expect(r.resultats.every(e => e.ns === "society")).toBe(true);
  expect(r.resultats.map(e => e.cle).sort()).toEqual([
    "block.society.diamond_sprinkler",
    "jei.society.category.furniture_catalog",
    "society.furniture_catalog.give_me_coin",
    "tooltip.society.furniture_catalog",
  ].sort());
});

// La portée qualifie à la fois « avec » et « sans » : élargir à pack_et_mods ajoute des
// clés à la clause avec (le jar traduit plus que le pack) mais en retire aussi à la
// clause sans (une clé traduite dans le jar n'est plus « sans » cette langue). Le sens
// du total dépend donc de la langue demandée — il n'y a pas de relation d'ordre fixe
// entre les deux portées, seulement la certitude qu'elles mesurent des choses différentes.
test("la portée change ce que « présent » veut dire, sans ordre fixe entre les deux", () => {
  for (const langue of ["es_es", "ko_kr"]) {
    const pack = search(idx, { avec: [langue], sans: ["fr_fr"], portee: "pack", limite: 5000 });
    const packEtMods = search(idx, { avec: [langue], sans: ["fr_fr"], portee: "pack_et_mods", limite: 5000 });
    expect(pack.total).toBeGreaterThan(0);
    expect(packEtMods.total).toBeGreaterThan(0);
    expect(packEtMods.total).not.toBe(pack.total);
  }
});

test("plusieurs langues en « ou » dans la clause avec", () => {
  const es = search(idx, { avec: ["es_es"], sans: ["fr_fr"], portee: "pack", limite: 500 }).total;
  const deux = search(idx, { avec: ["es_es", "pt_br"], sans: ["fr_fr"], portee: "pack", limite: 500 }).total;
  expect(deux).toBeGreaterThanOrEqual(es);
});

test("sans clause, tout passe", () => {
  const r = search(idx, { avec: [], sans: [], limite: 10 });
  expect(r.total).toBe(idx.entrees.length);
});

// Correctif : « avec anglais, sans français » — l'exemple même qui justifie ce filtre
// dans le document de conception — était inexprimable (en_us absent de idx.locales et
// de presentDans). Ancrage de non-régression sur le corpus réel : 0 est le résultat
// CORRECT, pas un signe de panne — mesuré, toute clé sans français (8822, voir
// DetailPanel.svelte) est une clé sans aucune source anglaise (origine "aucune"), donc
// la couverture française est complète pour tout ce qui a un anglais. Vérifié sur une
// langue plus rare (japonais) pour prouver que le mécanisme n'est pas juste "toujours
// zéro".
test("avec anglais, sans français : 0 sur le corpus réel (couverture française complète), mécanisme vérifié sur le japonais", () => {
  const avecEnSansFr = search(idx, { avec: ["en_us"], sans: ["fr_fr"], portee: "pack_et_mods", limite: 5 });
  expect(avecEnSansFr.total).toBe(0);
  const avecEnSansJa = search(idx, { avec: ["en_us"], sans: ["ja_jp"], portee: "pack_et_mods", limite: 5 });
  expect(avecEnSansJa.total).toBeGreaterThan(0);
});
