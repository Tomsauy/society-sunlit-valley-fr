// Les ligatures que String.normalize ne décompose pas : il faut les traiter à part.
// La table doit rester identique à celle d'Accents.java dans le mod, sinon l'Atelier
// prétend trouver ce que le jeu ne trouve pas.
const LIGATURES = [["œ", "oe"], ["Œ", "OE"], ["æ", "ae"], ["Æ", "AE"],
                   ["ø", "o"], ["Ø", "O"], ["ß", "ss"], ["ẞ", "ss"],
                   ["đ", "d"], ["Đ", "D"], ["ð", "d"], ["Ð", "D"],
                   ["ł", "l"], ["Ł", "L"]];

// La forme de comparaison d'un texte : minuscules, sans accents. Chercher « ble »
// doit trouver « Blé », comme en jeu — c'est exactement ce que fait le mod Accent
// Fold, et l'Atelier était le dernier endroit à ne pas le faire.
//
// La même logique existe en Java dans le mod (https://github.com/Tomsauy/accent-fold,
// Accents.java) et en Python dans fr-workspace/scripts/compare_accents.py. Trois
// langages, trois copies, et depuis que le mod a son propre dépôt, deux dépôts :
// qui touche à l'une doit regarder les autres.
const normalise = s => {
  let t = s ?? "";
  if (!t) return t;
  // Le cas majoritaire — une requête ou une valeur tout en ASCII — n'a rien à
  // faire dans le décomposeur, qui tourne à chaque frappe sur tout l'index.
  if (!/[^\x00-\x7F]/.test(t)) return t.toLowerCase();
  // Recomposer en NFC après avoir ôté les marques : sans cela le coréen ressortirait
  // en jamos séparés, et « 홉 씨앗 » ne trouverait plus rien.
  const recompose = t.normalize("NFD").replace(/\p{M}+/gu, "").normalize("NFC");
  // Les ligatures se remplacent APRÈS la recomposition, jamais avant : « Ǽ » et « Ǿ »
  // ne sont pas dans la table, se décomposent en « Æ » et « Ø » plus une marque, et
  // n'arrivent sous leur forme connue qu'ici. L'ordre compte autant que la table.
  let replace = recompose;
  for (const [avant, apres] of LIGATURES) replace = replace.replaceAll(avant, apres);
  return replace.toLowerCase();
};

// Une limite ou un offset non numérique (ex. "abc") ou négatif retombe silencieusement
// sur la valeur par défaut plutôt que de produire un slice(NaN, NaN) (page vide malgré
// un total correct — indistinguable d'une vraie absence de résultat côté client) ou un
// slice(0, -5) (limite négative interprétée par slice comme « jusqu'à la fin moins 5 »,
// ce qui renvoie presque tout l'index).
function versEntierPositif(valeur, defaut) {
  const n = Number(valeur);
  return Number.isInteger(n) && n >= 0 ? n : defaut;
}

function correspond(e, q, champ) {
  if (!q) return true;
  const t = normalise(q);
  if (champ === "cle") return normalise(e.cle).includes(t);
  if (champ === "toutes")
    return normalise(e.cle).includes(t) || normalise(e.source.en).includes(t) ||
           Object.values(e.traductions).some(v => normalise(v).includes(t));
  // "texte" par défaut : anglais source et français
  return normalise(e.source.en).includes(t) || normalise(e.traductions.fr_fr).includes(t);
}

// La portée décide ce que « présent » signifie : au sens strict, seulement ce que le
// pack porte lui-même ; au sens large, ce qui est visible en jeu, jar du mod compris.
function aLangue(e, loc, portee) {
  if (portee === "pack") return e.presentDans.pack.includes(loc);
  return e.presentDans.pack.includes(loc) || e.presentDans.mods.includes(loc);
}

export function search(idx, { q = "", champ = "texte", ns = null, origine = null,
                              avec = [], sans = [], portee = "pack_et_mods",
                              limite = 100, offset = 0 } = {}) {
  limite = versEntierPositif(limite, 100);
  offset = versEntierPositif(offset, 0);
  const filtres = idx.entrees.filter(e =>
    (!ns || e.ns === ns) &&
    (!origine || e.source.origine === origine) &&
    (avec.length === 0 || avec.some(l => aLangue(e, l, portee))) &&
    (sans.length === 0 || sans.every(l => !aLangue(e, l, portee))) &&
    correspond(e, q, champ));
  return { total: filtres.length, resultats: filtres.slice(offset, offset + limite) };
}
