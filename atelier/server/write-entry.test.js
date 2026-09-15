// site/server/write-entry.test.js
import { mkdtempSync, writeFileSync, readFileSync, existsSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test, expect, afterEach } from "vitest";
import { writeLangEntry, validerValeur } from "./write-entry.js";

let dossier;
const fichierTest = (contenu) => {
  dossier = mkdtempSync(join(tmpdir(), "atelier-"));
  const f = join(dossier, "fr_fr.json");
  writeFileSync(f, JSON.stringify(contenu, null, 2) + "\n");
  return f;
};
afterEach(() => dossier && rmSync(dossier, { recursive: true, force: true }));

test("écrit une valeur et garde les clés triées", () => {
  const f = fichierTest({ "b.cle": "deux", "a.cle": "un" });
  expect(writeLangEntry({ fichier: f, cle: "c.cle", valeur: "trois" }).ok).toBe(true);
  const brut = readFileSync(f, "utf8");
  expect(JSON.parse(brut)["c.cle"]).toBe("trois");
  expect(brut.indexOf('"a.cle"')).toBeLessThan(brut.indexOf('"b.cle"'));
  expect(brut.endsWith("\n")).toBe(true);
});

test("crée le fichier et le dossier manquants (mod pas encore couvert par le pack)", () => {
  dossier = mkdtempSync(join(tmpdir(), "atelier-"));
  const f = join(dossier, "nouveau_mod/lang/fr_fr.json");
  expect(existsSync(f)).toBe(false);
  const r = writeLangEntry({ fichier: f, cle: "item.mod.x", valeur: "Un objet" });
  expect(r.ok).toBe(true);
  expect(JSON.parse(readFileSync(f, "utf8"))["item.mod.x"]).toBe("Un objet");
});

test("refuse d'écrire dans un fichier qui contient des commentaires (correction B)", () => {
  dossier = mkdtempSync(join(tmpdir(), "atelier-"));
  const f = join(dossier, "fr_fr.json");
  const avant = '{\n  "a.cle": "un",\n  //commentaire à préserver\n  "b.cle": "deux"\n}\n';
  writeFileSync(f, avant);
  const r = writeLangEntry({ fichier: f, cle: "c.cle", valeur: "trois" });
  expect(r.ok).toBe(false);
  expect(r.erreur).toMatch(/commentaire/i);
  expect(readFileSync(f, "utf8")).toBe(avant); // rien n'a été écrit, le commentaire survit
});

test("refuse un placeholder perdu", () => {
  const pb = validerValeur({ en: "Gives %s coins", fr: "Donne des pièces", cle: "x.y.z" });
  expect(pb.length).toBeGreaterThan(0);
  expect(pb[0]).toMatch(/placeholder/i);
});

// --- La politique d'accents, abrogée (DECISION-ACCENTS.md, quatrième épisode) ---
//
// Ces quatre cas figeaient la règle inverse : ils refusaient un accent sur un nom
// cherchable, et l'Atelier répondait 422 à qui corrigeait « Blé ». Le mod Accent Fold
// replie les diacritiques dans les dix-sept cibles de recherche, Refined Storage compris ;
// plus aucun nom n'a à s'écrire sans accents. Ils vérifient désormais l'acceptation.
test("accepte un accent sur un nom d'objet cherchable", () => {
  expect(validerValeur({ en: "Wheat", fr: "Blé", cle: "item.mod.wheat" })).toEqual([]);
});

test("accepte un accent sur les trois préfixes que la règle visait (item., block., entity.)", () => {
  for (const cle of ["item.mod.wheat", "block.mod.hay", "entity.mod.cow"])
    expect(validerValeur({ en: "Wheat", fr: "Blé", cle })).toEqual([]);
});

test("accepte un accent sur une description (clé à 4 segments)", () => {
  expect(validerValeur({ en: "Aged well", fr: "Très bien vieilli", cle: "item.mod.x.description" }))
    .toEqual([]);
});

test("accepte une valeur correcte", () => {
  expect(validerValeur({ en: "Gives %s coins", fr: "Donne %s pièces", cle: "tooltip.mod.x" }))
    .toEqual([]);
});

// L'ancienne règle ne visait que les libellés « courts » — au plus six mots anglais, sans
// ponctuation finale — et ne comptait que les clés à trois segments. Aucune de ces formes
// ne doit plus rien déclencher : l'acceptation ne dépend ni de la longueur de l'anglais,
// ni du nombre de segments de la clé.
test("accepte un accent quelle que soit la forme de l'anglais (libellé court ou phrase)", () => {
  expect(validerValeur({ en: "Wheat", fr: "Un bon vieux blé.", cle: "item.mod.wheat" })).toEqual([]);
  expect(validerValeur({ en: "This is a wheat-like grain.", fr: "Blé", cle: "item.mod.wheat" })).toEqual([]);
});

// --- Divergences avec fr-workspace/scripts/validate_translation.py (correction A) ---

test("règle untranslated : une traduction identique à l'anglais est une erreur", () => {
  const pb = validerValeur({ en: "Wooden Plank", fr: "Wooden Plank", cle: "block.mod.plank" });
  expect(pb.length).toBeGreaterThan(0);
  expect(pb.some((p) => /identique|non traduit/i.test(p))).toBe(true);
});

test("règle should_be_empty : anglais vide ou blanc, français vide accepté", () => {
  expect(validerValeur({ en: "", fr: "", cle: "advancement.mod.x.title" })).toEqual([]);
  expect(validerValeur({ en: "   ", fr: "", cle: "advancement.mod.x.title" })).toEqual([]);
});

test("règle should_be_empty : anglais vide ou blanc mais français renseigné est un refus (le brief interdisait l'inverse)", () => {
  const pb = validerValeur({ en: "", fr: "Quelque chose", cle: "advancement.mod.x.title" });
  expect(pb.length).toBeGreaterThan(0);
});

test("origine « aucune » (en absent, pas seulement blanc) : une valeur française est acceptée, Python ne voit jamais cette clé", () => {
  expect(validerValeur({ en: null, fr: "Un objet créé par script", cle: "item.mod.script_item" }))
    .toEqual([]);
});

test("origine « aucune » : une valeur française vide reste refusée", () => {
  const pb = validerValeur({ en: null, fr: "", cle: "item.mod.script_item" });
  expect(pb.length).toBeGreaterThan(0);
});

// Ces deux cas fermaient une divergence de comptage de mots avec Python — un espace de
// bord dans l'anglais faisait basculer `libelleCourt`, donc la contrainte d'accents, à
// tort. Le comptage a disparu avec la règle ; ce qui reste à garantir est qu'aucune forme
// d'anglais, espaces de bord compris, ne ressuscite un refus sur un nom accentué.
test("un espace de tête dans l'anglais ne déclenche plus rien sur un nom accentué", () => {
  expect(validerValeur({ en: " One Two Three Four Five Six", fr: "Blé", cle: "item.mod.wheat4" }))
    .toEqual([]);
});

test("un espace de fin dans l'anglais ne déclenche plus rien sur un nom accentué", () => {
  expect(validerValeur({ en: "One Two Three Four Five Six ", fr: "Blé", cle: "item.mod.wheat5" }))
    .toEqual([]);
});
