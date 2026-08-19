import { readdirSync, readFileSync, statSync, existsSync } from "node:fs";
import { join, basename, extname } from "node:path";
import { EXTRACTED } from "./paths.js";
import { parseLang } from "./parse-lang.js";
import { isLocale } from "./locales.js";

// Lit les langues extraites des JARs des mods : <extracted>/<jar>/<namespace>/<locale>.json
// Le nom du dossier <jar> porte la version du mod (create-1.20.1-6.0.8), affichée telle quelle.
// Un même namespace peut apparaître dans plusieurs jars : leurs clés se fusionnent, le contenu
// d'un jar traité plus tard écrasant celui d'un jar traité plus tôt pour une même clé. `jar`
// suit cette même précédence — il porte le dernier jar à avoir réellement fourni du contenu —
// et `jars` liste tous les jars contributeurs, dans l'ordre où ils ont été traités.
//
// `extracted` est injectable (répertoire temporaire) pour les tests ; en usage normal
// il vaut EXTRACTED, la racine des JARs extraits dans fr-workspace.
//
// La Map retournée porte en plus une propriété `illisibles` : les chemins des
// fichiers dont le JSON reste invalide même après la tolérance aux commentaires
// de parseLang. Un fichier illisible est signalé, jamais ignoré en silence —
// c'est ce silence qui avait fait disparaître 190 clés de vintagedelight.
//
const estDossier = (p) => {
  try { return statSync(p).isDirectory(); } catch { return false; }
};

// Une propriété `manquantes` complète `illisibles` pour un cas distinct : `extracted`
// absent du disque — un environnement qui n'a jamais extrait les JARs des mods (le cas
// courant d'un dépôt publié, où fr-workspace/extracted/ n'est pas suivi par git). Avant
// ce correctif, readdirSync(extracted) levait alors une ENOENT non rattrapée, qui
// faisait tomber /api/sante ET la vue Clés en 500 — pas un « fichier illisible » (il n'y
// a pas de fichier à lire), donc pas confondu avec `illisibles`.
//
// Le test porte sur « est-ce un dossier », pas sur « existe ». Un chemin mal configuré
// qui désigne un fichier passait `existsSync` puis levait ENOTDIR sur readdirSync, ce qui
// ramenait exactement le 500 que ce correctif supprime. read-pack.js et read-quests.js y
// échappent par construction — ils testent un sous-chemin, qui ne peut pas exister sous un
// fichier — mais celui-ci teste sa racine directement, d'où la garde explicite.
export function readMods(extracted = EXTRACTED) {
  const out = new Map();
  const illisibles = [];
  if (!estDossier(extracted)) {
    out.illisibles = illisibles;
    out.manquantes = [
      `Langues extraites introuvables : ${extracted} — traductions des mods indisponibles ` +
      `(ATELIER_EXTRACTED pour corriger).`,
    ];
    return out;
  }
  out.manquantes = [];
  for (const jar of readdirSync(extracted)) {
    const jarDir = join(extracted, jar);
    if (!statSync(jarDir).isDirectory()) continue;
    for (const ns of readdirSync(jarDir)) {
      const nsDir = join(jarDir, ns);
      if (!statSync(nsDir).isDirectory()) continue;
      const entry = out.get(ns) ?? { locales: new Map(), jar, jars: [] };
      let contribue = false;
      for (const f of readdirSync(nsDir)) {
        if (extname(f) !== ".json") continue;
        const loc = basename(f, ".json");
        if (!isLocale(loc)) continue;
        const chemin = join(nsDir, f);
        const { data } = parseLang(readFileSync(chemin, "utf8"));
        if (!data) { illisibles.push(chemin); continue; }
        const dejaLa = entry.locales.get(loc) ?? {};
        entry.locales.set(loc, { ...dejaLa, ...data });
        contribue = true;
      }
      // Seul un jar qui fournit vraiment du contenu devient le contributeur
      // « courant » — un dossier vide ou entièrement illisible ne doit pas
      // usurper l'étiquette de version.
      if (contribue) {
        entry.jar = jar;
        entry.jars.push(jar);
      }
      if (entry.locales.size) out.set(ns, entry);
    }
  }
  out.illisibles = illisibles;
  return out;
}
