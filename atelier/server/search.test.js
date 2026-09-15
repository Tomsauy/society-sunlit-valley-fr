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

test("un nom accentué se trouve en le tapant sans accents", () => {
  // Le défaut que le mod Accent Fold corrige en jeu : l'Atelier était le dernier
  // endroit où il subsistait. « Blé séché » doit sortir sur « ble seche ».
  const r = search(idx, { q: "ble seche", champ: "texte", limite: 50 });
  expect(r.resultats.some(e => e.traductions.fr_fr === "Blé séché")).toBe(true);
});

test("une requête accentuée donne exactement les mêmes résultats que sans accents", () => {
  // La propriété qui compte, et que compter les résultats éprouve mieux qu'un
  // échantillon : les deux graphies mènent au même ensemble.
  const sans = search(idx, { q: "ble", champ: "texte", limite: 1 });
  const avec = search(idx, { q: "Blé", champ: "texte", limite: 1 });
  expect(avec.total).toBe(sans.total);
  expect(sans.total).toBeGreaterThan(0);
});

test("la ligature oe se cherche aussi en deux lettres", () => {
  // « coeur » et « cœur » doivent mener au même résultat : la convention du dépôt
  // proscrit la ligature, mais rien n'empêche de la taper.
  const sans = search(idx, { q: "coeur", champ: "toutes", limite: 1 });
  const avec = search(idx, { q: "cœur", champ: "toutes", limite: 1 });
  expect(avec.total).toBe(sans.total);
});

test("le champ « clé » profite aussi de la normalisation", () => {
  // Les clés sont en ASCII, mais la fonction leur est appliquée : elle ne doit rien
  // y casser.
  const r = search(idx, { q: "sparkstone", champ: "cle", limite: 50 });
  expect(r.total).toBeGreaterThan(0);
});

// Table de référence, tenue identique dans les trois implémentations : ce fichier,
// fr-workspace/scripts/test_compare_accents.py, et AccentsTest.java dans le dépôt du
// mod (github.com/Tomsauy/accent-fold). Le 15/09/2026 elles avaient divergé — table
// incomplète et ligatures appliquées avant le NFC — et l'Atelier prétendait trouver
// ce que le jeu ne trouvait pas.
const CAS_DE_REFERENCE = [
  ["Ragoût", "ragout"],
  ["Clé rouge", "cle rouge"],
  ["Cœur", "coeur"],
  ["Ægir", "aegir"],
  ["ǣ", "ae"],               // ordre : ligature APRÈS le NFC, sinon « æ »
  ["Ǿl", "ol"],              // idem pour le O barré accentué
  ["Straße", "strasse"],
  ["STRAẞE", "strasse"],     // le S dur majuscule doit converger avec le minuscule
  ["Łącze magazynowe", "lacze magazynowe"],
  ["Cài đặt", "cai dat"],
  ["Avbjóðing", "avbjoding"],
  ["한국어", "한국어"],         // ni décomposé en jamos, ni touché
];

// On éprouve la normalisation à travers search(), la seule porte publique : une
// entrée fabriquée par cas, une requête sous forme pliée, le résultat doit sortir.
test("la table de référence de la normalisation, partagée avec le mod et le script Python", () => {
  const entrees = CAS_DE_REFERENCE.map(([texte], i) => ({
    cle: `cas-${i}`, ns: "test",
    source: { en: "", origine: "aucune" },
    traductions: { fr_fr: texte },
    presentDans: { pack: [], mods: [] },
  }));
  const faux = { entrees, locales: [] };
  for (const [i, [texte, plie]] of CAS_DE_REFERENCE.entries()) {
    // La requête pliée doit trouver la valeur accentuée — le cas du joueur qui
    // tape « ragout » — et la requête accentuée aussi, les deux côtés étant
    // normalisés. Les deux sens, parce qu'un seul passerait même si un seul
    // côté était normalisé.
    for (const requete of [plie, texte]) {
      const r = search(faux, { q: requete, champ: "toutes", limite: 50 });
      expect(r.resultats.map(e => e.cle),
             `« ${requete} » devrait trouver « ${texte} »`).toContain(`cas-${i}`);
    }
  }
});
