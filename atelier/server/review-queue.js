// site/server/review-queue.js
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { WORKSPACE } from "./paths.js";
import { namespaceDuFichier } from "./read-meta.js";

const DEFAUT = join(WORKSPACE, "a-revoir.json");

// Comme readPack()/readMods()/readMeta() : le tableau retourné porte une propriété
// `illisibles` plutôt que de faire disparaître silencieusement un JSON invalide dans
// un [] indiscernable d'une file réellement vide. Un fichier absent est une file vide
// légitime (premier lancement, rien à signaler) ; un fichier présent mais invalide est
// un état d'erreur qui ne doit surtout pas être écrasé par une écriture ultérieure —
// voir ajouterMarque()/retirerMarque() ci-dessous, qui refusent d'écrire dans ce cas.
//
// Un JSON *valide* qui n'est pas un tableau (ex. `{"cle":"x"}`, une faute de frappe en
// éditant le fichier à la main) passait autrefois la garde try/catch — JSON.parse
// réussit — et ressortait tel quel comme "d". ajouterMarque() appelle ensuite
// d.findIndex(...), qui n'existe pas sur un objet nu : l'exception remontait hors de
// ce module (elle survient dans le rappel req.on("end", ...) d'api.js, donc hors du
// try/catch de l'intergiciel) et faisait sortir le processus Node entier — le seul
// plantage total mesuré sur cette branche. La forme attendue (un tableau) est donc
// vérifiée explicitement, pas seulement l'analyse : un JSON valide de mauvaise forme
// est traité exactement comme un JSON invalide — signalé dans `illisibles`, jamais
// silencieusement accepté ni écrasé.
const charger = (f) => {
  if (!existsSync(f)) return Object.assign([], { illisibles: [] });
  try {
    const d = JSON.parse(readFileSync(f, "utf8"));
    if (!Array.isArray(d)) return Object.assign([], { illisibles: [f] });
    return Object.assign(d, { illisibles: [] });
  } catch {
    return Object.assign([], { illisibles: [f] });
  }
};
const sauver = (f, d) => writeFileSync(f, JSON.stringify(d, null, 1) + "\n", "utf8");

export const messageIllisible = (f) =>
  `La file à revoir (${f}) contient un JSON invalide ou n'est pas un tableau : écriture refusée pour ne pas ` +
  `écraser son contenu existant. Corrige le fichier à la main avant de réessayer.`;

// Une entrée posée avant l'introduction du champ `id` n'en porte pas : on la
// retrouve alors par sa clé nue. Une entrée qui porte un id est retrouvée par cet id
// complet — la clé nue seule ne suffit pas, 422 clés du corpus réel sont partagées
// par plusieurs namespaces, et deux mods qui partagent une clé ne doivent pas se
// marcher dessus lors d'un retrait (voir retirerMarque ci-dessous — celle-ci reçoit
// un identifiant nu, sans namespace connu, donc ce simple repli suffit : les marques
// posées par le site portent toutes un id depuis cette tâche, la seule ambiguïté qui
// reste au retrait concernerait deux marques antérieures sans id partageant la même
// clé, un cas qui ne s'est jamais produit sur le fichier réel).
const correspond = (e, id, cle) => (e.id ? e.id === id : e.cle === cle);

// ajouterMarque, lui, CONNAÎT le namespace de l'entrée qu'on est en train de marquer
// (l'appelant le lit sur l'entrée d'index) : correspondMarque s'en sert pour éviter
// une collision que `correspond` ci-dessus ne peut pas voir. Marquer l'entrée d'un
// mod sur une clé partagée par plusieurs namespaces (422 clés réelles) ne doit
// fusionner qu'avec la marque antérieure du même mod, jamais avec celle d'un autre —
// sans quoi remarquer une entrée effacerait la note d'une marque qui ne la concernait
// pas, et le panneau de détail l'attribuerait au mauvais mod (voir son usage dans
// api.js, route /detail/:id). Réutilise namespaceDuFichier (read-meta.js), qui résout
// déjà ce même problème pour provenance.json — pas une seconde implémentation.
// Une marque sans id NI fichier est indécidable : on refuse de la faire correspondre
// plutôt que de deviner à qui elle appartient.
export function correspondMarque(m, { id, cle, ns }) {
  if (m.id) return m.id === id;
  if (m.cle !== cle) return false;
  if (!m.fichier) return false;
  return namespaceDuFichier(m.fichier) === ns;
}

export const listerMarques = (fichier = DEFAUT) => charger(fichier);

// « pour » distingue ce que je traiterai moi-même de ce qui peut être repris en lot
// par l'IA — c'est ce qui rend la file exploitable.
//
// Fusionne l'entrée existante plutôt que de la remplacer intégralement : une marque
// posée à la main peut porter des champs que le site ne connaît pas (ex. `statut`,
// une distinction vérifié/déduit) — les effacer à chaque remarquage détruirait un
// travail d'analyse qu'aucune de ces deux fonctions n'a produit et ne doit donc pas
// perdre. Seuls les champs que le site gère (id, cle, fichier, fr_actuel, note,
// pour, ajoute_le) sont écrasés ; tout le reste survit. `ns` (le namespace de
// l'entrée qu'on marque) ne devient pas lui-même un champ stocké — il sert
// uniquement à correspondMarque pour éviter de fusionner à tort avec la marque d'un
// autre mod (voir commentaire ci-dessus).
export function ajouterMarque({ id, cle, ns, fichier: cible, fr_actuel, note, pour = "utilisateur" },
                               fichier = DEFAUT) {
  const d = charger(fichier);
  if (d.illisibles.length) return { ok: false, erreur: messageIllisible(fichier) };
  const i = d.findIndex(e => correspondMarque(e, { id, cle, ns }));
  const entree = {
    ...(i >= 0 ? d[i] : {}),
    id, cle, fichier: cible, fr_actuel, note, pour,
    ajoute_le: new Date().toISOString().slice(0, 10),
  };
  if (i >= 0) d[i] = entree; else d.push(entree);
  sauver(fichier, d);
  return { ok: true, entree };
}

// `identifiant` est l'id complet de la marque si elle en porte un, ou sa clé nue
// pour une marque antérieure au champ id — à l'appelant de fournir la bonne valeur
// (voir DetailPanel.svelte / ReviewView.svelte : m.id ?? m.cle).
export function retirerMarque(identifiant, fichier = DEFAUT) {
  const d = charger(fichier);
  if (d.illisibles.length) return { ok: false, erreur: messageIllisible(fichier) };
  const reste = d.filter(e => !correspond(e, identifiant, identifiant));
  if (reste.length === d.length) return { ok: true, retire: false };
  sauver(fichier, reste);
  return { ok: true, retire: true };
}
