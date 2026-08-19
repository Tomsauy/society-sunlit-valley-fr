import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { test, expect, vi } from "vitest";
import { ROOT, PACK, WORKSPACE, EXTRACTED, QUESTS_CONFIG } from "./paths.js";

test("les racines de données existent", () => {
  for (const p of [ROOT, PACK, WORKSPACE, EXTRACTED, QUESTS_CONFIG]) {
    expect(existsSync(p), `${p} introuvable`).toBe(true);
  }
});

test("PACK pointe sur le repo du modpack", () => {
  expect(existsSync(`${PACK}/kubejs/assets`)).toBe(true);
  expect(existsSync(`${PACK}/patchouli_books`)).toBe(true);
});

// Sans variable d'environnement, les quatre chemins réels gardent exactement leur valeur
// par défaut (disposition de l'auteur) — c'est ce que le test ci-dessus vérifie déjà en
// creux. Ici, on vérifie l'autre moitié du contrat : chacun peut être fixé de l'extérieur,
// et une valeur relative se résout par rapport à ROOT (la racine du dépôt), jamais par
// rapport au dossier courant du processus — sans quoi `npm run dev` lancé d'un autre
// dossier que `site/` changerait silencieusement où l'atelier va lire ses données.
// vi.resetModules() + import() dynamique : paths.js lit process.env à l'IMPORT (valeurs
// figées dans des `const` au chargement du module), donc seule une réévaluation complète
// du module voit une variable posée après le premier import statique ci-dessus.
test("un chemin relatif fourni par variable d'environnement se résout par rapport à ROOT, pas au dossier courant", async () => {
  const avant = { ...process.env };
  process.env.ATELIER_PACK = "un-pack-ailleurs";
  process.env.ATELIER_WORKSPACE = "/tmp/un-espace-de-travail-absolu";
  try {
    vi.resetModules();
    const m = await import("./paths.js");
    expect(m.PACK).toBe(resolve(m.ROOT, "un-pack-ailleurs"));
    // Une valeur déjà absolue traverse resolve() telle quelle (resolve() ignore ROOT dès
    // qu'un argument suivant est absolu) : même mécanisme, pas un cas à part.
    expect(m.WORKSPACE).toBe("/tmp/un-espace-de-travail-absolu");
    // EXTRACTED/QUESTS_CONFIG suivent leur dérivation habituelle depuis WORKSPACE/PACK
    // quand ils ne sont pas eux-mêmes fixés — la dérivation par défaut survit au réglage
    // des deux autres.
    expect(m.EXTRACTED).toBe(resolve(m.WORKSPACE, "extracted"));
    expect(m.QUESTS_CONFIG).toBe(resolve(m.PACK, "config/ftbquests/quests"));
  } finally {
    process.env = avant;
    vi.resetModules();
  }
});
