// site/src/lib/mc-render.js
//
// Rendu HTML de l'aperçu « en jeu » des textes du modpack, et comparaison des codes de
// mise en forme entre deux langues d'un même champ.
//
// Deux dialectes cohabitent dans le pack et ne se mélangent JAMAIS dans un même champ
// (mesuré sur society-sunlit-valley, pas juste supposé) :
//   - "quest"     (FTB Quests / FTBQuestLocalizer, kubejs/assets/ftbquestlocalizer/lang) :
//                 codes `&x` (couleur/gras/italique/soulignement/barré/brouillé/reset) et,
//                 par convention Minecraft standard, `§x` — jamais observé dans ce corpus
//                 mais couvert au même titre que &, pour la même raison que les couleurs
//                 hors palette : dégrader proprement plutôt que planter si l'un des douze
//                 fichiers de langue venait à en contenir. `\&` échappe un "&" littéral —
//                 44 occurrences réelles dans les douze langues ("Butterfly \& Moth"), pas
//                 documenté dans le brief, découvert en creusant le corpus.
//   - "patchouli" (patchouli_books/*/​{lang}/entries|categories) : balises `$(...)` — gras
//                 $(l)/$() (806 dans almanac+fish_finder, toutes langues confondues, count
//                 réel), puce $(li) (1936), sauts de ligne $(br)/$(br2) (282/278), lien
//                 $(l:cible)…$(/l) (68 paires), couleur hex $(#RRGGBB) (0 occurrence
//                 mesurée mais présente dans la doc Patchouli, supportée par prudence) —
//                 et, fait absent du brief : les mêmes codes `§x` que les quêtes, pour les
//                 mêmes couleurs (§0 §2 §4 §5 §6 §b §r mesurés dans almanac/pale_oak.json
//                 et consorts, ex. "$(l)Stats$()$(li)🌐 §5Year-round§r"). `:coin:` est une
//                 icône Patchouli propre à ce pack (752 occurrences) ; `:slightly_smiling_face:`
//                 et consorts, croisés dans le même corpus, ne sont PAS des codes reconnus
//                 par Patchouli — ils s'affichent tels quels en jeu, donc ici aussi (repli
//                 par défaut : tout ce qui n'est reconnu par aucune règle ci-dessous reste
//                 du texte littéral, échappé comme le reste).
//
// Sécurité : le texte du corpus devient ici du HTML inséré via {@html} — c'est le seul
// endroit du projet où c'est le cas. AUCUN fragment du texte source ne doit pouvoir
// produire de balise active : voir echapper() et les tests « hostiles » de
// mc-render.test.js (script, attribut, faux code…).

const COULEURS = {
  0: "#000000", 1: "#0000AA", 2: "#00AA00", 3: "#00AAAA", 4: "#AA0000", 5: "#AA00AA",
  6: "#FFAA00", 7: "#AAAAAA", 8: "#555555", 9: "#5555FF", a: "#55FF55", b: "#55FFFF",
  c: "#FF5555", d: "#FF55FF", e: "#FFFF55", f: "#FFFFFF",
};

const echapper = (s) => (s ?? "").replace(/[&<>"]/g,
  c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

// Un seul passage sur le texte SOURCE, jamais sur du HTML déjà produit : echapper()
// transforme "&" en "&amp;" et une seconde passe de substitution relirait ce "&amp;" en y
// trouvant un faux code (le "&a" de "&amp;" lu comme le vert — c'est exactement le bug
// mesuré par le donneur d'ordre sur "&6Maîtrise&r"). On découpe donc le texte en jetons
// (code reconnu | reste littéral) en une seule traversée, et on n'échappe que les
// segments littéraux — jamais ce que ce module vient lui-même de générer.
const JETON_QUEST = /\\&|&[0-9a-fk-or]|§[0-9a-fk-or]/g;
const JETON_PATCHOULI = /\$\([^)]*\)|§[0-9a-fk-or]|:coin:/g;

// Referme tout ce qui reste ouvert sur la pile, dans l'ordre inverse de l'ouverture
// (LIFO — un <b> ouvert avant un <span> se ferme après lui). Utilisée à la fois par les
// codes de réinitialisation (&r, §r, $()) et en fin de rendu : sans ce second appel, la
// couleur ou le gras du dernier code ouvert d'un champ déborderait visuellement sur le
// paragraphe suivant dans l'aperçu — correction explicitement demandée, le brief livrait
// $(#RRGGBB) et $(l:...) sans fermeture.
function fermer(pile) {
  let s = "";
  while (pile.length) s += pile.pop();
  return s;
}

// Code couleur/mise en forme partagé par &x et §x, dans les deux dialectes : Patchouli
// utilise §x pour ses couleurs au même titre que les quêtes (voir l'en-tête du fichier).
//
// Comportement Minecraft documenté (et mesuré dans le corpus réel, ftbquests.chapter.
// vault.quest4B9634D942E590AB.description3 : "&oThe &6Skull Cavern Teleporter&r&o…") :
// un code de COULEUR réinitialise systématiquement tout le style en cours avant de
// s'appliquer — "Skull Cavern Teleporter" n'est PAS en italique en jeu, seulement doré,
// bien que &o soit resté ouvert juste avant &6 sans &r explicite entre les deux. Un
// simple push aurait empilé la couleur À L'INTÉRIEUR de l'italique au lieu de le
// remplacer. Les codes de STYLE (l/o/n/m/k), eux, s'additionnent sans rien fermer.
function codeCouleur(c, pile) {
  if (c === "r") return fermer(pile);
  if (COULEURS[c]) {
    const fermeture = fermer(pile);
    pile.push("</span>");
    return `${fermeture}<span style="color:${COULEURS[c]}">`;
  }
  if (c === "l") { pile.push("</b>"); return "<b>"; }
  if (c === "o") { pile.push("</i>"); return "<i>"; }
  if (c === "n") { pile.push("</u>"); return "<u>"; }
  if (c === "m") { pile.push("</s>"); return "<s>"; }
  // &k (brouillé) : effet dynamique en jeu (glyphes qui changent à chaque tick), pas
  // reproductible dans un aperçu statique sans animation — on donne un indice visuel
  // approximatif plutôt que de l'ignorer complètement ou de laisser fuiter "&k".
  if (c === "k") { pile.push("</span>"); return '<span class="brouille">'; }
  return "";
}

// interieur = le contenu entre "$(" et ")". Seuls les codes réellement rencontrés dans
// almanac/ et fish_finder/ (toutes langues) sont couverts en plus de $(#RRGGBB), présent
// dans la doc Patchouli mais absent de ce pack — gardé par prudence, coût nul.
function codePatchouli(interieur, pile) {
  if (interieur === "") return fermer(pile); // $() réinitialise TOUT, pas seulement le gras
  if (interieur === "l") { pile.push("</b>"); return "<b>"; }
  if (interieur === "li") return '<span class="puce"></span>';
  if (interieur === "br") return "<br>";
  if (interieur === "br2") return "<br><br>";
  if (interieur === "/l") return pile.length ? pile.pop() : "";
  if (interieur.startsWith("l:")) { pile.push("</span>"); return '<span class="lien">'; }
  const hex = interieur.match(/^#([0-9a-fA-F]{6})$/);
  if (hex) { pile.push("</span>"); return `<span style="color:#${hex[1]}">`; }
  // Code $(...) non reconnu : aucun autre trouvé dans le corpus mesuré. On dégrade sans
  // rien afficher — jamais laisser fuiter "$(xxx)" à l'écran — et on journalise en dev
  // pour repérer si un futur ajout au pack en introduit un nouveau.
  if (import.meta.env?.DEV) console.warn(`mc-render: code patchouli inconnu $(${interieur})`);
  return "";
}

function traiterCode(jeton, pile) {
  if (jeton === "\\&") return "&amp;"; // "&" littéral échappé par la convention du pack
  if (jeton === ":coin:") return '<span class="piece"></span>';
  if (jeton.charCodeAt(0) === 38 /* & */ || jeton.charCodeAt(0) === 167 /* § */) {
    return codeCouleur(jeton[1], pile);
  }
  return codePatchouli(jeton.slice(2, -1), pile); // le reste : un jeton $(...)
}

// dialecte ∈ "quest" | "patchouli" — voir l'en-tête du fichier. Les deux jeux de règles
// ne se mélangent pas : un "$(" dans un texte de quête, ou un "&6" dans un texte
// Patchouli, ne matche aucun jeton de SON dialecte et reste donc du texte littéral,
// échappé comme n'importe quel autre caractère.
export function rendre(texte, dialecte = "quest") {
  const source = texte ?? "";
  const jeton = dialecte === "patchouli" ? JETON_PATCHOULI : JETON_QUEST;
  const pile = [];
  let sortie = "";
  let dernier = 0;
  jeton.lastIndex = 0;
  let m;
  while ((m = jeton.exec(source))) {
    if (m.index > dernier) sortie += echapper(source.slice(dernier, m.index));
    sortie += traiterCode(m[0], pile);
    dernier = jeton.lastIndex;
  }
  sortie += echapper(source.slice(dernier));
  sortie += fermer(pile);
  return sortie;
}

// Les codes présents dans un texte, triés — pour comparer deux langues d'un même champ
// sans se soucier de leur ordre d'apparition. Sert à Peek.svelte : un &o italique côté
// anglais rendu par un &3 cyan côté français est une erreur invisible à la lecture brute
// (les deux validations existantes vérifient la PRÉSENCE de codes, pas leur identité) —
// mesuré sur ce pack, l'anglais et le français gardent en fait des jeux de codes
// identiques partout (voir task-13-report.md) ; codesDe reste la garde qui le vérifierait
// si un futur écart apparaissait.
export function codesDe(texte) {
  return ((texte ?? "").match(/[&§][0-9a-fk-or]|\$\([^)]*\)/g) ?? []).sort();
}
