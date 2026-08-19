// site/src/lib/mc-render.test.js
import { test, expect } from "vitest";
import { rendre, codesDe } from "./mc-render.js";

// --- Tests du brief (task-13-brief.md, Step 1) --------------------------------------

test("les codes de couleur des quêtes deviennent des couleurs", () => {
  const h = rendre("Débloquer la &6Maîtrise&r te donne accès", "quest");
  expect(h).toContain("#FFAA00");
  expect(h).not.toContain("&6");
});

test("l'italique des quêtes", () => {
  expect(rendre("&oJette un œil", "quest")).toContain("<i>");
});

test("les codes patchouli : gras, puce, icône", () => {
  const h = rendre("$(l)Stats$()$(li):coin: 42", "patchouli");
  expect(h).toContain("<b>");
  expect(h).toContain("puce");
  expect(h).toContain("piece");
  expect(h).not.toContain("$(li)");
});

test("le HTML des données est neutralisé", () => {
  expect(rendre("<script>alert(1)</script>", "quest")).not.toContain("<script>");
});

test("codesDe permet de comparer deux langues", () => {
  expect(codesDe("&6Un&r deux")).toEqual(["&6", "&r"]);
  expect(codesDe("&6Un&r deux")).not.toEqual(codesDe("&3Un&r deux"));
});

// --- Correction A : echapper() puis substitution sur la même chaîne (bug du brief) --
//
// Sur "Débloquer la &6Maîtrise&r te donne accès", l'implémentation du brief produit
// "…<span style=\"color:#55FF55\">mp;6Maîtrise<span style=\"color:#55FF55\">mp;r te…" :
// echapper() transforme "&" en "&amp;" AVANT la substitution des codes, donc le "&a" de
// "&amp;" est relu comme le vert et "mp;" reste affiché tel quel. Ces tests figent le
// résultat correct, jeton par jeton, pas seulement "contient la couleur".

test("aucun résidu d'échappement (mp;) ni de code brut dans le rendu", () => {
  const h = rendre("Débloquer la &6Maîtrise&r te donne accès", "quest");
  expect(h).toBe('Débloquer la <span style="color:#FFAA00">Maîtrise</span> te donne accès');
});

test("tous les codes & réellement utilisés dans le pack (couleurs, gras, italique, reset)", () => {
  // &6 &r (dominants), &d &o &b &3 &c &a &l &5 &e &7 — recensés sur les douze langues de
  // ftbquestlocalizer/lang. Un seul texte les enchaîne pour vérifier qu'aucun ne laisse
  // fuiter "&x" ni de résidu d'échappement.
  const texte = "&d&o&b&3&c&a&l&5&e&7&rTexte&r";
  const h = rendre(texte, "quest");
  expect(h).not.toMatch(/&[0-9a-fk-or]/);
  expect(h).not.toContain("mp;");
});

// --- Correction B : les balises doivent se refermer ----------------------------------

test("$(#RRGGBB) ouvre un span qui se referme en fin de rendu", () => {
  const h = rendre("$(#FF0000)Rouge", "patchouli");
  expect(h).toBe('<span style="color:#FF0000">Rouge</span>');
});

test("$() réinitialise TOUT le formatage ouvert, pas seulement le gras", () => {
  const h = rendre("$(#00FF00)$(l)Vert gras$()reste", "patchouli");
  // les deux balises ouvertes (couleur puis gras) se referment ensemble sur $(),
  // dans l'ordre inverse de leur ouverture — sinon "reste" resterait dans le span vert.
  expect(h).toBe('<span style="color:#00FF00"><b>Vert gras</b></span>reste');
});

test("&r referme la couleur ET le gras ouverts avant lui (pas juste le dernier)", () => {
  const h = rendre("&6&lGras doré&rsuite", "quest");
  expect(h).toBe('<span style="color:#FFAA00"><b>Gras doré</b></span>suite');
});

test("aucune balise ouverte ne survit en fin de rendu (pas de fuite sur le paragraphe suivant)", () => {
  const h = rendre("&6Sans reset explicite", "quest");
  expect(h).toBe('<span style="color:#FFAA00">Sans reset explicite</span>');
  // deux rendus indépendants ne partagent aucun état (la pile est locale à l'appel) :
  const suite = rendre("Texte normal", "quest");
  expect(suite).toBe("Texte normal");
});

test("un lien Patchouli $(l:cible)…$(/l) s'ouvre et se referme sans fuite du code", () => {
  const h = rendre("$(l:tree_crops/cherry)8x Cerises$(/l) suite", "patchouli");
  expect(h).not.toContain("$(l:");
  expect(h).not.toContain("$(/l)");
  expect(h).toContain("8x Cerises");
  expect(h).toContain("suite");
  expect(h.match(/<span/g)?.length).toBe(1);
  expect(h.match(/<\/span>/g)?.length).toBe(1);
});

// --- Un code couleur réinitialise le style en cours (comportement Minecraft standard, --
// --- mesuré dans le corpus réel — voir le commentaire de codeCouleur dans mc-render.js) -

test("un code couleur annule l'italique resté ouvert, comme en jeu (cas réel : quête du Caveau)", () => {
  // Texte exact de ftbquests.chapter.vault.quest4B9634D942E590AB.description3 (en_us) :
  // &o ouvre l'italique, &6 (couleur) doit le refermer avant de colorer "Skull Cavern
  // Teleporter" — qui ne doit donc PAS apparaître en italique, seulement doré.
  const h = rendre(
    "&oThe &6Skull Cavern Teleporter&r&o can also be bought from the &6Guild&r&o if it is lost somehow.",
    "quest"
  );
  expect(h).toBe(
    '<i>The </i><span style="color:#FFAA00">Skull Cavern Teleporter</span>' +
    '<i> can also be bought from the </i><span style="color:#FFAA00">Guild</span>' +
    '<i> if it is lost somehow.</i>'
  );
});

test("des couleurs qui se succèdent sans reset ne s'emboîtent pas (chaque segment garde SA couleur)", () => {
  // Cas réel : patchouli_books/fish_finder, page Stats — une liste de saisons où chaque
  // §-couleur suit la précédente sans §r. Si les couleurs s'imbriquaient (un simple push
  // sans fermeture), la portée visuelle resterait correcte par cascade CSS, mais la
  // structure serait absurde ; ce test fige la structure PLATE attendue.
  const h = rendre("§0a §2b§0 §6c§0", "patchouli");
  expect(h).toBe(
    '<span style="color:#000000">a </span><span style="color:#00AA00">b</span>' +
    '<span style="color:#000000"> </span><span style="color:#FFAA00">c</span>' +
    '<span style="color:#000000"></span>'
  );
});

// --- L'échappement "\&" propre au pack (découvert en creusant le corpus réel) --------

test('"\\&" (échappement du pack) devient un "&" littéral, pas un code ni un artefact', () => {
  const h = rendre("Butterflies \\& Moths", "quest");
  expect(h).toBe("Butterflies &amp; Moths");
  expect(h).not.toContain("\\");
});

// --- $(br2), découvert dans le corpus (555 occurrences), absent du code du brief -----

test("$(br2) produit un saut de paragraphe, pas juste un fragment supprimé", () => {
  const h = rendre("Un$(br2)Deux", "patchouli");
  expect(h).toBe("Un<br><br>Deux");
});

// --- Isolation des dialectes : ils ne se mélangent jamais ---------------------------

test("un code $(...) dans un texte de quête reste du texte littéral", () => {
  const h = rendre("$(l)Bold$()", "quest");
  expect(h).toBe("$(l)Bold$()");
});

test("un code &x dans un texte Patchouli reste du texte littéral, échappé", () => {
  const h = rendre("&6Texte&r", "patchouli");
  expect(h).toBe("&amp;6Texte&amp;r");
});

// --- Dégradation propre des codes inconnus : jamais de fragment visible -------------

test("un code $(...) patchouli inconnu disparaît sans laisser de fragment", () => {
  const h = rendre("Avant $(inconnu_xyz) après", "patchouli");
  expect(h).not.toContain("$(");
  expect(h).not.toContain("inconnu_xyz");
  expect(h).toBe("Avant  après");
});

test("&k (brouillé) ne laisse pas fuiter le code, même sans équivalent animé fidèle", () => {
  const h = rendre("&kXXXX&r", "quest");
  expect(h).not.toContain("&k");
  expect(h).toContain("XXXX");
});

// --- Cas hostiles : le rendu produit du HTML injecté via {@html}, donc aucune donnée --
// --- ne doit jamais pouvoir produire de balise active --------------------------------

test("une valeur cherchant à casser un attribut de couleur ne s'échappe pas de son span", () => {
  // Le "onerror=alert(1)" reste présent en texte INERTE (normal : un champ de traduction
  // légitime peut contenir le mot "onerror") — ce qui compte est qu'aucun "<" ni ">" ni
  // '"' ne survive tel quel pour rouvrir une vraie balise ou un vrai attribut. D'où une
  // comparaison exacte plutôt qu'une simple absence de sous-chaîne, imprécise pour ce cas.
  const h = rendre('&6"><img src=x onerror=alert(1)>', "quest");
  expect(h).toBe(
    '<span style="color:#FFAA00">&quot;&gt;&lt;img src=x onerror=alert(1)&gt;</span>'
  );
});

test("un faux code dans le texte d'un lien Patchouli ne casse pas le balisage", () => {
  const h = rendre("$(l:x)</span><script>alert(1)</script>$(/l)", "patchouli");
  expect(h).toBe(
    '<span class="lien">&lt;/span&gt;&lt;script&gt;alert(1)&lt;/script&gt;</span>'
  );
});

test("une balise complète fournie en clair (Patchouli) reste neutralisée", () => {
  const h = rendre("<b onmouseover=alert(1)>x</b>", "patchouli");
  expect(h).toBe("&lt;b onmouseover=alert(1)&gt;x&lt;/b&gt;");
});

test("guillemets et chevrons dans un champ de quête normal restent neutralisés", () => {
  const h = rendre('Le bouton "mute" > désactive tout', "quest");
  expect(h).not.toContain('"mute"');
  expect(h).toContain("&quot;mute&quot;");
  expect(h).toContain("&gt;");
});

// --- codesDe : robustesse sur l'échappement et sur les entrées vides -----------------

test("codesDe ignore \\& (ce n'est pas un code de mise en forme)", () => {
  expect(codesDe("Butterflies \\& Moths")).toEqual([]);
});

test("rendre et codesDe tolèrent une entrée vide ou absente", () => {
  expect(rendre("", "quest")).toBe("");
  expect(rendre(undefined, "patchouli")).toBe("");
  expect(codesDe("")).toEqual([]);
  expect(codesDe(undefined)).toEqual([]);
});
