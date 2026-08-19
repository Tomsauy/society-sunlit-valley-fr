// site/server/read-quests.js
import { readdirSync, readFileSync, existsSync } from "node:fs";
import { join, basename } from "node:path";
import { PACK, QUESTS_CONFIG } from "./paths.js";
import { parseLang } from "./parse-lang.js";
import { isLocale } from "./locales.js";

// La structure du livre n'est PAS dans les fichiers de langue : elle se reconstitue
// depuis chapter_groups.snbt (groupes et leur ordre), chaque chapters/*.snbt (groupe
// d'appartenance, order_index) et le fichier de langue pour les titres, reliés par le
// NOM DE FICHIER du chapitre.
//
// `pack` et `questsConfig` sont injectables (répertoire temporaire) pour les tests, comme
// readPack/readMods/readMeta ; en usage normal ils valent PACK et QUESTS_CONFIG. Le
// deuxième défaut par rapport à `pack` (pas à la constante QUESTS_CONFIG) pour qu'un
// appel à un seul argument — la forme qu'utilisent déjà les tests existants — retrouve
// la config des quêtes SOUS le même répertoire temporaire, sans avoir à répéter le
// chemin ; l'appelant réel (api.js) passe les deux constantes explicitement, pour que
// QUESTS_CONFIG reste réglable indépendamment de PACK (cf. paths.js).
//
// La configuration des quêtes (questsConfig — chapter_groups.snbt et chapters/) est une
// des quatre racines réglables de l'atelier (paths.js) : absente, elle ne doit ni faire
// planter le lecteur ni se confondre avec un fichier illisible — un livre de quêtes vide
// et un signalement dans `manquantes`, comme readPack()/readMods() pour PACK/EXTRACTED.
// Les titres de quêtes (dossierLangues, sous `pack`) restent, eux, tolérés en silence
// s'ils manquent — même repli que readBooks() pour ses propres sous-dossiers : les
// chapitres se construisent quand même, juste sans traduction.
export function readQuests(pack = PACK, questsConfig = join(pack, "config/ftbquests/quests")) {
  const dossierLangues = join(pack, "kubejs/assets/ftbquestlocalizer/lang");

  if (!existsSync(join(questsConfig, "chapter_groups.snbt")) || !existsSync(join(questsConfig, "chapters"))) {
    return {
      groupes: [], parQuete: new Map(), illisibles: [],
      manquantes: [
        `Configuration des quêtes introuvable : ${questsConfig} — livre de quêtes indisponible ` +
        `(ATELIER_QUESTS_CONFIG pour corriger).`,
      ],
    };
  }
  const dossierQuetes = questsConfig;

  const { locales: L, illisibles } = langues(dossierLangues);
  const fr = L.fr_fr ?? {};
  const val = (cle) => Object.fromEntries(
    Object.entries(L).filter(([, d]) => d[cle] !== undefined).map(([loc, d]) => [loc, d[cle]]));

  // groupes, dans l'ordre du fichier chapter_groups.snbt. "welcome" est le seul chapitre
  // hors groupe (group: "" dans son .snbt) : son titre se lit comme celui de n'importe
  // quel autre chapitre — ftbquests.chapter.welcome.title — plutôt que d'être figé en
  // dur dans le code d'un outil qui affiche par ailleurs douze langues ; repli sur le nom
  // de fichier si la clé venait à disparaître du fichier de langue.
  const grpTxt = normaliserFinsDeLigne(readFileSync(join(dossierQuetes, "chapter_groups.snbt"), "utf8"));
  const groupes = [{ id: "", titre: fr["ftbquests.chapter.welcome.title"] ?? "welcome", chapitres: [] }];
  for (const m of grpTxt.matchAll(/id:\s*"([0-9A-F]+)",\s*title:\s*"\{([^}]+)\}"/g)) {
    groupes.push({ id: m[1], titre: fr[m[2]] ?? m[2], chapitres: [] });
  }
  const parGroupe = new Map(groupes.map(g => [g.id, g]));
  const parQuete = new Map();

  for (const f of readdirSync(join(dossierQuetes, "chapters"))) {
    if (!f.endsWith(".snbt")) continue;
    const fichier = basename(f, ".snbt");
    // Deux chapitres du livre réel (dont ii__building_up_the_farm, le plus scruté par
    // les tests) sont entièrement en fins de ligne CRLF, contre LF pour tous les autres —
    // sans doute l'éditeur d'un contributeur Windows. readFileSync ne les normalise pas :
    // laissé tel quel, le découpage par bloc ci-dessous (qui cherche "\n\t\t{\n") ne
    // trouve alors aucun séparateur dans ces deux fichiers et en tire zéro quête, pas une
    // erreur visible — le genre de silence que ce projet a déjà payé cher (190 clés de
    // vintagedelight, cf. parse-lang.js).
    const txt = normaliserFinsDeLigne(readFileSync(join(dossierQuetes, "chapters", f), "utf8"));
    const tete = enTete(txt);
    const gid = tete.match(/group:\s*"([0-9A-F]*)"/)?.[1] ?? "";
    const ordre = Number(tete.match(/order_index:\s*(-?\d+)/)?.[1] ?? 999);
    const icone = tete.match(/icon:\s*"([^"]+)"/)?.[1] ?? null;

    // Un bloc de quête commence à une accolade indentée de trois tabulations, à
    // l'intérieur du tableau quests: — ce découpage n'est pas remis en cause : il retient
    // bien les quêtes portant au moins un champ traduisible (voir plus bas), et c'est le
    // compte qui compte pour un explorateur de traductions, pas le nombre brut d'objets
    // du livre.
    const blocs = txt.split(/\n\t\t\{\n/).slice(1);
    const quetes = [];
    for (const bloc of blocs) {
      // L'identifiant de quête tel qu'il apparaît DANS LES CLÉS DE LANGUE perd ses zéros
      // de tête (contrairement au champ id: du bloc, toujours seize caractères) : il faut
      // donc l'extraire en longueur variable, jamais fixée à seize, pour ne manquer
      // aucune des quêtes dont la forme courte fait quinze ou quatorze caractères.
      const ids = [...bloc.matchAll(new RegExp(`ftbquests\\.chapter\\.${fichier}\\.(quest[0-9A-F]+)\\.`, "g"))];
      if (!ids.length) continue;  // aucun champ traduisible : rien à relire, hors de l'explorateur
      const questId = ids[0][1];
      const prefixe = `ftbquests.chapter.${fichier}.${questId}`;
      const champs = [];
      const vus = new Set();
      for (const m of bloc.matchAll(new RegExp(`${prefixe}\\.([a-zA-Z0-9_.]+)\\}`, "g"))) {
        const nom = m[1];
        if (vus.has(nom)) continue;
        vus.add(nom);
        champs.push({ nom, cle: `${prefixe}.${nom}`, valeurs: val(`${prefixe}.${nom}`) });
      }

      const quete = {
        questId, chapitre: fichier,
        titre: val(`${prefixe}.title`),
        champs,
        masquee: /hide_until_deps_complete:\s*true/.test(bloc),
        dependances: dependancesDuBloc(bloc),
      };
      quetes.push(quete);
      parQuete.set(questId, quete);
    }

    const chapitre = {
      fichier, ordre, icone,
      titre: fr[`ftbquests.chapter.${fichier}.title`] ?? fichier,
      sousTitre: fr[`ftbquests.chapter.${fichier}.subtitle0`] ?? null,
      quetes,
      // Total brut d'objets quête du chapitre (avant le filtre "au moins un champ
      // traduisible") : l'écart avec quetes.length ne doit jamais être masqué à
      // l'utilisateur — deux corrections précédentes sur cette arborescence sont déjà
      // parties d'un désaccord entre ce que le livre en jeu montre et ce que l'outil
      // affichait. La vue affiche les deux nombres plutôt que de n'en garder qu'un.
      totalQuetes: blocs.length,
    };
    (parGroupe.get(gid) ?? parGroupe.get("")).chapitres.push(chapitre);
  }

  for (const g of groupes) g.chapitres.sort((a, b) => a.ordre - b.ordre);
  return { groupes, parQuete, illisibles, manquantes: [] };
}

function langues(dossierLangues) {
  const locales = {};
  // Un fichier de langue illisible même après la tolérance aux commentaires de
  // parseLang est signalé, jamais ignoré en silence — même principe que read-pack.js,
  // read-mods.js et read-meta.js : api.js journalise cette liste et la publie dans
  // /api/sante.
  const illisibles = [];
  // dossierLangues absent (pack incomplet, ou renommé — cf. le repli documenté en tête
  // de readQuests) : mêmes titres de secours que readBooks() pour ses propres
  // sous-dossiers manquants (nom de fichier / clé brute), pas un signalement dédié —
  // seule `questsConfig`, la racine réglable de ce lecteur, en porte un.
  if (!existsSync(dossierLangues)) return { locales, illisibles };
  for (const f of readdirSync(dossierLangues)) {
    const loc = basename(f, ".json");
    if (!isLocale(loc)) continue;
    const chemin = join(dossierLangues, f);
    const { data } = parseLang(readFileSync(chemin, "utf8"));
    if (!data) { illisibles.push(chemin); continue; }
    locales[loc] = data;
  }
  return { locales, illisibles };
}

const normaliserFinsDeLigne = (txt) => txt.replace(/\r\n/g, "\n");

const enTete = (txt) => {
  const i = txt.indexOf("\n\tquests:");
  return i > 0 ? txt.slice(0, i) : txt;
};

// Un identifiant de dépendance stocké dans dependencies: [...] fait toujours seize
// caractères dans le .snbt (zéros de tête compris), alors que le même identifiant, une
// fois passé par le générateur de clés de langue, les a perdus (ex. "0A39B0C0A77E57B0"
// en dépendance désigne la même quête que la clé "...questA39B0C0A77E57B0...", quinze
// caractères). Sans cette normalisation, une dépendance sur seize caractères ne
// retrouverait jamais sa cible dans parQuete, qui indexe par la forme courte — et
// l'utilisateur ne saurait plus pourquoi une quête masquée reste masquée.
//
// Le préfixe "quest" est ajouté pour retrouver exactement la forme de questId : le
// groupe capturé par le motif ids ci-dessus (quest[0-9A-F]+) l'inclut déjà, et parQuete
// indexe par cette forme complète — sans le préfixe, aucune dépendance ne s'y résoudrait
// jamais malgré une normalisation par ailleurs correcte.
const normaliserId = (id) => `quest${id.replace(/^0+(?=[0-9A-F])/, "")}`;

// dependencies: [...] est un tableau dédié du bloc, distinct de tout le reste : le lire
// spécifiquement (plutôt qu'un motif appliqué à bloc entier) évite de capturer
// l'identifiant de la quête elle-même ainsi que ceux de ses tâches et de ses
// récompenses, qui portent eux aussi des chaînes hexadécimales entre guillemets.
function dependancesDuBloc(bloc) {
  const brut = bloc.match(/dependencies:\s*\[([^\]]*)\]/)?.[1] ?? "";
  return [...brut.matchAll(/"([0-9A-F]+)"/g)].map(m => normaliserId(m[1]));
}
