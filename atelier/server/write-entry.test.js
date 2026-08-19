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

test("refuse un accent sur un nom d'objet cherchable", () => {
  const pb = validerValeur({ en: "Wheat", fr: "Blé", cle: "item.mod.wheat" });
  expect(pb[0]).toMatch(/accent/i);
});

test("accepte un accent sur une description (clé à 4 segments)", () => {
  expect(validerValeur({ en: "Aged well", fr: "Très bien vieilli", cle: "item.mod.x.description" }))
    .toEqual([]);
});

test("accepte une valeur correcte", () => {
  expect(validerValeur({ en: "Gives %s coins", fr: "Donne %s pièces", cle: "tooltip.mod.x" }))
    .toEqual([]);
});

// --- Divergences avec fr-workspace/scripts/validate_translation.py (correction A) ---

test("is_name se calcule sur l'anglais, pas sur le français (1/2) : anglais court, français devenu une phrase reste soumis à la contrainte", () => {
  // En français, "Un bon vieux blé." est une phrase (>6 mots ou ponctuation finale n'entre
  // même pas en jeu ici : elle finit par un point) : un validateur qui jugerait sur le
  // français laisserait passer l'accent. Python (qui fait foi) juge sur l'anglais "Wheat",
  // court : la contrainte s'applique toujours.
  const pb = validerValeur({ en: "Wheat", fr: "Un bon vieux blé.", cle: "item.mod.wheat" });
  expect(pb.some((p) => /accent/i.test(p))).toBe(true);
});

test("is_name se calcule sur l'anglais, pas sur le français (2/2) : anglais déjà une phrase, français court et accentué, aucune contrainte", () => {
  // Ici l'anglais est une phrase (se termine par un point) : is_name est faux côté Python
  // même si la traduction, elle, est un unique mot accentué. Un validateur qui jugerait sur
  // le français aurait refusé "Blé" à tort.
  const pb = validerValeur({ en: "This is a wheat-like grain.", fr: "Blé", cle: "item.mod.wheat" });
  expect(pb.some((p) => /accent/i.test(p))).toBe(false);
});

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

// Divergence relevée en revue, absente des 24 cas confrontés au départ : Python compte
// les mots avec v.split() (sans argument), qui ignore nativement les espaces de bord ;
// en.split(/\s+/) sur une chaîne non trimée ajoute un élément vide par espace de tête/fin,
// ce qui peut faire dépasser 6 et basculer estNom à faux à tort — laissant passer un
// accent que Python aurait refusé. Dormant sur le corpus actuel (aucune des 314 valeurs
// anglaises à espaces de bord n'est une clé item./block./entity. à 3 segments), mais
// exactement la classe d'erreur que « un test par divergence » visait à fermer.
test("un espace de tête dans l'anglais ne doit pas faire passer un nom à 6 mots pour une phrase (libelleCourt)", () => {
  const pb = validerValeur({ en: " One Two Three Four Five Six", fr: "Blé", cle: "item.mod.wheat4" });
  expect(pb.some((p) => /accent/i.test(p))).toBe(true);
});

test("un espace de fin dans l'anglais ne doit pas faire passer un nom à 6 mots pour une phrase (libelleCourt)", () => {
  const pb = validerValeur({ en: "One Two Three Four Five Six ", fr: "Blé", cle: "item.mod.wheat5" });
  expect(pb.some((p) => /accent/i.test(p))).toBe(true);
});
