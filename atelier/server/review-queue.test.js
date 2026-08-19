// site/server/review-queue.test.js
import { test, expect, beforeEach } from "vitest";
import { mkdtempSync, writeFileSync, readFileSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { ajouterMarque, listerMarques, retirerMarque, correspondMarque } from "./review-queue.js";

let dossier, fichier;
beforeEach(() => {
  dossier = mkdtempSync(join(tmpdir(), "revoir-"));
  fichier = join(dossier, "a-revoir.json");
  writeFileSync(fichier, "[]");
});

test("ajoute, liste et retire une marque", () => {
  const r = ajouterMarque(
    { id: "lang:x:item.x.y", cle: "item.x.y", fichier: "f.json", fr_actuel: "Truc",
      note: "à vérifier", pour: "ia" },
    fichier,
  );
  expect(r.ok).toBe(true);
  const l = listerMarques(fichier);
  expect(l).toHaveLength(1);
  expect(l[0].pour).toBe("ia");
  expect(l[0].id).toBe("lang:x:item.x.y");
  expect(l[0].ajoute_le).toMatch(/^\d{4}-\d{2}-\d{2}$/);

  const s = retirerMarque("lang:x:item.x.y", fichier);
  expect(s).toEqual({ ok: true, retire: true });
  expect(listerMarques(fichier)).toHaveLength(0);
});

test("ré-ajouter le même id remplace au lieu de dupliquer", () => {
  ajouterMarque({ id: "lang:a:a.b", cle: "a.b", note: "un", pour: "ia" }, fichier);
  ajouterMarque({ id: "lang:a:a.b", cle: "a.b", note: "deux", pour: "utilisateur" }, fichier);
  const l = listerMarques(fichier);
  expect(l).toHaveLength(1);
  expect(l[0].note).toBe("deux");
  expect(l[0].pour).toBe("utilisateur");
});

// Correction B du brief tâche 10 : une marque posée à la main (fichier réel,
// aucun champ `id`) peut porter des champs que le site ne connaît pas — ex.
// `statut`, une distinction vérifié/déduit. Remarquer cette même clé depuis le
// site doit fusionner, pas écraser : le champ inconnu doit survivre.
test("fusionne avec une entrée antérieure sans id, sur la clé, sans perdre ses champs inconnus", () => {
  const anterieure = [{
    cle: "society_tips.tip.villager_decor",
    fichier: "kubejs/assets/society_tips/lang/fr_fr.json",
    fr_actuel: "ancien texte",
    note: "note longue et soignée à préserver",
    pour: "utilisateur",
    ajoute_le: "2026-08-08",
    statut: "deduction_non_confirmee",
  }];
  writeFileSync(fichier, JSON.stringify(anterieure));

  const r = ajouterMarque({
    id: "lang:society_tips:society_tips.tip.villager_decor",
    cle: "society_tips.tip.villager_decor",
    ns: "society_tips",
    fichier: "kubejs/assets/society_tips/lang/fr_fr.json",
    fr_actuel: "nouveau texte",
    note: "nouvelle note",
    pour: "ia",
  }, fichier);

  expect(r.ok).toBe(true);
  const l = listerMarques(fichier);
  expect(l).toHaveLength(1);
  expect(l[0].statut).toBe("deduction_non_confirmee");
  expect(l[0].note).toBe("nouvelle note");
  expect(l[0].pour).toBe("ia");
  expect(l[0].id).toBe("lang:society_tips:society_tips.tip.villager_decor");
});

// Correctif post-revue : la correction D fermait la collision au retrait, mais
// pas à l'ajout. Une marque antérieure sans id n'est retrouvée que par sa clé
// nue ; sur une clé partagée par plusieurs mods (422 clés réelles), marquer
// l'entrée d'un AUTRE mod ne doit ni fusionner avec elle (perte de sa note),
// ni — côté /api/detail/:id — s'afficher comme si elle lui appartenait.
// correspondMarque tranche avec le namespace tiré de `fichier`
// (namespaceDuFichier, réutilisée de read-meta.js).
test("marquer un AUTRE mod sur une clé partagée ne fusionne pas avec la marque antérieure et ne l'écrase pas", () => {
  const anterieure = [{
    cle: "item.shared",
    fichier: "kubejs/assets/modA/lang/fr_fr.json",
    fr_actuel: "texte A",
    note: "note originale de modA, à ne jamais perdre",
    pour: "utilisateur",
    ajoute_le: "2026-01-01",
  }];
  writeFileSync(fichier, JSON.stringify(anterieure));

  // On marque item.shared, mais côté modB — même clé nue, autre mod.
  const r = ajouterMarque({
    id: "lang:modB:item.shared", cle: "item.shared", ns: "modB",
    fichier: "kubejs/assets/modB/lang/fr_fr.json",
    fr_actuel: "texte B", note: "note de modB", pour: "ia",
  }, fichier);

  expect(r.ok).toBe(true);
  const l = listerMarques(fichier);
  // Deux entrées distinctes, pas une fusion : la marque de modA est intacte.
  expect(l).toHaveLength(2);
  const deModA = l.find(x => x.fichier === "kubejs/assets/modA/lang/fr_fr.json");
  expect(deModA.note).toBe("note originale de modA, à ne jamais perdre");
  expect(deModA.id).toBeUndefined();
  const deModB = l.find(x => x.id === "lang:modB:item.shared");
  expect(deModB.note).toBe("note de modB");

  // Le lookup utilisé par /api/detail/:id (même fonction) ne doit pas non plus
  // attribuer la marque de modA à modB, ni l'inverse.
  expect(correspondMarque(deModA, { id: "lang:modB:item.shared", cle: "item.shared", ns: "modB" }))
    .toBe(false);
  expect(correspondMarque(deModA, { id: "lang:modA:item.shared", cle: "item.shared", ns: "modA" }))
    .toBe(true);
});

test("marquer le MÊME mod sur une clé partagée fusionne bien avec sa propre marque antérieure", () => {
  const anterieure = [{
    cle: "item.shared",
    fichier: "kubejs/assets/modA/lang/fr_fr.json",
    fr_actuel: "texte A",
    note: "note originale de modA",
    pour: "utilisateur",
    ajoute_le: "2026-01-01",
  }];
  writeFileSync(fichier, JSON.stringify(anterieure));

  const r = ajouterMarque({
    id: "lang:modA:item.shared", cle: "item.shared", ns: "modA",
    fichier: "kubejs/assets/modA/lang/fr_fr.json",
    fr_actuel: "texte A mis à jour", note: "note mise à jour", pour: "ia",
  }, fichier);

  expect(r.ok).toBe(true);
  const l = listerMarques(fichier);
  expect(l).toHaveLength(1);
  expect(l[0].note).toBe("note mise à jour");
  expect(l[0].id).toBe("lang:modA:item.shared");
});

test("correspondMarque : une marque sans id NI fichier est indécidable, jamais reconnue", () => {
  const indecidable = { cle: "item.shared", note: "on ne sait pas de quel mod" };
  expect(correspondMarque(indecidable, { id: "lang:modA:item.shared", cle: "item.shared", ns: "modA" }))
    .toBe(false);
  expect(correspondMarque(indecidable, { id: "lang:modB:item.shared", cle: "item.shared", ns: "modB" }))
    .toBe(false);
});

// Correction D : 422 clés du corpus réel sont partagées par plusieurs namespaces.
// Marquer/retirer une entrée d'un mod ne doit jamais toucher l'entrée d'un autre
// mod qui porte la même clé nue.
test("deux entrées de mods différents partageant la même clé restent indépendantes", () => {
  ajouterMarque({ id: "lang:modA:item.shared", cle: "item.shared", note: "A", pour: "ia" }, fichier);
  ajouterMarque({ id: "lang:modB:item.shared", cle: "item.shared", note: "B", pour: "utilisateur" }, fichier);
  expect(listerMarques(fichier)).toHaveLength(2);

  const s = retirerMarque("lang:modA:item.shared", fichier);
  expect(s).toEqual({ ok: true, retire: true });
  const l = listerMarques(fichier);
  expect(l).toHaveLength(1);
  expect(l[0].id).toBe("lang:modB:item.shared");
});

test("retirerMarque replie sur la clé pour une marque antérieure sans id", () => {
  writeFileSync(fichier, JSON.stringify([{ cle: "a.b", note: "x", pour: "ia", ajoute_le: "2026-01-01" }]));
  const s = retirerMarque("a.b", fichier);
  expect(s).toEqual({ ok: true, retire: true });
  expect(listerMarques(fichier)).toHaveLength(0);
});

test("retirer un identifiant absent ne modifie rien et le signale", () => {
  ajouterMarque({ id: "lang:a:a.b", cle: "a.b", note: "x", pour: "ia" }, fichier);
  const s = retirerMarque("lang:introuvable:x", fichier);
  expect(s).toEqual({ ok: true, retire: false });
  expect(listerMarques(fichier)).toHaveLength(1);
});

// Correction C : un JSON invalide ne doit jamais être remplacé en silence par une
// liste tronquée à la seule nouvelle entrée — c'est une perte de données, plus
// grave qu'un simple défaut d'affichage.
test("un fichier corrompu fait refuser l'écriture, sans toucher au fichier", () => {
  const brut = '[{"cle": "a.b", "note": "présente déjà"';
  writeFileSync(fichier, brut);

  const r = ajouterMarque({ id: "lang:a:a.b", cle: "a.b", note: "x", pour: "ia" }, fichier);
  expect(r.ok).toBe(false);
  expect(r.erreur).toMatch(/JSON invalide/);
  expect(readFileSync(fichier, "utf8")).toBe(brut);
});

test("retirerMarque refuse aussi d'écrire sur un fichier corrompu", () => {
  const brut = '[{"cle": "a.b"';
  writeFileSync(fichier, brut);
  const r = retirerMarque("a.b", fichier);
  expect(r.ok).toBe(false);
  expect(r.erreur).toMatch(/JSON invalide/);
  expect(readFileSync(fichier, "utf8")).toBe(brut);
});

// Régression du seul plantage total de la branche : un JSON *valide* mais qui n'est
// pas un tableau (faute de frappe en éditant le fichier à la main, ex. un objet nu au
// lieu d'un tableau) passait la garde try/catch — JSON.parse réussit — et
// ajouterMarque() appelait ensuite d.findIndex(...) sur un objet, une TypeError qui
// remontait hors du module et faisait sortir le processus Node entier. La forme doit
// être traitée exactement comme une analyse invalide : refus d'écrire, message
// explicite, fichier intact.
test("un JSON valide mais qui n'est pas un tableau fait refuser l'écriture, sans planter", () => {
  const brut = '{"cle":"x"}';
  writeFileSync(fichier, brut);

  const r = ajouterMarque({ id: "lang:a:a.b", cle: "a.b", note: "x", pour: "ia" }, fichier);
  expect(r.ok).toBe(false);
  expect(r.erreur).toMatch(/JSON invalide/);
  expect(readFileSync(fichier, "utf8")).toBe(brut);
});

test("retirerMarque refuse aussi d'écrire quand le JSON est valide mais pas un tableau", () => {
  const brut = '{"cle":"x"}';
  writeFileSync(fichier, brut);
  const r = retirerMarque("a.b", fichier);
  expect(r.ok).toBe(false);
  expect(r.erreur).toMatch(/JSON invalide/);
  expect(readFileSync(fichier, "utf8")).toBe(brut);
});

test("listerMarques sur un JSON valide mais pas un tableau le signale dans illisibles plutôt que de planter", () => {
  writeFileSync(fichier, '{"cle":"x"}');
  const l = listerMarques(fichier);
  expect(l).toHaveLength(0);
  expect(l.illisibles).toEqual([fichier]);
});

test("listerMarques sur un fichier absent renvoie une file vide sans erreur", () => {
  mkdirSync(dossier, { recursive: true });
  expect(listerMarques(join(dossier, "inexistant.json"))).toHaveLength(0);
});

test("préserve les entrées existantes du fichier réel", () => {
  const reel = JSON.parse(readFileSync("../fr-workspace/a-revoir.json", "utf8"));
  expect(Array.isArray(reel)).toBe(true);
  if (reel.length) expect(reel[0]).toHaveProperty("cle");
});
