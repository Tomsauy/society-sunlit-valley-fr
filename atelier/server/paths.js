import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

// Racine du dépôt : deux niveaux au-dessus de ce fichier (site/server/ → site/ → dépôt).
// Sert de base à la résolution des quatre chemins ci-dessous, y compris quand ils sont
// fixés de l'extérieur — voir `depuisEnv`.
export const ROOT = resolve(here, "../..");

// Les quatre chemins réels que ce module résout sont ceux de la disposition de dossiers
// de l'auteur (pack et espace de travail à côté de site/, langues extraites et config
// des quêtes dedans) — mais un autre environnement peut les avoir ailleurs, ou vouloir
// les nommer autrement. Chacun peut donc être fixé par une variable d'environnement
// (ATELIER_PACK, ATELIER_WORKSPACE, ATELIER_EXTRACTED, ATELIER_QUESTS_CONFIG) ; à
// défaut, on retombe sur la disposition habituelle, exactement comme avant. Une valeur
// fournie relative est résolue par rapport à ROOT — la racine du dépôt — jamais par
// rapport au dossier courant du processus qui lance `npm run dev`, pour un résultat
// prévisible quel que soit l'endroit d'où l'on démarre le serveur ; `resolve` ignore ROOT
// de lui-même si la valeur fournie est déjà absolue.
const depuisEnv = (variable, defaut) => {
  const v = process.env[variable];
  return v ? resolve(ROOT, v) : defaut;
};

// PACK : la racine du modpack (le dépôt society-sunlit-valley).
export const PACK = depuisEnv("ATELIER_PACK", resolve(ROOT, "society-sunlit-valley"));

// WORKSPACE : fr-workspace/, où vivent provenance.json, a-revoir.json et (par défaut)
// les langues extraites des JARs.
export const WORKSPACE = depuisEnv("ATELIER_WORKSPACE", resolve(ROOT, "fr-workspace"));

// EXTRACTED et QUESTS_CONFIG dérivent par défaut de WORKSPACE/PACK — c'est la disposition
// habituelle — mais chacun reste réglable indépendamment : rien n'empêche de garder les
// langues extraites ailleurs que dans fr-workspace/, par exemple.
export const EXTRACTED = depuisEnv("ATELIER_EXTRACTED", resolve(WORKSPACE, "extracted"));
export const QUESTS_CONFIG = depuisEnv("ATELIER_QUESTS_CONFIG", resolve(PACK, "config/ftbquests/quests"));
