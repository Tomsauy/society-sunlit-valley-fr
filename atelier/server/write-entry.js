// site/server/write-entry.js
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname } from "node:path";
import { parseLang } from "./parse-lang.js";

const JETON = /%(?:\d+\$)?[sdfeu]|%%|§.|\$\([^)]*\)|\\n|\{\d+\}/g;
const ACCENTS = /[àâäéèêëîïôöùûüÿçÀÂÄÉÈÊËÎÏÔÖÙÛÜŸÇœŒæÆ]/;
const MOT = /[A-Za-z]{4,}/;
const PREFIXES_SANS_ACCENT = ["item.", "block.", "entity."];

const jetons = (s) => (s ?? "").match(JETON)?.sort().join("|") ?? "";

// Mêmes règles que fr-workspace/scripts/validate_translation.py, qui fait foi pour
// le corpus (voir DECISION-ACCENTS.md pour accent_free_prefixes). Trois points où
// une version antérieure de ce fichier divergeait du script Python, désormais alignés :
//
//  1. `is_name` (le nom est-il un libellé court cherchable dans EMI ?) se calcule sur
//     l'ANGLAIS, pas sur le français : un texte anglais court qui a été traduit par une
//     phrase reste soumis à la contrainte sans accents, et inversement un anglais déjà
//     long ne l'est pas même si sa traduction tient en un mot accentué.
//  2. `untranslated` : une traduction strictement identique à l'anglais, dès lors que ce
//     dernier contient un mot d'au moins 4 lettres et fait plus de 3 caractères, est une
//     erreur — l'objet n'a tout simplement pas été traduit.
//  3. `should_be_empty` : quand l'anglais est vide ou blanc, le français DOIT l'être aussi
//     (certaines clés du corpus sont volontairement vides des deux côtés) ; une valeur
//     française non vide dans ce cas est l'erreur, pas l'inverse.
export function validerValeur({ en, fr, cle }) {
  const problemes = [];

  // origine "aucune" (voir index-build.js) : la clé n'existe dans AUCUN en_us.json, ni
  // jar ni override — objet créé par un script du pack. Python ne voit jamais cette
  // clé (elle n'apparaît pas dans son en.json), donc n'a pas d'avis : ni placeholders
  // (rien à comparer), ni politique d'accents (qui se juge sur l'anglais, absent ici),
  // ni règle should_be_empty (qui, côté Python, ne s'applique qu'aux clés réellement
  // présentes dans en.json avec une valeur blanche — pas aux clés absentes). On se
  // contente d'exiger une valeur non vide.
  if (en === null || en === undefined) {
    if (!fr || !fr.trim()) problemes.push("La traduction est vide.");
    return problemes;
  }

  if (!en.trim()) {
    // should_be_empty (Python) : l'anglais existe mais est vide ou blanc — le français
    // doit l'être aussi.
    if (fr && fr.trim())
      problemes.push("L'anglais est vide ou blanc : la traduction doit l'être aussi.");
    return problemes;
  }

  if (!fr || !fr.trim()) {
    problemes.push("La traduction est vide.");
    return problemes;
  }

  if (jetons(en) !== jetons(fr))
    problemes.push(`Placeholders différents : l'anglais a ${jetons(en) || "aucun"}, la traduction ${jetons(fr) || "aucun"}.`);

  const segments = (cle.match(/\./g) ?? []).length;
  const estNom = PREFIXES_SANS_ACCENT.some((p) => cle.startsWith(p));
  // Python compte les mots avec v.split() (sans argument), qui ignore nativement les
  // espaces de bord. en.split(/\s+/) sur un anglais NON trimé produit un élément vide
  // de plus par espace de tête/fin, gonflant le compte au-delà de 6 et faisant basculer
  // estNom à faux à tort — d'où le .trim() avant de découper, pour rester fidèle à
  // Python plutôt que scinder sur la chaîne brute.
  const libelleCourt = en.trim().split(/\s+/).length <= 6 && !/[.!?]$/.test(en.trim());
  if (estNom && segments === 2 && libelleCourt && ACCENTS.test(fr))
    problemes.push("Accent interdit : ce nom est cherchable dans EMI, il doit s'écrire sans accents.");

  if (fr === en && MOT.test(en) && en.length > 3)
    problemes.push("Traduction identique à l'anglais : cette clé n'a pas été traduite.");

  return problemes;
}

export function writeLangEntry({ fichier, cle, valeur }) {
  try {
    let data = {};
    if (existsSync(fichier)) {
      const { data: lu, tolerated } = parseLang(readFileSync(fichier, "utf8"));
      if (!lu) return { ok: false, erreur: "Fichier illisible : JSON invalide même après tolérance aux commentaires." };
      // parseLang tolère les commentaires // (délibérément — les rejeter avait fait
      // disparaître 190 clés en silence), mais JSON.stringify les efface sans le dire.
      // Réécrire ce fichier détruirait ses commentaires sans qu'on l'ait demandé :
      // on refuse plutôt que d'agir en silence sur un fichier qu'on ne peut pas
      // fidèlement reproduire.
      if (tolerated)
        return { ok: false, erreur: "Ce fichier contient des commentaires (//) que l'écriture effacerait sans le dire. Corrige-le à la main." };
      data = lu;
    }
    data[cle] = valeur;
    const trie = Object.fromEntries(Object.keys(data).sort().map((k) => [k, data[k]]));
    // e.emplacement.fichier n'est jamais null : c'est le fichier fr_fr.json existant du
    // pack, ou le chemin qu'il faudrait créer pour un mod pas encore couvert. On crée
    // donc le dossier (et le fichier) manquants plutôt que d'échouer.
    mkdirSync(dirname(fichier), { recursive: true });
    writeFileSync(fichier, JSON.stringify(trie, null, 2) + "\n", "utf8");
    return { ok: true };
  } catch (e) {
    return { ok: false, erreur: e.message };
  }
}
