// site/server/read-books.test.js
import { test, expect } from "vitest";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { readBooks } from "./read-books.js";

// readBooks() renvoie { livres, illisibles }, aligné sur readMeta()/readQuests()
// (voir le commentaire en tête de read-books.js) — pas un tableau portant `.illisibles`
// accroché dessus.
const { livres, illisibles } = readBooks();

test("deux livres", () => {
  expect(livres.map((l) => l.id).sort()).toEqual(["almanac", "fish_finder"]);
});

test("l'almanach a six catégories nommées en français", () => {
  const a = livres.find((l) => l.id === "almanac");
  expect(a.categories).toHaveLength(6);
  expect(a.categories.map((c) => c.nom)).toContain("Cultures");
});

// Correction D du brief : une catégorie porte name ET description, toutes deux
// traduites. "Cultures" (patchouli:crops) porte la sienne dans les quatre langues.
test("les catégories portent aussi leur description, dans plusieurs langues", () => {
  const a = livres.find((l) => l.id === "almanac");
  const cultures = a.categories.find((c) => c.nom === "Cultures");
  expect(cultures.description).toMatch(/cultures/i);
  expect(cultures.descriptions.fr_fr).toBe(cultures.description);
  expect(cultures.descriptions.en_us).toMatch(/crops/i);
  expect(cultures.descriptions.ko_kr).toBeTruthy();
  expect(cultures.descriptions.zh_cn).toBeTruthy();
});

test("l'aubergine porte son nom dans les quatre langues", () => {
  const a = livres.find((l) => l.id === "almanac");
  const e = a.categories.flatMap((c) => c.entrees).find((x) => x.chemin.endsWith("crops/eggplant.json"));
  expect(e.nom.fr_fr).toBe("Aubergine 🍂");
  expect(e.nom.en_us).toBe("Eggplant 🍂");
  expect(e.nom.ko_kr).toBeTruthy();
});

// Correction A du brief : la spécification d'origine (et le brief avec elle) affirmait
// que patchouli:multiblock et patchouli:entity n'ont rien à traduire. Mesuré faux :
// sur les 524 pages réelles des deux livres, patchouli:multiblock porte son nom dans
// un champ "name " (110 pages), patchouli:entity porte son "text" et/ou son "name"
// (153 pages) — les 524 pages portent du texte. Ce test, contrairement à celui du
// brief, vérifie que la page multibloc EST traduisible (inversion de l'assertion
// d'origine, qui aurait caché 263 pages sur 524).
test("les pages texte ET les pages multiblocs sont traduisibles", () => {
  const a = livres.find((l) => l.id === "almanac");
  const e = a.categories.flatMap((c) => c.entrees).find((x) => x.chemin.endsWith("crops/eggplant.json"));
  expect(e.pages[0].type).toBe("patchouli:text");
  expect(e.pages[0].traduisible).toBe(true);
  expect(e.pages[0].pointeur).toBe("pages/0/text");
  expect(e.pages[0].valeurs.fr_fr).toMatch(/Automne/);

  expect(e.pages[1].type).toBe("patchouli:multiblock");
  expect(e.pages[1].traduisible).toBe(true);
  // Champ "name " avec une espace finale : c'est le nom du champ tel qu'il existe sur
  // le disque dans les sources anglaise/française/chinoise (Patchouli lit "name" sans
  // espace au rendu — un défaut du pack, pas de ce lecteur, non masqué ici).
  expect(e.pages[1].pointeur).toBe("pages/1/name ");
  expect(e.pages[1].valeurs.fr_fr).toBe("Pousse d'aubergine");
  expect(e.pages[1].valeurs.en_us).toBe("Eggplant Crop");
});

test("les pages d'entité portent leur texte", () => {
  const a = livres.find((l) => l.id === "almanac");
  const vache = a.categories.flatMap((c) => c.entrees).find((x) => x.chemin.endsWith("animals/cow.json"));
  const p = vache.pages.find((x) => x.type === "patchouli:entity");
  expect(p.traduisible).toBe(true);
  expect(p.valeurs.fr_fr).toBeTruthy();
});

// Correction B du brief : les quatre arbres de langue ne se superposent pas partout.
// Le coréen écrit "name" (sans espace) plutôt que "name " sur 38 pages multiblocs — dont
// justement celle de l'aubergine. Un lecteur qui suppose le nom de champ de la langue
// de référence plutôt que de le lire dans le fichier ko_kr ouvert y afficherait une
// page vide. Verrouillé ici sur cette divergence réelle, mesurée sur le fichier.
test("le coréen diverge sur le champ du multibloc (name, sans l'espace finale) et reste lisible", () => {
  const a = livres.find((l) => l.id === "almanac");
  const e = a.categories.flatMap((c) => c.entrees).find((x) => x.chemin.endsWith("crops/eggplant.json"));
  expect(e.pages[1].valeurs.ko_kr).toBe("가지 작물");
});

// Corollaire de la même correction B, sur l'autre livre : deux pages de fish_finder
// (fish/leech.json, fish/goldfish.json) changent même de type en coréen
// (patchouli:spotlight au lieu de patchouli:entity, "item" au lieu de "entity") — mais
// leur champ "text" reste écrit sous ce nom-là dans les deux langues, donc lisible sans
// alias particulier : preuve que la lecture par nom de champ propre au fichier ouvert,
// pas par type de page hérité de la référence, est la bonne approche.
test("fish/goldfish.json reste lisible en coréen malgré un type de page qui change", () => {
  const f = livres.find((l) => l.id === "fish_finder");
  const goldfish = f.categories.flatMap((c) => c.entrees).find((x) => x.chemin.endsWith("fish/goldfish.json"));
  const p = goldfish.pages.find((x) => x.type === "patchouli:entity");
  expect(p.traduisible).toBe(true);
  expect(p.valeurs.ko_kr).toBeTruthy();
});

// Correction C du brief : book.json porte name comme une CLÉ ("society.books.almanac.name"),
// pas un littéral. Résolue dans kubejs/assets/society/lang/.
test("les titres de livre sont résolus depuis les fichiers de langue, pas la clé brute", () => {
  const a = livres.find((l) => l.id === "almanac");
  const f = livres.find((l) => l.id === "fish_finder");
  expect(a.titre.fr_fr).toBe("Almanach du fermier");
  expect(a.titre.en_us).toBe("Farmer's Almanac");
  expect(f.titre.fr_fr).toBe("Trouve-poissons");
});

// Régression : ce lecteur définissait son propre lireJson sur JSON.parse nu, là où les
// quatre autres passent par parseLang. Minecraft tolère un commentaire // en tête d'un
// fichier de langue ; un JSON.parse nu non — un tel fichier de titres de livre lisait
// alors comme entièrement absent, faisant retomber les titres sur l'anglais sans un
// mot alors que la recherche (read-pack.js, qui passe par parseLang) restait intacte.
test("un commentaire // en tête du fichier de titres de livre n'efface pas les titres (parseLang, pas JSON.parse nu)", () => {
  const tmp = mkdtempSync(join(tmpdir(), "read-books-commentaire-"));
  try {
    const dirLang = join(tmp, "kubejs/assets/society/lang");
    const dirLivre = join(tmp, "patchouli_books/almanac");
    mkdirSync(dirLang, { recursive: true });
    mkdirSync(join(dirLivre, "fr_fr/categories"), { recursive: true });
    mkdirSync(join(dirLivre, "fr_fr/entries"), { recursive: true });

    writeFileSync(
      join(dirLang, "fr_fr.json"),
      '// commentaire de tête, toléré par Minecraft\n{"society.books.almanac.name": "Almanach du fermier"}'
    );
    writeFileSync(join(dirLivre, "book.json"), JSON.stringify({ name: "society.books.almanac.name" }));

    const r = readBooks(tmp);
    expect(r.illisibles).toEqual([]);
    expect(r.livres[0].titre.fr_fr).toBe("Almanach du fermier");
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

// Recensement du brief, vérifié directement sur les fichiers : 524 pages portent du
// texte dans les deux livres, pour 527 champs traduisibles au total (une poignée de
// pages — 3 mesurées — portent deux champs à la fois, ex. name+text sur une page
// d'entité). Aucune page n'est donc légitimement non traduisible dans ce pack.
test("524 pages traduisibles, 527 champs, dans les deux livres", () => {
  const toutesPages = livres.flatMap((l) => l.categories).flatMap((c) => c.entrees).flatMap((e) => e.pages);
  expect(toutesPages).toHaveLength(524);
  expect(toutesPages.every((p) => p.traduisible)).toBe(true);
  const totalChamps = toutesPages.reduce((n, p) => n + p.champs.length, 0);
  expect(totalChamps).toBe(527);
});

test("aucun fichier illisible sur le pack réel", () => {
  expect(illisibles).toEqual([]);
});

// Même garde que read-quests.test.js : un fichier de langue de livre illisible même
// après tentative de lecture doit être signalé dans .illisibles, jamais ignoré en
// silence — c'est ce tableau qu'api.js journalise et publie dans /api/sante.
test("un book.json et un fichier de langue illisibles sont signalés, pas ignorés", () => {
  const tmp = mkdtempSync(join(tmpdir(), "read-books-illisible-"));
  try {
    const dirLang = join(tmp, "kubejs/assets/society/lang");
    const dirLivre = join(tmp, "patchouli_books/almanac");
    mkdirSync(dirLang, { recursive: true });
    mkdirSync(join(dirLivre, "fr_fr/categories"), { recursive: true });
    mkdirSync(join(dirLivre, "fr_fr/entries"), { recursive: true });
    mkdirSync(join(dirLivre, "en_us/categories"), { recursive: true });
    mkdirSync(join(dirLivre, "en_us/entries"), { recursive: true });

    writeFileSync(join(dirLang, "fr_fr.json"), '{"a": "b"'); // tronqué : illisible
    writeFileSync(join(dirLang, "en_us.json"), "{}");
    writeFileSync(join(dirLivre, "book.json"), "{ pas du json"); // illisible
    writeFileSync(
      join(dirLivre, "fr_fr/categories/crops.json"),
      JSON.stringify({ name: "Cultures", description: "Un aperçu.", category: "patchouli:crops" })
    );
    writeFileSync(
      join(dirLivre, "en_us/categories/crops.json"),
      JSON.stringify({ name: "Crops", description: "An overview.", category: "patchouli:crops" })
    );
    writeFileSync(
      join(dirLivre, "fr_fr/entries/pomme.json"),
      JSON.stringify({ name: "Pomme", category: "patchouli:crops", pages: [{ type: "patchouli:text", text: "Un fruit." }] })
    );

    const r = readBooks(tmp);
    const cheminLang = join(dirLang, "fr_fr.json");
    const cheminLivre = join(dirLivre, "book.json");

    expect(r.illisibles).toContain(cheminLang);
    expect(r.illisibles).toContain(cheminLivre);
    // Le livre se construit quand même, avec repli sur l'id pour son titre puisque
    // book.json n'a pas pu être lu.
    expect(r.livres).toHaveLength(1);
    expect(r.livres[0].titre).toEqual({ fr_fr: "almanac" });
    expect(r.livres[0].categories[0].entrees).toHaveLength(1);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

// Régression post-revue : `(base.pages ?? []).map(...)` protège contre `pages` absent
// (null/undefined), pas contre une forme inattendue (JSON par ailleurs valide). Un
// `pages` réduit à un objet plantait sur .map(...) — le même piège que celui corrigé
// dans review-queue.js (point 1 de la revue finale), qui avait échappé à l'audit
// initial de ce fichier. Une entrée dont `pages` est mal formé doit être signalée dans
// `illisibles`, jamais faire planter tout le lecteur (donc /api/livres ET /api/sante,
// qui appellent toutes deux readBooks()).
test("une entrée dont `pages` n'est pas un tableau est signalée dans illisibles, sans planter", () => {
  const tmp = mkdtempSync(join(tmpdir(), "read-books-pages-forme-"));
  try {
    const dirLivre = join(tmp, "patchouli_books/almanac");
    mkdirSync(join(dirLivre, "fr_fr/categories"), { recursive: true });
    mkdirSync(join(dirLivre, "fr_fr/entries"), { recursive: true });

    writeFileSync(join(dirLivre, "book.json"), JSON.stringify({ name: "almanac" }));
    writeFileSync(
      join(dirLivre, "fr_fr/categories/crops.json"),
      JSON.stringify({ name: "Cultures", category: "patchouli:crops" })
    );
    // `pages` est un objet, pas un tableau : JSON par ailleurs valide, forme inattendue.
    writeFileSync(
      join(dirLivre, "fr_fr/entries/pomme.json"),
      JSON.stringify({ name: "Pomme", category: "patchouli:crops", pages: { 0: { type: "patchouli:text", text: "x" } } })
    );

    const cheminEntree = join(dirLivre, "fr_fr/entries/pomme.json");
    const r = readBooks(tmp);

    expect(r.illisibles).toContain(cheminEntree);
    expect(r.livres).toHaveLength(1);
    const entree = r.livres[0].categories[0].entrees[0];
    expect(entree.pages).toEqual([]);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

// Corollaire : un élément `null` À L'INTÉRIEUR d'un tableau `pages` par ailleurs valide
// (donc pas signalé par le test ci-dessus) plante aussi sur l'accès de propriété
// (pg.type), contrairement à un élément primitif. Replié sur une page vide plutôt que
// de planter.
test("un élément `null` dans `pages` ne plante pas, replié sur une page sans champ connu", () => {
  const tmp = mkdtempSync(join(tmpdir(), "read-books-page-null-"));
  try {
    const dirLivre = join(tmp, "patchouli_books/almanac");
    mkdirSync(join(dirLivre, "fr_fr/categories"), { recursive: true });
    mkdirSync(join(dirLivre, "fr_fr/entries"), { recursive: true });

    writeFileSync(join(dirLivre, "book.json"), JSON.stringify({ name: "almanac" }));
    writeFileSync(
      join(dirLivre, "fr_fr/categories/crops.json"),
      JSON.stringify({ name: "Cultures", category: "patchouli:crops" })
    );
    writeFileSync(
      join(dirLivre, "fr_fr/entries/pomme.json"),
      JSON.stringify({ name: "Pomme", category: "patchouli:crops", pages: [null, { type: "patchouli:text", text: "x" }] })
    );

    const r = readBooks(tmp);
    expect(r.illisibles).toEqual([]);
    const pages = r.livres[0].categories[0].entrees[0].pages;
    expect(pages).toHaveLength(2);
    expect(pages[0].traduisible).toBe(false);
    expect(pages[1].traduisible).toBe(true);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

test("un livre sans book.json retombe sur le nom du dossier au lieu de lever", () => {
  // Cas réel du dépôt de traduction : il publie les arbres fr_fr des livres mais pas
  // leur manifeste. readFileSync levait alors une ENOENT qui faisait tomber /api/livres
  // ET /api/sante en 500 — un miroir partiel rendait l'Atelier inutilisable.
  const d = mkdtempSync(join(tmpdir(), "atelier-livres-"));
  const entree = join(d, "patchouli_books", "monlivre", "fr_fr", "entries", "cat");
  mkdirSync(entree, { recursive: true });
  mkdirSync(join(d, "patchouli_books", "monlivre", "fr_fr", "categories"), { recursive: true });
  writeFileSync(join(d, "patchouli_books", "monlivre", "fr_fr", "categories", "cat.json"),
    JSON.stringify({ name: "Une catégorie", description: "Sa description" }));
  writeFileSync(join(entree, "page.json"), JSON.stringify({
    name: "Une entrée", category: "monlivre:cat",
    pages: [{ type: "patchouli:text", text: "Du texte" }],
  }));

  const r = readBooks(d);
  expect(r.livres).toHaveLength(1);
  expect(r.livres[0].id).toBe("monlivre");
  expect(r.livres[0].titre.fr_fr).toBe("monlivre");
  expect(r.illisibles).toHaveLength(0);
  rmSync(d, { recursive: true, force: true });
});
