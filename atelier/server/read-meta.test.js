// site/server/read-meta.test.js
import { test, expect } from "vitest";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { readMeta, evenementsPourNamespace } from "./read-meta.js";

const meta = readMeta();

test("charge la provenance", () => {
  expect(meta.provenance.size).toBeGreaterThan(2000);
  const ev = meta.provenance.get("item.brewery.hop_trellis_seed");
  expect(ev[0].type).toBe("sans_source_anglaise");
  expect(ev[0].temoins.ko_kr).toBeTruthy();
});

test("charge le glossaire indexé par terme anglais", () => {
  expect(meta.glossaire.size).toBeGreaterThan(1500);
  expect(meta.glossaire.get("Copper").fr).toBe("Cuivre");
});

test("charge la file à revoir", () => {
  expect(Array.isArray(meta.aRevoir)).toBe(true);
});

test("les termes de glossaire d'un texte sont retrouvables, du plus long au plus court", () => {
  const { termesDe } = meta;
  const t = termesDe("Stone Brick Stairs");
  const i = t.findIndex(x => x.en === "Stairs");
  const j = t.findIndex(x => x.en === "Stone");
  expect(i).toBeGreaterThanOrEqual(0);
  expect(j).toBeGreaterThanOrEqual(0);
  expect(i).toBeLessThan(j);
});

test("l'appariement respecte les frontières de mot : Water ne doit pas ressortir de Watering", () => {
  const { termesDe } = meta;
  const t = termesDe("Watering Can");
  expect(t.some(x => x.en === "Water")).toBe(false);
});

test("un terme de glossaire à bord ponctué s'apparie quand même — cas réel « %s (%s) »", () => {
  // La frontière \b ne peut s'imposer que du côté où le terme commence ou finit par un
  // caractère de mot ; « %s (%s) » commence et finit par de la ponctuation, exiger \b des
  // deux côtés l'aurait rendu introuvable dans un texte comme « Flask of %s (%s) ».
  const { termesDe } = meta;
  const t = termesDe("Flask of %s (%s)");
  expect(t.some(x => x.en === "%s (%s)")).toBe(true);
});

test("un événement de provenance dont le fichier désigne un autre namespace est écarté — cas réel jeed/windswept", () => {
  // effect.windswept.thorns.description existe à la fois dans le mod jeed et dans windswept,
  // avec un texte anglais différent. provenance.json indexe par clé nue : une seule entrée de
  // provenance existe pour cette clé, et son `fichier`
  // (kubejs/assets/windswept/lang/fr_fr.json) ne concerne que windswept — la présenter côté
  // jeed serait de la fausse traçabilité.
  const brut = meta.provenance.get("effect.windswept.thorns.description");
  expect(brut.length).toBeGreaterThan(0);
  expect(brut.every(ev => ev.fichier)).toBe(true);

  expect(evenementsPourNamespace(brut, "windswept")).toHaveLength(brut.length);
  expect(evenementsPourNamespace(brut, "jeed")).toHaveLength(0);
});

test("un événement de provenance sans fichier est conservé quel que soit le namespace — on ne peut pas trancher", () => {
  const evenements = [{ type: "relecture", fr: "x" }];
  expect(evenementsPourNamespace(evenements, "peu_importe_lequel")).toHaveLength(1);
});

test("un fichier de métadonnées corrompu est signalé, pas ignoré en silence", () => {
  const tmp = mkdtempSync(join(tmpdir(), "read-meta-illisible-"));
  try {
    mkdirSync(tmp, { recursive: true });
    // JSON tronqué : sans le signalement, ça se lit comme « aucune décision connue »
    // alors qu'il faudrait lire « source cassée » — deux situations à ne jamais confondre.
    writeFileSync(join(tmp, "provenance.json"), '{"cles": {"a": [');
    writeFileSync(join(tmp, "a-revoir.json"), "[]");

    const m = readMeta(tmp);
    const chemin = join(tmp, "provenance.json");

    expect(m.illisibles).toContain(chemin);
    expect(m.provenance.size).toBe(0);
    expect(m.aRevoir).toEqual([]);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

// Même piège que review-queue.js (qui, lui, faisait tomber tout le serveur) : un JSON
// *valide* mais de mauvaise forme — provenance.json réduit à un tableau, a-revoir.json
// devenu un objet nu — passe l'analyse sans erreur. Sans vérification de forme,
// `prov.cles` et `md.aRevoir.find(...)` (api.js, route /detail/:id) se lisent comme
// « aucune décision connue » ou plantent silencieusement au lieu de signaler une
// source cassée.
test("un provenance.json ou a-revoir.json JSON valide mais de mauvaise forme est signalé, pas confondu avec une absence légitime", () => {
  const tmp = mkdtempSync(join(tmpdir(), "read-meta-forme-"));
  try {
    mkdirSync(tmp, { recursive: true });
    writeFileSync(join(tmp, "provenance.json"), "[1, 2, 3]"); // un tableau, pas un objet {cles, glossaire}
    writeFileSync(join(tmp, "a-revoir.json"), '{"cle": "x"}'); // un objet nu, pas un tableau

    const m = readMeta(tmp);
    const cheminProv = join(tmp, "provenance.json");
    const cheminRevoir = join(tmp, "a-revoir.json");

    expect(m.illisibles).toContain(cheminProv);
    expect(m.illisibles).toContain(cheminRevoir);
    expect(m.provenance.size).toBe(0);
    expect(Array.isArray(m.aRevoir)).toBe(true);
    expect(m.aRevoir).toEqual([]);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});
