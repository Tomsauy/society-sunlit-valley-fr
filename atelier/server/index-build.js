import { join } from "node:path";
import { readPack } from "./read-pack.js";
import { readMods } from "./read-mods.js";
import { PACK } from "./paths.js";

// Une entrée = une clé de traduction, avec toutes ses langues et son anglais source.
// L'anglais peut venir de trois endroits, par ordre de priorité :
//   override — le pack a renommé l'objet, son en_us fait foi
//   jar      — le fichier anglais du mod
//   aucune   — objet créé par un script du pack, aucun anglais n'existe
export function buildKeyIndex() {
  const pack = readPack();
  const mods = readMods();
  const entrees = [];
  const parId = new Map();
  // Une même clé (chaîne nue) peut exister dans plusieurs namespaces — deux mods
  // différents choisissent parfois le même identifiant. parCle regroupe toutes les
  // entrées qui partagent une clé, tous namespaces confondus, pour qu'on puisse
  // détecter cette ambiguïté (provenance.json, lui, indexe par clé nue).
  const parCle = new Map();
  const locales = new Set();

  const namespaces = new Set([...pack.keys(), ...mods.keys()]);
  for (const ns of namespaces) {
    const p = pack.get(ns);
    const m = mods.get(ns);
    const overrideEn = p?.locales.get("en_us") ?? {};
    const jarEn = m?.locales.get("en_us") ?? {};

    // Chemin cible du fichier français du pack : celui qui existe déjà, sinon
    // celui qu'on créerait — jamais null, sans quoi un namespace tout neuf côté
    // mods (aucun fichier de langue encore présent dans le pack) deviendrait
    // impossible à corriger depuis le site.
    const fichierFr = p?.fichiers.get("fr_fr") ?? join(PACK, "kubejs/assets", ns, "lang/fr_fr.json");

    const cles = new Set([
      ...Object.keys(overrideEn),
      ...Object.keys(jarEn),
      ...[...(p?.locales.values() ?? [])].flatMap(o => Object.keys(o)),
      ...[...(m?.locales.values() ?? [])].flatMap(o => Object.keys(o)),
    ]);

    for (const cle of cles) {
      const traductions = {};
      const presentDans = { pack: [], mods: [] };
      // le pack masque le jar : on garde ce que le joueur voit réellement
      for (const [loc, obj] of m?.locales ?? []) {
        if (loc !== "en_us" && obj[cle] !== undefined) {
          traductions[loc] = obj[cle]; presentDans.mods.push(loc); locales.add(loc);
        }
      }
      for (const [loc, obj] of p?.locales ?? []) {
        if (loc !== "en_us" && obj[cle] !== undefined) {
          traductions[loc] = obj[cle]; presentDans.pack.push(loc); locales.add(loc);
        }
      }

      // L'anglais est la SOURCE (source.en ci-dessous), pas une traduction : il reste
      // donc hors de `traductions` — DetailPanel.svelte l'affiche déjà séparément dans
      // un bloc dédié, et l'ajouter à `traductions` l'y aurait fait apparaître une
      // seconde fois. Mais `presentDans`/`locales` alimentent aussi le filtre avec/sans
      // (LangFilter.svelte → search.js/aLangue) et /api/locales, où en_us doit
      // justement pouvoir être nommé : « avec anglais, sans français » est l'exemple
      // même qui justifie ce filtre dans le document de conception, et jusqu'ici en_us
      // en était exclu partout (105 locales sur /api/locales, jamais l'anglais). Mêmes
      // conditions que la résolution de "origine" juste en dessous : présent dans le
      // pack quand l'override du pack porte la clé, dans les mods quand le jar la
      // porte — pas une nouvelle règle, la même lue deux fois.
      if (overrideEn[cle] !== undefined) { presentDans.pack.push("en_us"); locales.add("en_us"); }
      if (jarEn[cle] !== undefined) { presentDans.mods.push("en_us"); locales.add("en_us"); }

      let en = null, origine = "aucune";
      if (overrideEn[cle] !== undefined) { en = overrideEn[cle]; origine = "override"; }
      else if (jarEn[cle] !== undefined) { en = jarEn[cle]; origine = "jar"; }

      const e = {
        id: `lang:${ns}:${cle}`,
        kind: "lang",
        ns, cle,
        source: { en, origine },
        traductions,
        presentDans,
        emplacement: { fichier: fichierFr, pointeur: null },
        contexte: { mod: ns, version: m?.jar ?? "override du pack" },
      };
      entrees.push(e);
      parId.set(e.id, e);
      const groupe = parCle.get(cle);
      if (groupe) groupe.push(e); else parCle.set(cle, [e]);
    }
  }
  // pack et mods portent chacun leur propre `illisibles` (read-pack.js, read-mods.js) :
  // les chemins des fichiers dont le JSON reste invalide même après la tolérance aux
  // commentaires. On les regroupe ici pour que l'appelant n'ait qu'une seule liste à
  // surveiller pour tout ce qui a contribué à l'index.
  const illisibles = [...pack.illisibles, ...mods.illisibles];
  // Même principe pour `manquantes` : PACK et/ou EXTRACTED absents du disque, un
  // signalement distinct d'un fichier illisible (voir read-pack.js/read-mods.js).
  const manquantes = [...pack.manquantes, ...mods.manquantes];
  return { entrees, parId, parCle, locales: [...locales].sort(), illisibles, manquantes };
}
