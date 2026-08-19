import { watch } from "node:fs";
import { relative } from "node:path";
import { buildKeyIndex } from "./index-build.js";
import { localeLabel } from "./locales.js";
import { readMeta, evenementsPourNamespace } from "./read-meta.js";
import { readQuests } from "./read-quests.js";
import { readBooks } from "./read-books.js";
import { search } from "./search.js";
import { writeLangEntry, validerValeur } from "./write-entry.js";
import { listerMarques, ajouterMarque, retirerMarque, correspondMarque, messageIllisible } from "./review-queue.js";
import { PACK, EXTRACTED, WORKSPACE, QUESTS_CONFIG } from "./paths.js";

let idx = null;
let construitLe = 0;
let meta = null;
let quetes = null;
let livres = null;

// buildKeyIndex() (donc readPack/readMods), readMeta(), readQuests() et readBooks()
// collectent chacun leurs fichiers illisibles dans `illisibles`, mais jusqu'ici
// personne ne les lisait : un provenance.json corrompu retombait en silence sur une
// provenance vide, et rien ne le distinguait d'une absence légitime de décisions.
// index(), metadonnees(), quetesFn() et livresFn() sont le point unique où les cinq
// lecteurs se rejoignent — c'est là qu'on journalise, via creerJournal() ; la liste
// elle-même repart avec l'index/les métadonnées/les quêtes/les livres vers /sante.
// readBooks() retourne { livres, illisibles }, aligné sur readMeta()/readQuests() —
// livresFn() ne garde en cache QUE le tableau `livres` (voir plus bas) : `.illisibles`
// serait sinon accroché à un tableau exposé tel quel par GET /api/livres, et
// disparaîtrait silencieusement au premier JSON.stringify (exactement le défaut que
// review-queue.js/listerMarques() reproduisait pour GET /api/revoir).
//
// Une invalidation de cache reconstruit l'index ou les métadonnées à la requête
// suivante ; si le fichier en cause reste corrompu, une reconstruction ultérieure
// déclenchée par un tout autre fichier du dossier surveillé retrouverait la même
// liste. On ne réémet donc le message que si la liste a changé depuis la dernière
// fois — sinon la répétition finirait, elle aussi, par se lire comme du bruit qu'on
// ignore, soit un silence par un autre chemin.
function creerJournal(formater) {
  let dernier = [];
  return (liste) => {
    const identique = liste.length === dernier.length &&
      [...liste].sort().every((c, i) => c === [...dernier].sort()[i]);
    if (liste.length && !identique) console.error(formater(liste));
    dernier = liste;
  };
}

const journalIllisibles = (etiquette) =>
  creerJournal((l) => `${etiquette} : ${l.length} fichier(s) illisible(s) — ${l.join(", ")}`);

const journalIndex = journalIllisibles("Index des clés");
const journalMeta = journalIllisibles("Métadonnées (fr-workspace)");
const journalQuetes = journalIllisibles("Quêtes (ftbquests)");
const journalLivres = journalIllisibles("Livres (patchouli_books)");

// Distinct de `illisibles` (fichier présent mais corrompu) : une racine absente n'est
// pas un fichier illisible, elle a donc son propre journal plutôt que de se retrouver
// mélangée aux quatre ci-dessus — même signalement (console + /api/sante), forme
// différente. Alimenté depuis /sante, qui construit déjà les quatre sources.
const journalManquantes = creerJournal((l) => `Sources absentes : ${l.join(" — ")}`);

function index() {
  if (!idx) {
    idx = buildKeyIndex();
    construitLe = Date.now();
    journalIndex(idx.illisibles);
  }
  return idx;
}

function metadonnees() {
  if (!meta) {
    meta = readMeta();
    journalMeta(meta.illisibles);
  }
  return meta;
}

function quetesFn() {
  if (!quetes) {
    // QUESTS_CONFIG passé explicitement (plutôt que de laisser readQuests() retomber sur
    // son défaut dérivé de `pack`) : c'est ce qui permet à ATELIER_QUESTS_CONFIG de régler
    // la configuration des quêtes indépendamment de ATELIER_PACK (voir paths.js).
    quetes = readQuests(PACK, QUESTS_CONFIG);
    journalQuetes(quetes.illisibles);
  }
  return quetes;
}

function livresFn() {
  if (!livres) {
    livres = readBooks();
    journalLivres(livres.illisibles);
  }
  return livres;
}

// Un changement sur disque invalide l'index, les métadonnées, le livre de quêtes et/ou
// les livres Patchouli ; ils se reconstruisent à la requête suivante. Reconstruire
// immédiatement gaspillerait du travail quand plusieurs fichiers changent d'affilée.
//
// Correctif mesuré : l'ancienne version remettait les QUATRE caches à zéro pour
// n'importe quel événement sur n'importe laquelle des cinq racines — 1,45 s sur la
// requête qui suit un marquage (qui n'écrit que a-revoir.json, donc ne concerne que
// `meta`), 1,13 s après avoir seulement touché un fichier de livre (qui ne concerne que
// `livres`). Chaque racine n'invalide maintenant que les caches qu'elle nourrit
// réellement — voir la correspondance ci-dessous, établie en lisant ce que readPack()/
// readMods()/readMeta()/readQuests()/readBooks() lisent effectivement sur disque, pas
// en la devinant :
//
//  - kubejs/assets/       → idx (readPack() y lit TOUS les namespaces, sans exception).
//    Deux sous-dossiers y portent EN PLUS des données lues par un second lecteur :
//    ftbquestlocalizer/lang (titres de quêtes, readQuests()) et society/lang (titres de
//    livres, readBooks() — voir le commentaire en tête de read-books.js). `filename`,
//    fourni par fs.watch en mode recursif et relatif à la racine surveillée, distingue
//    ces deux sous-chemins pour n'invalider quetes/livres que quand ils sont
//    effectivement concernés — un fichier de langue de n'importe quel autre mod n'a
//    aucune raison de reconstruire le livre de quêtes ou les livres Patchouli. Node ne
//    garantit pas `filename` sur toutes les plateformes : s'il manque, on invalide les
//    deux par prudence plutôt que de sous-invalider silencieusement.
//  - extracted/           → idx seul (readMods() ne lit que ça).
//  - fr-workspace/         → meta seul (readMeta() ne lit que provenance.json et
//    a-revoir.json, à sa racine). Piège à éviter ici, signalé en revue : fr-workspace/
//    contient aussi extracted/, qui nourrit l'index des clés — le rôle d'idx n'est PAS
//    oublié pour autant, il reste couvert par la racine extracted/ ci-dessus, surveillée
//    séparément ; ce n'est donc pas une sous-invalidation, seulement une redondance
//    évitée.
//  - QUESTS_CONFIG (config/ftbquests/quests par défaut, réglable séparément de PACK —
//    voir paths.js) → quetes seul (structure du livre de quêtes : chapitres, dépendances,
//    groupes).
//  - patchouli_books/     → livres seul (pages des deux livres Patchouli).
function observer() {
  const surAssets = (event, filename) => {
    idx = null;
    const rel = filename ? filename.replaceAll("\\", "/") : null;
    if (rel === null || rel.startsWith("ftbquestlocalizer/lang")) quetes = null;
    if (rel === null || rel.startsWith("society/lang")) livres = null;
  };
  const racines = [
    [`${PACK}/kubejs/assets`, surAssets],
    [EXTRACTED, () => { idx = null; }],
    [WORKSPACE, () => { meta = null; }],
    [QUESTS_CONFIG, () => { quetes = null; }],
    [`${PACK}/patchouli_books`, () => { livres = null; }],
  ];
  for (const [racine, invalider] of racines) {
    try { watch(racine, { recursive: true }, invalider); } catch {}
  }
}

function json(res, corps, code = 200) {
  res.statusCode = code;
  res.setHeader("content-type", "application/json; charset=utf-8");
  res.end(JSON.stringify(corps));
}

export function apiPlugin() {
  return {
    name: "atelier-api",
    configureServer(serveur) {
      observer();
      serveur.middlewares.use("/api", (req, res, next) => {
        try {
          const url = new URL(req.url, "http://local");
          const p = url.pathname;

          if (p === "/sante") {
            const i = index();
            // /sante construit aussi les métadonnées, le livre de quêtes et les livres
            // Patchouli : c'est la route d'état de l'application, elle doit pouvoir
            // signaler un provenance.json corrompu ou un fichier de langue illisible
            // (quêtes ou livres) sans attendre qu'une sélection dans le panneau de
            // détail ou l'onglet Quêtes/Livres le déclenche.
            const md = metadonnees();
            const qt = quetesFn();
            const lv = livresFn();
            // `manquantes` (racines absentes : PACK/EXTRACTED via l'index, QUESTS_CONFIG
            // via les quêtes) est distinct de `illisibles` (fichier présent mais corrompu) —
            // voir read-pack.js/read-mods.js/read-quests.js. readMeta()/readBooks() n'en
            // produisent pas : elles dégradent déjà en silence sans jamais planter, donc
            // rien à signaler de cette nature-là pour WORKSPACE ou patchouli_books/.
            const manquantes = [...i.manquantes, ...qt.manquantes];
            journalManquantes(manquantes);
            return json(res, {
              fichiers: i.entrees.length, locales: i.locales.length,
              construitLe, ages: Date.now() - construitLe,
              quetes: qt.parQuete.size,
              livres: lv.livres.length,
              illisibles: [...i.illisibles, ...md.illisibles, ...qt.illisibles, ...lv.illisibles],
              manquantes,
            });
          }
          if (p === "/locales") {
            return json(res, index().locales.map(c => ({ code: c, libelle: localeLabel(c) })));
          }
          if (p === "/quetes") return json(res, quetesFn().groupes);
          if (p === "/livres") return json(res, livresFn().livres);
          if (p === "/recherche") {
            const g = k => url.searchParams.get(k) ?? undefined;
            const liste = k => (url.searchParams.get(k) ?? "").split(",").filter(Boolean);
            return json(res, search(index(), {
              q: g("q"), champ: g("champ"), ns: g("ns"), origine: g("origine"),
              avec: liste("avec"), sans: liste("sans"), portee: g("portee"),
              limite: g("limite"), offset: g("offset"),
            }));
          }
          if (p.startsWith("/entree/")) {
            // decodeURIComponent lève une URIError sur une séquence % mal formée :
            // c'est une entrée client invalide (400), pas une panne serveur.
            let id;
            try { id = decodeURIComponent(p.slice("/entree/".length)); }
            catch { return json(res, { erreur: "Identifiant mal encodé" }, 400); }
            const e = index().parId.get(id);
            return e ? json(res, e) : json(res, { erreur: "Entrée introuvable" }, 404);
          }
          if (p.startsWith("/detail/")) {
            // Même garde que /entree/ : une séquence % mal formée est une entrée
            // client invalide (400), pas une panne serveur.
            let id;
            try { id = decodeURIComponent(p.slice("/detail/".length)); }
            catch { return json(res, { erreur: "Identifiant mal encodé" }, 400); }
            const e = index().parId.get(id);
            if (!e) return json(res, { erreur: "Entrée introuvable" }, 404);
            const md = metadonnees();
            // provenance.json indexe par clé nue, sans namespace : deux mods qui
            // choisissent le même identifiant (63 clés réelles) partagent la même
            // entrée. On écarte les événements dont `fichier` désigne un autre
            // namespace, et on prévient plutôt que de présenter comme établie une
            // attribution qu'on ne peut pas confirmer.
            const brut = md.provenance.get(e.cle) ?? [];
            const evenements = evenementsPourNamespace(brut, e.ns);
            const namespaces = new Set((index().parCle.get(e.cle) ?? []).map(x => x.ns));
            const attributionIncertaine = namespaces.size > 1 && evenements.some(ev => !ev.fichier);
            return json(res, {
              entree: e,
              provenance: { evenements, attributionIncertaine, namespaces: namespaces.size },
              glossaire: md.termesDe(e.source.en ?? e.traductions.fr_fr),
              // Une marque posée depuis le site porte l'id complet (lang:ns:cle) :
              // on la retrouve par cet id. Une marque antérieure au champ id n'a
              // que sa clé nue et son `fichier` pour se faire reconnaître —
              // correspondMarque (review-queue.js) vérifie aussi que ce fichier
              // désigne bien le namespace courant avant d'attribuer la marque à
              // cette entrée, pour ne jamais la présenter à tort comme celle d'un
              // autre mod sur une clé partagée (422 clés réelles dans ce cas).
              marque: md.aRevoir.find(r => correspondMarque(r, { id: e.id, cle: e.cle, ns: e.ns })) ?? null,
            });
          }
          if (p === "/corriger" && req.method === "POST") {
            let corps = "";
            req.on("data", c => (corps += c));
            req.on("end", () => {
              // JSON.parse et la validation de forme tournent dans ce rappel, donc en
              // dehors du try/catch de l'intergiciel ci-dessous : un corps mal formé ou
              // de forme inattendue doit être une réponse 400, jamais une exception non
              // attrapée qui ferait tomber le serveur (même logique que les gardes
              // decodeURIComponent de /entree/ et /detail/ ci-dessus).
              let payload;
              try { payload = JSON.parse(corps || "{}"); }
              catch { return json(res, { erreur: "Corps de requête mal formé (JSON invalide)" }, 400); }
              const { id, valeur } = payload;
              if (typeof id !== "string" || typeof valeur !== "string")
                return json(res, { erreur: "Corps de requête invalide : id et valeur doivent être des chaînes" }, 400);
              const e = index().parId.get(id);
              if (!e) return json(res, { erreur: "Entrée introuvable" }, 404);
              const problemes = validerValeur({ en: e.source.en, fr: valeur, cle: e.cle });
              if (problemes.length) return json(res, { ok: false, problemes }, 422);
              const r = writeLangEntry({ fichier: e.emplacement.fichier, cle: e.cle, valeur });
              if (r.ok) idx = null;  // l'observateur le ferait aussi, mais on veut la fraîcheur immédiate
              return json(res, r, r.ok ? 200 : 500);
            });
            return;
          }
          if (p === "/revoir" && req.method === "GET") {
            // listerMarques() renvoie un tableau portant `.illisibles` accroché dessus
            // (même forme que readBooks() avant son alignement plus haut) : JSON.stringify
            // n'émet que les index numériques d'un tableau, donc envoyer ce tableau tel
            // quel au client fait disparaître `.illisibles` en silence — la route répond
            // 200 avec une liste vide, indiscernable d'une file réellement vide, alors
            // qu'a-revoir.json est corrompu. On vérifie donc `.illisibles` ICI, côté
            // serveur, avant de sérialiser, et on répond 500 avec le même message
            // explicite que ajouterMarque()/retirerMarque() refusent déjà d'écraser.
            const m = listerMarques();
            if (m.illisibles.length) return json(res, { erreur: messageIllisible(m.illisibles[0]) }, 500);
            return json(res, m);
          }
          if (p === "/revoir" && req.method === "POST") {
            let corps = "";
            req.on("data", c => (corps += c));
            req.on("end", () => {
              // Même garde que /corriger ci-dessus : JSON.parse tourne dans ce
              // rappel, donc hors du try/catch de l'intergiciel — un corps mal
              // formé doit être une réponse 400, jamais une exception non
              // attrapée qui ferait tomber le serveur.
              let payload;
              try { payload = JSON.parse(corps || "{}"); }
              catch { return json(res, { erreur: "Corps de requête mal formé (JSON invalide)" }, 400); }
              const { id, note, pour } = payload;
              if (typeof id !== "string")
                return json(res, { erreur: "Corps de requête invalide : id doit être une chaîne" }, 400);
              const e = index().parId.get(id);
              if (!e) return json(res, { erreur: "Entrée introuvable" }, 404);
              // e.traductions.fr_fr est undefined pour les 8822 clés sans français
              // (voir index-build.js) : sans ce repli, le champ fr_actuel
              // disparaîtrait de l'entrée JSON écrite (JSON.stringify élague les
              // valeurs undefined), changeant la forme du fichier selon la clé.
              //
              // e.emplacement.fichier est absolu (chemin réel sur disque, utile à
              // writeLangEntry) ; l'entrée réelle de a-revoir.json, elle, porte un
              // chemin relatif au pack ("kubejs/assets/.../fr_fr.json") — écrire
              // l'absolu changerait la forme du fichier au premier marquage et
              // ferait fuiter le chemin local de l'utilisateur dans un fichier
              // suivi par git. `ns` (e.ns) permet à ajouterMarque de distinguer
              // une marque antérieure du même mod de celle d'un autre mod partageant
              // la même clé nue (voir correspondMarque, review-queue.js).
              const r = ajouterMarque({
                id: e.id, cle: e.cle, ns: e.ns, fichier: relative(PACK, e.emplacement.fichier),
                fr_actuel: e.traductions.fr_fr ?? "", note, pour,
              });
              if (!r.ok) return json(res, { erreur: r.erreur }, 500);
              meta = null;  // la file change : le détail doit la relire
              return json(res, r.entree);
            });
            return;
          }
          if (p.startsWith("/revoir/") && req.method === "DELETE") {
            // Même garde que /entree/ et /detail/ : une séquence % mal formée est
            // une entrée client invalide (400), pas une panne serveur.
            let identifiant;
            try { identifiant = decodeURIComponent(p.slice("/revoir/".length)); }
            catch { return json(res, { erreur: "Identifiant mal encodé" }, 400); }
            const r = retirerMarque(identifiant);
            if (!r.ok) return json(res, { erreur: r.erreur }, 500);
            meta = null;  // la file change : le détail doit la relire
            return json(res, { retire: r.retire });
          }
          next();
        } catch (err) {
          // Défaut imprévu du serveur : jamais de trace d'appels dans la réponse.
          console.error(err);
          json(res, { erreur: "Erreur interne" }, 500);
        }
      });
    },
  };
}
