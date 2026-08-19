// site/server/read-books.js
import { readdirSync, readFileSync, existsSync, statSync } from "node:fs";
import { join, relative, basename } from "node:path";
import { PACK } from "./paths.js";
import { isLocale } from "./locales.js";
import { parseLang } from "./parse-lang.js";

// Passe par parseLang comme readPack()/readMods()/readQuests() : Minecraft tolère les
// commentaires // en tête d'un fichier de langue, un JSON.parse nu non. Avant ce
// correctif, ce lecteur était le seul des cinq à ne pas passer par parseLang — un
// commentaire en tête de kubejs/assets/society/lang/fr_fr.json (accepté par Minecraft,
// et par les quatre autres lecteurs) laissait la recherche intacte mais faisait
// disparaître silencieusement les titres des deux livres, retombés sur l'anglais sans
// un mot : deux verdicts pour le même fichier dans le même processus.
const lireJson = (f) => parseLang(readFileSync(f, "utf8")).data;

function fichiersDe(racine) {
  const out = [];
  const marcher = (d) => {
    for (const n of readdirSync(d)) {
      const p = join(d, n);
      statSync(p).isDirectory() ? marcher(p) : n.endsWith(".json") && out.push(p);
    }
  };
  if (existsSync(racine)) marcher(racine);
  return out;
}

// Champs porteurs de texte, par type de page — mesurés sur les 524 pages réelles des
// deux livres du pack (261 patchouli:text, 153 patchouli:entity, 110
// patchouli:multiblock) : aucun des trois types n'est structurellement dépourvu de
// texte, contrairement à ce qu'affirmait la spécification d'origine pour
// patchouli:multiblock et patchouli:entity (qui aurait caché 263 pages sur 524). La
// traduisibilité d'une page se décide donc par la présence effective d'un de ces
// champs SUR CETTE page, jamais par son type. L'ordre reflète l'ordre d'apparition
// dans le JSON source (titre/nom avant le corps de texte).
//
// "name " (patchouli:multiblock) porte une espace finale intentionnelle : c'est le nom
// du champ tel qu'il existe sur le disque dans les sources anglaise, française et
// chinoise (110 pages). Patchouli lit "name" sans espace au moment du rendu — ces 110
// noms ne s'affichent donc jamais en jeu (défaut du pack, pas de ce lecteur) ; conservé
// littéral pour ne pas masquer l'anomalie, et parce que le pointeur d'écriture doit
// désigner le champ tel qu'il existe réellement sur le disque.
const CHAMPS_PAR_TYPE = {
  "patchouli:text": ["title", "text"],
  "patchouli:entity": ["name", "text"],
  "patchouli:multiblock": ["name "],
};

// Les quatre arbres de langue ne se superposent pas parfaitement : le coréen diverge
// de l'anglais/français/chinois sur 40 positions. 38 pages multiblocs y écrivent
// "name" (sans espace) plutôt que "name " ; 2 pages de fish_finder (fish/leech.json,
// fish/goldfish.json) changent même de type de page (patchouli:spotlight au lieu de
// patchouli:entity, avec un champ "item" au lieu de "entity") — mais leur champ "text"
// reste littéralement présent sous ce même nom, donc lisible sans alias. Seul "name "
// a donc besoin d'un repli explicite ; il se résout dans le fichier ouvert, jamais
// d'après le nom de champ utilisé par une autre langue.
const ALIAS_CHAMP = { "name ": ["name ", "name"] };

const litChamp = (page, nom) => {
  for (const alias of ALIAS_CHAMP[nom] ?? [nom]) {
    if (page[alias] !== undefined) return page[alias];
  }
  return undefined;
};

// Une poignée de pages (2 patchouli:entity avec name+text, 1 patchouli:text avec
// title+text — mesuré : 3 sur 524) portent DEUX champs traduisibles à la fois.
// `pointeur`/`valeurs` au sommet de la page restent des champs simples (forme attendue
// par le brief et ses tests, réputés justes) et reflètent le premier champ trouvé ;
// `champs` porte la liste complète, sur le modèle de quete.champs dans
// read-quests.js, pour qu'aucun des 527 champs mesurés sur les 524 pages ne
// disparaisse silencieusement derrière les 524 pointeurs simples.
// `fichier` (le chemin de l'entrée de langue de référence dont `base` a été lu) sert
// uniquement à nommer la source dans `illisibles` en cas de forme inattendue — voir
// juste en dessous.
function pagesDe(base, parLocale, illisibles, fichier) {
  // `?? []` protège contre `pages` absent (null/undefined), pas contre une forme
  // inattendue : `pages` réduit à un objet, une chaîne ou un nombre par un JSON par
  // ailleurs valide resterait truthy, passerait la garde, et ferait planter .map(...)
  // juste en dessous — même classe de piège que celui corrigé dans review-queue.js
  // (JSON valide, mauvaise forme, jamais vérifiée). Sans ce contrôle, /api/livres ET
  // /api/sante tombaient en 500 générique pour UNE entrée de livre malformée, sans
  // jamais nommer le fichier en cause — alors que les quatre autres lecteurs
  // signaleraient la même situation dans `illisibles`. Une forme inattendue est donc
  // traitée pareil ici : signalée, la page en cause simplement absente du résultat.
  if (base.pages !== undefined && !Array.isArray(base.pages)) {
    illisibles.push(fichier);
    return [];
  }
  return (base.pages ?? []).map((pg, i) => {
    // Un élément `null` est un tableau `pages` par ailleurs valide (donc pas signalé
    // ci-dessus) mais planterait quand même sur `pg.type` (accès de propriété sur
    // null, contrairement à un élément primitif comme une chaîne, qui se contente de
    // renvoyer `undefined`). Replié sur {} : le reste de la fonction la traite alors
    // comme une page sans champ connu, marquée non traduisible — le même repli que
    // pour un type de page hors de CHAMPS_PAR_TYPE, plus bas.
    pg = pg ?? {};
    const type = pg.type ?? "?";
    const noms = (CHAMPS_PAR_TYPE[type] ?? []).filter((n) => litChamp(pg, n) !== undefined);
    const champs = noms.map((nom) => {
      const valeurs = {};
      for (const [loc, d] of Object.entries(parLocale)) {
        const p = d.pages?.[i];
        if (!p) continue;
        const v = litChamp(p, nom);
        if (v !== undefined) valeurs[loc] = v;
      }
      return { nom: nom.trim(), pointeur: `pages/${i}/${nom}`, valeurs };
    });
    const primaire = champs[0] ?? null;
    return {
      index: i,
      type,
      traduisible: champs.length > 0,
      pointeur: primaire?.pointeur ?? null,
      valeurs: primaire?.valeurs ?? {},
      champs,
      // Repli pour un type de page hors de CHAMPS_PAR_TYPE (aucun n'existe
      // actuellement dans les deux livres du pack, mais un type Patchouli non
      // recensé ici ne doit pas planter le lecteur — juste rester marqué non
      // traduisible avec un résumé du mieux qu'on peut, comme le prévoyait déjà
      // le brief d'origine).
      resume: champs.length ? null : (pg.entity ?? pg.item ?? pg.name ?? Object.keys(pg).join(", ")),
    };
  });
}

function langues(dossier, illisibles) {
  const out = {};
  if (!existsSync(dossier)) return out;
  for (const f of readdirSync(dossier)) {
    const loc = basename(f, ".json");
    if (!isLocale(loc)) continue;
    const chemin = join(dossier, f);
    const d = lireJson(chemin);
    if (!d) {
      illisibles.push(chemin);
      continue;
    }
    out[loc] = d;
  }
  return out;
}

// `pack` est injectable (répertoire temporaire) pour les tests, comme readPack/
// readMods/readMeta/readQuests. readBooks() retourne un objet { livres, illisibles },
// aligné sur readMeta()/readQuests() — pas un tableau portant `.illisibles` accroché
// dessus comme une propriété non indicielle. Cette dernière forme a été essayée puis
// abandonnée : elle survit bien à .map/.find en mémoire, mais pas à un aller-retour
// HTTP — JSON.stringify() n'émet que les index numériques d'un tableau, donc
// `.illisibles` disparaît silencieusement dès qu'un appelant sérialise le tableau
// entier vers un client (exactement ce qui s'est produit pour listerMarques() et
// GET /api/revoir : voir review-queue.js et api.js). readBooks() n'est aujourd'hui
// jamais sérialisé tel quel — /api/livres renvoie déjà `.livres` — mais c'était la
// même fragilité, prête à se répéter au premier appelant qui oublierait de la
// contourner ; alignée ici avant qu'elle ne se matérialise une seconde fois.
export function readBooks(pack = PACK) {
  const dossierLivres = join(pack, "patchouli_books");
  const illisibles = [];

  // Les titres de livre (book.json.name) sont des clés de traduction, pas des
  // littéraux ("society.books.almanac.name" → "Almanach du fermier" en fr_fr, "Farmer's
  // Almanac" en en_us) : elles se résolvent dans les fichiers de langue du mod
  // "society", avec repli sur la clé elle-même si elle manque d'une langue — jamais un
  // livre sans titre affichable.
  const titresParLocale = langues(join(pack, "kubejs/assets/society/lang"), illisibles);
  const resoudre = (cle) => {
    const t = {};
    for (const [loc, d] of Object.entries(titresParLocale)) t[loc] = d[cle] ?? cle;
    return t;
  };

  const livres = [];
  if (!existsSync(dossierLivres)) {
    return { livres, illisibles };
  }

  for (const id of readdirSync(dossierLivres)) {
    const dir = join(dossierLivres, id);
    if (!statSync(dir).isDirectory()) continue;
    const locales = readdirSync(dir).filter((n) => isLocale(n) && statSync(join(dir, n)).isDirectory());
    if (!locales.length) continue;
    const ref = locales.includes("fr_fr") ? "fr_fr" : locales[0];

    // book.json est lu au jugé : un miroir partiel du pack peut très bien publier les
    // arbres de langue d'un livre sans son manifeste — c'est le cas du dépôt de
    // traduction, qui ne suit que les arbres fr_fr. Absent, on retombe sur le nom du
    // dossier et la vue reste lisible ; présent mais illisible, c'est un vrai défaut et
    // il est signalé. Sans cette distinction, readFileSync levait une ENOENT qui faisait
    // tomber /api/livres ET /api/sante en 500 dans un dépôt au miroir partiel.
    const cheminBook = join(dir, "book.json");
    const bookJson = existsSync(cheminBook) ? lireJson(cheminBook) : null;
    if (existsSync(cheminBook) && !bookJson) illisibles.push(cheminBook);
    const titre = bookJson?.name ? resoudre(bookJson.name) : { [ref]: id };

    // Une catégorie porte name ET description, toutes deux traduites et propres à
    // chaque arbre de langue (brief d'origine : Categorie n'avait que nom, laissant
    // sept descriptions traduites invisibles). `nom`/`description` restent des
    // chaînes simples (langue de référence) pour la forme attendue par le test
    // ".categories.map(c => c.nom)" ; `noms`/`descriptions` portent la version
    // complète par langue, sur le modèle de EntreeLivre.nom.
    const cats = new Map();
    for (const f of fichiersDe(join(dir, ref, "categories"))) {
      const d = lireJson(f);
      if (!d) {
        illisibles.push(f);
        continue;
      }
      const catId = basename(f, ".json");
      const noms = {};
      const descriptions = {};
      for (const loc of locales) {
        const dl = lireJson(join(dir, loc, "categories", `${catId}.json`));
        if (!dl) continue;
        if (dl.name !== undefined) noms[loc] = dl.name;
        if (dl.description !== undefined) descriptions[loc] = dl.description;
      }
      cats.set(`patchouli:${catId}`, {
        id: catId,
        nom: d.name ?? catId,
        noms,
        description: d.description ?? null,
        descriptions,
        entrees: [],
      });
    }

    for (const f of fichiersDe(join(dir, ref, "entries"))) {
      const rel = relative(join(dir, ref, "entries"), f);
      const base = lireJson(f);
      if (!base) {
        illisibles.push(f);
        continue;
      }

      const parLocale = {};
      for (const loc of locales) {
        const p = join(dir, loc, "entries", rel);
        if (!existsSync(p)) continue; // langue qui n'a simplement pas (encore) cette entrée
        const d = lireJson(p);
        if (!d) {
          illisibles.push(p);
          continue;
        }
        parLocale[loc] = d;
      }

      const nom = {};
      for (const [loc, d] of Object.entries(parLocale)) if (d.name !== undefined) nom[loc] = d.name;

      const entree = {
        chemin: rel,
        nom,
        icone: base.icon ?? null,
        pages: pagesDe(base, parLocale, illisibles, f),
      };

      const cat = cats.get(base.category);
      if (cat) {
        cat.entrees.push(entree);
      } else {
        // Recensé : aucune entrée réelle des deux livres ne référence une catégorie
        // absente. Conservé en défense — une entrée orpheline doit rester visible
        // plutôt que disparaître silencieusement d'un livre par ailleurs complet.
        cats.set(base.category ?? "?", {
          id: base.category ?? "?",
          nom: base.category ?? "Sans catégorie",
          noms: {},
          description: null,
          descriptions: {},
          entrees: [entree],
        });
      }
    }

    for (const c of cats.values()) {
      c.entrees.sort((a, b) =>
        (a.nom.fr_fr ?? a.nom.en_us ?? a.chemin).localeCompare(b.nom.fr_fr ?? b.nom.en_us ?? b.chemin, "fr")
      );
    }

    livres.push({ id, titre, categories: [...cats.values()] });
  }

  return { livres, illisibles };
}
