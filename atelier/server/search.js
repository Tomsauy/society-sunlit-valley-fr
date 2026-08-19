const bas = s => (s ?? "").toLowerCase();

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
  const t = bas(q);
  if (champ === "cle") return bas(e.cle).includes(t);
  if (champ === "toutes")
    return bas(e.cle).includes(t) || bas(e.source.en).includes(t) ||
           Object.values(e.traductions).some(v => bas(v).includes(t));
  // "texte" par défaut : anglais source et français
  return bas(e.source.en).includes(t) || bas(e.traductions.fr_fr).includes(t);
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
