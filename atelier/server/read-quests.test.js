import { test, expect } from "vitest";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { readQuests } from "./read-quests.js";

const q = readQuests();

test("les quatre groupes du jeu, dans l'ordre du fichier chapter_groups.snbt", () => {
  const titres = q.groupes.slice(1).map(g => g.titre);
  expect(titres).toEqual(["Tutoriel", "Centre communautaire", "Guides", "Collection"]);
});

test("le chapitre Bienvenue est hors groupe et vient en premier, titre lu depuis le fichier de langue", () => {
  // Le titre ne doit rien à une chaîne figée dans le code : ftbquests.chapter.welcome.title
  // se lit en fr_fr comme n'importe quel autre titre de chapitre.
  expect(q.groupes[0].id).toBe("");
  expect(q.groupes[0].titre).toBe("Bienvenue");
});

test("29 chapitres au total", () => {
  expect(q.groupes.flatMap(g => g.chapitres)).toHaveLength(29);
});

test("les titres et sous-titres de chapitre sont traduits", () => {
  const tous = q.groupes.flatMap(g => g.chapitres);
  expect(tous.find(c => c.fichier === "ii__building_up_the_farm").titre).toBeTruthy();
  expect(tous.find(c => c.fichier === "abandoned_farm").titre).toBe("Ferme abandonnée");
  // Correction C : huit chapitres portent un ftbquests.chapter.<fichier>.subtitle0, que
  // le type Chapitre du brief original ne captait pas.
  expect(tous.find(c => c.fichier === "abandoned_farm").sousTitre).toBe("Récompense : Botania débloqué");
  expect(tous.filter(c => c.sousTitre).length).toBe(8);
  // Un chapitre sans subtitle0 ne doit pas afficher de sous-titre inventé.
  expect(tous.find(c => c.fichier === "ii__building_up_the_farm").sousTitre).toBeNull();
});

test("« All on Farming » est dans le chapitre II et non ailleurs", () => {
  const ch = q.groupes.flatMap(g => g.chapitres).find(c => c.fichier === "ii__building_up_the_farm");
  const quete = ch.quetes.find(x => x.titre.en_us === "All on Farming");
  expect(quete).toBeTruthy();
  expect(quete.titre.fr_fr).toBe("Tout sur l'agriculture");
});

// Correction A du brief : le compte de 43 (donné par le brief) est celui des quêtes
// PORTANT UN title: — mesuré, confirmé (43 quêtes titrées sur 67 objets quête bruts dans
// ce chapitre). Il ne doit pas régir le découpage par bloc, qui retient à raison toute
// quête ayant au moins un champ traduisible (title, subtitle, descriptionN, task.N.title…).
//
// Mesuré directement sur le fichier via ce même découpage : 67 quêtes ont au moins un
// champ traduisible dans ce chapitre — pas 61. L'écart de 6 avec le compte donné dans les
// corrections de la tâche vient de la façon dont ces 6 quêtes sont mesurées : leur
// identifiant, dans les clés de langue, a perdu un zéro de tête (ex. la clé porte
// "questA39B0C0A77E57B0", quinze caractères, pour la quête dont le champ id: du .snbt
// vaut "0A39B0C0A77E57B0", seize caractères — voir dependancesDuBloc plus bas, qui doit
// justement composer avec cette perte). Un motif qui n'accepterait que seize caractères
// pile — le même type d'erreur que celui identifié pour dependencies: [...] dans les
// corrections — sous-compte donc aussi les quêtes elles-mêmes, pas seulement leurs
// dépendances. C'était le cas de test-A39B0C0A77E57B0 lui-même : sa propre quête
// ("Préparer les champs") fait partie des 6 non comptées par un motif à seize caractères.
//
// Autre point vérifié : deux chapitres du livre réel (dont celui-ci) sont intégralement
// en fins de ligne CRLF ; sans normalisation, le découpage par bloc n'y trouve aucun
// séparateur et en tire zéro quête. C'est réel (voir read-quests.js) et non un scénario
// de test artificiel.
test("les quêtes masquées sont marquées, pas exclues", () => {
  const ch = q.groupes.flatMap(g => g.chapitres).find(c => c.fichier === "ii__building_up_the_farm");
  expect(ch.quetes.filter(x => x.masquee).length).toBeGreaterThan(30);
  expect(ch.quetes.filter(x => x.masquee).length).toBe(39);
  expect(ch.quetes.length).toBe(67);
  // L'en-tête de chapitre doit pouvoir afficher les deux nombres (traduisibles / bruts)
  // sans qu'aucun ne soit caché : ici les deux coïncident (aucune quête sans texte dans
  // ce chapitre précis), ce qui n'est pas le cas du livre entier (voir plus bas).
  expect(ch.totalQuetes).toBe(67);
});

test("une quête porte ses descriptions dans plusieurs langues", () => {
  const ch = q.groupes.flatMap(g => g.chapitres).find(c => c.fichier === "ii__building_up_the_farm");
  const quete = ch.quetes.find(x => x.titre.en_us === "All on Farming");
  const d1 = quete.champs.find(c => c.nom === "description1");
  expect(d1.valeurs.fr_fr).toMatch(/Almanach du fermier/);
  expect(d1.valeurs.en_us).toMatch(/Farmer's Almanac/);
});

// Correction B du brief : dependencies: [...] est un tableau dédié du bloc, à lire
// spécifiquement — un motif appliqué à tout le bloc capturerait aussi l'identifiant de
// la quête elle-même et ceux de ses tâches/récompenses. Et les identifiants qu'il
// contient ne font pas tous seize caractères une fois ramenés à la forme utilisée par
// les clés de langue (zéros de tête perdus) : la dépendance doit être normalisée pour
// se résoudre dans parQuete. Verrouillée ici sur une dépendance réelle du fichier —
// "Premiers semis" (quest6ADD884F3FFE5D42) dépend de "Préparer les champs"
// (quest0A39B0C0A77E57B0 dans le .snbt, quinze caractères une fois sans son zéro de tête).
test("une dépendance réelle se résout dans parQuete, zéro de tête compris", () => {
  const premiersSemis = q.parQuete.get("quest6ADD884F3FFE5D42");
  expect(premiersSemis.titre.fr_fr).toBe("Premiers semis");
  expect(premiersSemis.dependances).toEqual(["questA39B0C0A77E57B0"]);
  const cible = q.parQuete.get(premiersSemis.dependances[0]);
  expect(cible).toBeTruthy();
  expect(cible.titre.fr_fr).toBe("Préparer les champs");
});

test("47 quêtes masquées au total dans le livre, pas seulement au chapitre II", () => {
  const total = q.groupes.flatMap(g => g.chapitres).flatMap(c => c.quetes).filter(x => x.masquee).length;
  expect(total).toBe(47);
});

// Un chapitre entièrement en CRLF, distinct de celui déjà couvert ci-dessus : sans la
// normalisation des fins de ligne, le découpage par bloc y échouerait aussi.
test("getting_started (l'autre chapitre en CRLF) n'est pas vide", () => {
  const ch = q.groupes.flatMap(g => g.chapitres).find(c => c.fichier === "getting_started");
  expect(ch.quetes.length).toBeGreaterThan(0);
});

// Le livre entier compte largement plus d'objets quête bruts que de quêtes traduisibles
// (beaucoup de jalons de collection ne portent qu'une icône, sans aucun champ de texte).
// Ce test vérifie que l'écart existe et reste honnête au niveau du livre — contrairement
// au chapitre II où, mesuré, cet écart se trouve être nul.
test("le livre entier a plus d'objets quête bruts que de quêtes traduisibles", () => {
  const tous = q.groupes.flatMap(g => g.chapitres);
  const totalBrut = tous.reduce((a, c) => a + c.totalQuetes, 0);
  const totalTraduisible = tous.reduce((a, c) => a + c.quetes.length, 0);
  expect(totalTraduisible).toBe(528);
  expect(totalBrut).toBeGreaterThan(totalTraduisible);
});

test("un fichier de langue illisible même après tolérance aux commentaires est signalé, pas ignoré", () => {
  const tmp = mkdtempSync(join(tmpdir(), "read-quests-illisible-"));
  try {
    const dirLang = join(tmp, "kubejs/assets/ftbquestlocalizer/lang");
    const dirQuetes = join(tmp, "config/ftbquests/quests/chapters");
    mkdirSync(dirLang, { recursive: true });
    mkdirSync(dirQuetes, { recursive: true });
    // JSON tronqué : aucun commentaire à retirer, reste invalide après tolérance.
    writeFileSync(join(dirLang, "fr_fr.json"), '{"a": "b"');
    writeFileSync(join(dirLang, "en_us.json"), "{}");
    writeFileSync(join(tmp, "config/ftbquests/quests/chapter_groups.snbt"), "{ chapter_groups: [] }");
    writeFileSync(
      join(dirQuetes, "vide.snbt"),
      '{\n\tfilename: "vide"\n\tgroup: ""\n\torder_index: 0\n\tquests: [\n\t]\n}'
    );

    const r = readQuests(tmp);
    const chemin = join(dirLang, "fr_fr.json");

    expect(r.illisibles).toContain(chemin);
    // Le fichier lisible (en_us.json, vide) ne doit pas disparaître pour autant : le
    // chapitre se construit quand même, juste sans traduction française.
    expect(r.groupes.flatMap(g => g.chapitres)).toHaveLength(1);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

// Le vrai défaut corrigé ici : QUESTS_CONFIG (chapter_groups.snbt et chapters/) est l'une
// des quatre racines réglables de l'atelier (paths.js), réglable indépendamment de PACK —
// un utilisateur peut avoir le pack sans avoir la config des quêtes. Avant ce correctif,
// son absence faisait lever readFileSync(chapter_groups.snbt) ou readdirSync(chapters) —
// une ENOENT non rattrapée qui faisait tomber /api/sante ET /api/quetes en 500. Un livre
// de quêtes vide et un signalement dans `manquantes`, jamais une exception.
test("une config des quêtes absente ne lève pas — livre vide, signalé dans manquantes", () => {
  const tmp = mkdtempSync(join(tmpdir(), "read-quests-pack-"));
  const questsConfigAbsent = join(tmp, "config/ftbquests/quests");
  try {
    // Le pack existe (titres de quêtes lisibles), seule la config des quêtes manque —
    // le scénario « pack présent, config des quêtes absente » que la tâche demande de
    // vérifier contre le serveur réel.
    mkdirSync(join(tmp, "kubejs/assets/ftbquestlocalizer/lang"), { recursive: true });
    writeFileSync(join(tmp, "kubejs/assets/ftbquestlocalizer/lang/fr_fr.json"), "{}");

    const r = readQuests(tmp, questsConfigAbsent);

    expect(r.groupes).toEqual([]);
    expect(r.parQuete.size).toBe(0);
    expect(r.illisibles).toEqual([]);
    expect(r.manquantes).toHaveLength(1);
    expect(r.manquantes[0]).toContain(questsConfigAbsent);
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});

// Le repli symétrique : la config des quêtes est là, mais le pack (donc les titres de
// quêtes, ftbquestlocalizer/lang) ne l'est pas — un cas plus délibérément dégradé que
// « pack absent » (readPack le signalerait déjà lui-même côté vue Clés), vérifié ici pour
// s'assurer que readQuests() ne lève pas non plus dans ce sens : le livre se construit,
// juste sans titre traduit.
test("des titres de quêtes absents (pack incomplet) ne lèvent pas — chapitres sans traduction", () => {
  const tmp = mkdtempSync(join(tmpdir(), "read-quests-sans-titres-"));
  try {
    const dirQuetes = join(tmp, "config/ftbquests/quests/chapters");
    mkdirSync(dirQuetes, { recursive: true });
    writeFileSync(join(tmp, "config/ftbquests/quests/chapter_groups.snbt"), "{ chapter_groups: [] }");
    writeFileSync(
      join(dirQuetes, "vide.snbt"),
      '{\n\tfilename: "vide"\n\tgroup: ""\n\torder_index: 0\n\tquests: [\n\t]\n}'
    );

    // Aucun kubejs/assets/ftbquestlocalizer/lang sous tmp : dossierLangues est absent.
    const r = readQuests(tmp);

    expect(r.manquantes).toEqual([]);
    expect(r.groupes.flatMap(g => g.chapitres)).toHaveLength(1);
    expect(r.groupes[0].titre).toBe("welcome"); // repli sur le nom, aucun fichier de langue à lire
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
});
