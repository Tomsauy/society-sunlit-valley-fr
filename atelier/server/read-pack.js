import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join, basename, extname } from "node:path";
import { PACK } from "./paths.js";
import { parseLang } from "./parse-lang.js";
import { isLocale } from "./locales.js";

// Lit les traductions du modpack lui-même : le lieu où les corrections
// seront écrites plus tard, d'où la conservation du chemin de chaque fichier.
// `pack` est injectable (répertoire temporaire) pour les tests ; en usage normal
// il vaut PACK, la racine du modpack dans le dépôt.
//
// La Map retournée porte en plus une propriété `illisibles` : les chemins des
// fichiers dont le JSON reste invalide même après la tolérance aux commentaires
// de parseLang. Un fichier illisible est signalé, jamais ignoré en silence —
// c'est ce silence qui avait fait disparaître 190 clés de vintagedelight.
//
// Une propriété `manquantes` complète `illisibles` pour un cas distinct : `pack` lui-même
// (ou son sous-dossier kubejs/assets) absent du disque — un dépôt qui ne l'a pas encore
// cloné, ou une configuration qui pointe à côté. Avant ce correctif, readdirSync(assets)
// levait alors une ENOENT non rattrapée, qui faisait tomber /api/sante ET la vue Clés en
// 500 — pas de « fichier illisible » (il n'y a pas de fichier à lire), donc pas confondu
// avec `illisibles` : un signalement de nature différente, dans son propre tableau.
export function readPack(pack = PACK) {
  const assets = join(pack, "kubejs/assets");
  const out = new Map();
  const illisibles = [];
  if (!existsSync(assets)) {
    out.illisibles = illisibles;
    out.manquantes = [
      `Modpack introuvable : ${assets} — clés de traduction indisponibles (ATELIER_PACK pour corriger).`,
    ];
    return out;
  }
  out.manquantes = [];
  for (const ns of readdirSync(assets)) {
    const dir = join(assets, ns, "lang");
    if (!existsSync(dir)) continue;
    const locales = new Map(), fichiers = new Map();
    for (const f of readdirSync(dir)) {
      if (extname(f) !== ".json") continue;
      const loc = basename(f, ".json");
      if (!isLocale(loc)) continue;
      const chemin = join(dir, f);
      const { data } = parseLang(readFileSync(chemin, "utf8"));
      if (!data) { illisibles.push(chemin); continue; }
      locales.set(loc, data);
      fichiers.set(loc, chemin);
    }
    if (locales.size) out.set(ns, { locales, fichiers });
  }
  out.illisibles = illisibles;
  return out;
}
