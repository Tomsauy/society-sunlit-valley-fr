import { test, expect } from "vitest";
import { buildKeyIndex } from "./index-build.js";
import { search } from "./search.js";

const idx = buildKeyIndex();

test("recherche dans le texte français", () => {
  const r = search(idx, { q: "houblon", champ: "texte", limite: 50 });
  expect(r.total).toBeGreaterThan(0);
  expect(r.resultats.some(e => e.cle === "item.brewery.hop_trellis_seed")).toBe(true);
});

test("recherche dans la clé", () => {
  const r = search(idx, { q: "sparkstone", champ: "cle", limite: 50 });
  expect(r.resultats.every(e => e.cle.toLowerCase().includes("sparkstone"))).toBe(true);
});

test("recherche toutes langues trouve via le coréen", () => {
  const r = search(idx, { q: "홉 씨앗", champ: "toutes", limite: 20 });
  expect(r.resultats.some(e => e.cle === "item.brewery.hop_trellis_seed")).toBe(true);
});

test("filtre par mod", () => {
  const r = search(idx, { ns: "brewery", limite: 500 });
  expect(r.resultats.every(e => e.ns === "brewery")).toBe(true);
});

test("filtre par origine de l'anglais", () => {
  const r = search(idx, { origine: "aucune", limite: 10 });
  expect(r.resultats.every(e => e.source.origine === "aucune")).toBe(true);
});

test("pagination", () => {
  const p1 = search(idx, { limite: 10, offset: 0 });
  const p2 = search(idx, { limite: 10, offset: 10 });
  expect(p1.resultats[0].id).not.toBe(p2.resultats[0].id);
  expect(p1.total).toBe(p2.total);
});

test("limite non numérique retombe sur la valeur par défaut plutôt que de vider silencieusement la page", () => {
  const parDefaut = search(idx, { offset: 0 });
  const avecLimiteInvalide = search(idx, { limite: "abc", offset: 0 });
  expect(avecLimiteInvalide.resultats.length).toBe(parDefaut.resultats.length);
  expect(avecLimiteInvalide.total).toBe(parDefaut.total);
});

test("limite négative ne renvoie pas presque tout l'index", () => {
  const r = search(idx, { limite: -5, offset: 0 });
  expect(r.resultats.length).toBe(100); // retombe sur la limite par défaut
});

test("offset négatif retombe sur 0 plutôt que de compter depuis la fin", () => {
  const avecOffsetInvalide = search(idx, { offset: -10, limite: 5 });
  const depuisLeDebut = search(idx, { offset: 0, limite: 5 });
  expect(avecOffsetInvalide.resultats.map(e => e.id)).toEqual(depuisLeDebut.resultats.map(e => e.id));
});
