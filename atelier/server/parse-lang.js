// Minecraft tolère les commentaires // dans les fichiers lang ; JSON.parse non.
// Un analyseur strict masque des mods entiers en silence : vintagedelight (190 clés)
// est resté invisible pendant tout le projet de traduction à cause de ça.
const COMMENT = /(^|[^:"])\/\/[^"\n]*$/gm;

export function parseLang(texte) {
  const net = texte.replace(/^﻿/, "");
  try {
    return { data: JSON.parse(net), tolerated: false };
  } catch {}
  try {
    return { data: JSON.parse(net.replace(COMMENT, "$1")), tolerated: true };
  } catch {
    return { data: null, tolerated: false };
  }
}
