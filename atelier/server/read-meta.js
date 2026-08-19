// site/server/read-meta.js
import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { WORKSPACE } from "./paths.js";

// Échappe les caractères spéciaux d'une regex : le glossaire contient des noms
// propres et des chaînes d'interface avec de la ponctuation (parenthèses, points,
// astérisques...) qui casseraient sinon la construction du motif ou changeraient
// son sens.
const echapper = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

// Une frontière \b n'existe qu'entre un caractère de mot et un caractère qui n'en
// est pas ; des deux côtés systématiquement, un terme qui commence ou finit par de
// la ponctuation (116 sur 1 689 dans le glossaire réel — ex. « %s (%s) », le
// placeholder d'un texte comme « Flask of %s (%s) ») ne peut alors jamais
// s'apparier. On n'exige la frontière que du côté où le terme commence — ou finit —
// effectivement par un caractère de mot ; « Water » reste ainsi rejeté à l'intérieur
// de « Watering » (les deux bords sont des caractères de mot) sans pénaliser les
// termes à bord ponctué.
const motifDuTerme = (terme) => {
  const debut = /^\w/.test(terme) ? "\\b" : "";
  const fin = /\w$/.test(terme) ? "\\b" : "";
  return new RegExp(`${debut}${echapper(terme)}${fin}`, "i");
};

// La clé nue qui indexe provenance.json est parfois partagée par plusieurs
// namespaces (deux mods choisissent le même identifiant, avec des textes anglais
// différents — 63 clés réelles). Un événement qui porte `fichier` (ex.
// "kubejs/assets/windswept/lang/fr_fr.json") désigne le namespace qu'il concerne
// réellement ; un événement dont le fichier pointe ailleurs est écarté plutôt que
// présenté à tort comme la décision d'un autre mod. Un événement sans `fichier` est
// conservé : on ne peut pas trancher, mais on ne l'invente pas non plus.
//
// Exportée : review-queue.js réutilise cette même fonction pour désambiguïser
// a-revoir.json sur exactement le même problème (une marque antérieure au champ
// `id` n'a que sa clé nue et son `fichier` pour se faire reconnaître, et 422 clés
// du corpus réel sont, elles aussi, partagées par plusieurs namespaces).
export const namespaceDuFichier = (fichier) => fichier.match(/assets\/([^/]+)\//)?.[1] ?? null;

export function evenementsPourNamespace(evenements, ns) {
  return evenements.filter(ev => !ev.fichier || namespaceDuFichier(ev.fichier) === ns);
}

// `workspace` est injectable (répertoire temporaire) pour les tests ; en usage
// normal il vaut WORKSPACE, fr-workspace/ à la racine du dépôt.
//
// L'objet retourné porte en plus une propriété `illisibles` : les chemins des
// fichiers de métadonnées dont le JSON est invalide. Un fichier illisible est
// signalé, jamais ignoré en silence — le même principe que read-pack.js et
// read-mods.js, pour la même raison : un fichier de métadonnées corrompu qui
// retombe sans bruit sur une valeur par défaut vide se lit comme « aucune décision
// connue » alors qu'il faudrait lire « source cassée », deux situations que
// l'appelant doit pouvoir distinguer.
export function readMeta(workspace = WORKSPACE) {
  const illisibles = [];
  // `estValide` vérifie la FORME du JSON analysé, pas seulement qu'il s'analyse : un
  // JSON valide de mauvaise forme (provenance.json réduit à un tableau, a-revoir.json
  // devenu un objet nu...) est le même genre de piège que celui qui a fait tomber le
  // serveur entier dans review-queue.js — ici il ne ferait "que" fausser silencieusement
  // provenance/aRevoir (Object.entries/le .find de md.aRevoir dans api.js échoueraient
  // ou mentiraient), donc traité pareil : signalé dans `illisibles`, jamais accepté tel
  // quel ni confondu avec une absence légitime de décisions.
  const lire = (nom, defaut, estValide) => {
    const p = join(workspace, nom);
    if (!existsSync(p)) return defaut;
    let val;
    try { val = JSON.parse(readFileSync(p, "utf8")); }
    catch { illisibles.push(p); return defaut; }
    if (estValide && !estValide(val)) { illisibles.push(p); return defaut; }
    return val;
  };

  const prov = lire("provenance.json", { cles: {}, glossaire: [] },
    (v) => v !== null && typeof v === "object" && !Array.isArray(v));
  const provenance = new Map(Object.entries(prov.cles ?? {}));
  const glossaire = new Map((prov.glossaire ?? []).map(g => [g.en, g]));
  const aRevoir = lire("a-revoir.json", [], Array.isArray);

  // Les termes du glossaire présents dans un texte donné, du plus long au plus court
  // pour que « Hops Seeds » ne masque pas « Hops ». Les expressions régulières sont
  // compilées une seule fois ici, à la lecture — pas à chaque appel de termesDe() —
  // sans quoi 1 698 termes seraient recompilés à chaque sélection dans l'interface.
  const parLongueur = [...glossaire.values()]
    .filter(g => g.en.length >= 3)
    .map(g => ({ g, re: motifDuTerme(g.en) }))
    .sort((a, b) => b.g.en.length - a.g.en.length);

  const termesDe = (texte) => {
    if (!texte) return [];
    return parLongueur.filter(({ re }) => re.test(texte)).map(({ g }) => g).slice(0, 8);
  };

  return { provenance, glossaire, aRevoir, termesDe, illisibles };
}
