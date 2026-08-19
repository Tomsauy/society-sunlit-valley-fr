<!-- site/src/views/BooksView.svelte -->
<script>
  import { livres as fetchLivres } from "../lib/api.js";
  // site/src/lib/format.js n'existe pas : localeLabel, exporté par server/locales.js,
  // est ce que QuestsView utilise déjà pour la même chose (bilingue + bascule
  // « toutes les langues »).
  import { localeLabel } from "../../server/locales.js";
  import Peek from "../lib/Peek.svelte";

  let livres = $state([]);
  let erreur = $state("");
  let ouverts = $state(new Set());
  // { type: "categorie", livreId, categorie } | { type: "entree", livreId, categorie, entree } | null
  // — un clic sur une catégorie choisit son en-tête (nom, description bilingue) dans le
  // panneau de lecture, sans empêcher par ailleurs de la déplier/replier dans l'arbre
  // (même principe que choisirChapitre dans QuestsView).
  let selection = $state(null);
  let toutesLangues = $state(false);

  // Aperçu du rendu en jeu (tâche 13, correctif) — voir la même logique et sa
  // justification dans QuestsView.svelte. `champ.pointeur` (ex. "pages/0/text") n'est
  // unique QU'AU SEIN d'une entrée — très souvent répété d'une entrée à l'autre (page
  // unique à un seul champ "text", le cas le plus courant du pack) — donc la clé
  // d'ouverture doit inclure l'entrée (`e.chemin`, déjà utilisé comme identifiant unique
  // d'entrée ailleurs dans ce fichier) pour ne pas laisser un aperçu paraître déjà
  // ouvert en arrivant sur une nouvelle entrée qui réutilise le même pointeur.
  let survoles = $state(new Set());
  let focuses = $state(new Set());
  const marquer = (ensemble, cle, present) => {
    const s = new Set(ensemble);
    present ? s.add(cle) : s.delete(cle);
    return s;
  };
  const apercuOuvert = (cle) => survoles.has(cle) || focuses.has(cle);

  // Fermeture différée au survol (voir la justification détaillée dans QuestsView.svelte) :
  // sans ce délai, refermer l'aperçu du premier champ remonte le second exactement au
  // moment où la souris franchit leur frontière — une descente continue peut atterrir
  // dans l'espace qui vient de se libérer entre les deux (mesuré au pilotage, sur ce
  // fichier même : almanac/entries/animals/warped_wooly_cow.json).
  const DELAI_FERMETURE_MS = 160;
  let minuteries = new Map();
  const survolerDedans = (cle) => {
    const t = minuteries.get(cle);
    if (t !== undefined) { clearTimeout(t); minuteries.delete(cle); }
    survoles = marquer(survoles, cle, true);
  };
  const survolerDehors = (cle) => {
    const t = setTimeout(() => {
      survoles = marquer(survoles, cle, false);
      minuteries.delete(cle);
    }, DELAI_FERMETURE_MS);
    minuteries.set(cle, t);
  };
  // Identifiant DOM stable dérivé de la clé du champ — relie le bouton au panneau qu'il
  // déclenche via aria-controls (voir plus bas), même principe que QuestsView.svelte.
  const idApercu = (cle) => `peek-${cle.replace(/[^a-zA-Z0-9_-]/g, "-")}`;

  $effect(() => {
    fetchLivres()
      .then((l) => { livres = l; erreur = ""; })
      .catch((err) => { erreur = `Chargement impossible : ${err.message}`; });
  });

  // Les identifiants de catégorie ne sont uniques qu'au sein d'un livre (rien
  // n'empêcherait deux livres de choisir le même) : la clé d'ouverture/sélection est
  // donc composée avec l'id du livre.
  const cle = (livreId, catId) => `${livreId}:${catId}`;

  const basculer = (livreId, cat) => {
    const k = cle(livreId, cat.id);
    const s = new Set(ouverts);
    s.has(k) ? s.delete(k) : s.add(k);
    ouverts = s;
  };

  const choisirCategorie = (livreId, cat) => {
    basculer(livreId, cat);
    selection = { type: "categorie", livreId, categorie: cat };
  };
  const choisirEntree = (livreId, cat, entree) => {
    selection = { type: "entree", livreId, categorie: cat, entree };
  };

  const nomEntree = (e) => e.nom.fr_fr ?? e.nom.en_us ?? e.chemin;
  const nomLivre = (l) => l.titre.fr_fr ?? l.titre.en_us ?? l.id;

  // "name " (patchouli:multiblock, 110 pages) porte une espace finale sur le disque en
  // anglais, français et chinois — c'est le nom du champ tel qu'il existe réellement.
  // Patchouli le lit SANS cette espace au moment du rendu : ces noms ne s'affichent
  // donc jamais en jeu, un défaut du pack et non de ce lecteur. On ne le masque pas :
  // un champ dont le pointeur se termine par une espace porte la note ci-dessous.
  const anomalieEspace = (champ) => champ.pointeur?.endsWith(" ") ?? false;
</script>

<div class="cols">
  <aside class="tree">
    {#if erreur}<p class="erreur" role="alert">{erreur}</p>{/if}
    {#each livres as l}
      <div class="livre">
        <span>{nomLivre(l)}</span>
        <em>{l.categories.reduce((n, c) => n + c.entrees.length, 0)}</em>
      </div>
      {#each l.categories as c}
        <button
          class="cat"
          class:open={ouverts.has(cle(l.id, c.id))}
          class:sel={selection?.type === "categorie" && selection.livreId === l.id && selection.categorie.id === c.id}
          aria-expanded={ouverts.has(cle(l.id, c.id))}
          onclick={() => choisirCategorie(l.id, c)}
        >
          <span class="car" aria-hidden="true">{ouverts.has(cle(l.id, c.id)) ? "▾" : "▸"}</span>
          <span class="lib">{c.nom}</span>
          <em>{c.entrees.length}</em>
        </button>
        {#if ouverts.has(cle(l.id, c.id))}
          {#each c.entrees as e}
            <button
              class="ent"
              class:on={selection?.type === "entree" && selection.entree.chemin === e.chemin}
              onclick={() => choisirEntree(l.id, c, e)}
            >
              {nomEntree(e)}
            </button>
          {/each}
        {/if}
      {/each}
    {/each}
  </aside>

  <main class="read">
    {#if !selection}
      <p class="vide">Choisis une catégorie ou une entrée.</p>
    {:else if selection.type === "categorie"}
      {@const c = selection.categorie}
      <div class="entete-cat">
        <h1>{c.nom}</h1>
        {#if c.description}<p class="sous">{c.description}</p>{/if}
        <p class="compte">
          <b>{c.entrees.length.toLocaleString("fr-FR")}</b> entrée{c.entrees.length > 1 ? "s" : ""}.
        </p>
        {#if Object.keys(c.descriptions).length}
          <div class="multi-desc">
            {#each Object.entries(c.descriptions) as [loc, txt]}
              <div class="txt multi"><span class="loc">{localeLabel(loc)}</span>{txt}</div>
            {/each}
          </div>
        {/if}
      </div>
    {:else}
      {@const e = selection.entree}
      <div class="titre">
        <div><div class="lab">Anglais</div><h1>{e.nom.en_us ?? "—"}</h1></div>
        <div><div class="lab">Français</div><h1>{e.nom.fr_fr ?? "—"}</h1></div>
      </div>
      <button class="tool" class:open={toutesLangues} onclick={() => (toutesLangues = !toutesLangues)}>
        {toutesLangues ? "Anglais / Français seulement" : "Toutes les langues"}
      </button>
      {#each e.pages as p}
        <div class="page">
          <div class="phead">
            <span class="pnum">page {p.index + 1}</span>
            <span class="ptype" class:non={!p.traduisible}>
              {p.traduisible ? p.type.replace("patchouli:", "") : `${p.type.replace("patchouli:", "")} · rien à traduire`}
            </span>
          </div>
          {#if p.traduisible}
            {#each p.champs as champ}
              {@const cleP = `${e.chemin}::${champ.pointeur}`}
              <!-- svelte-ignore a11y_no_static_element_interactions -- même raison que
                   QuestsView.svelte : .peekhook porte l'affordance et le chemin clavier,
                   ce survol n'est qu'un confort souris supplémentaire. -->
              <div
                class="champ"
                onmouseenter={() => survolerDedans(cleP)}
                onmouseleave={() => survolerDehors(cleP)}
              >
                {#if p.champs.length > 1}<div class="fld">{champ.nom}</div>{/if}
                <!-- Aperçu du rendu en jeu (tâche 13) : même mécanisme que QuestsView —
                     survol OU focus clavier sur ce bouton, jamais l'inverse. -->
                <button
                  type="button"
                  class="peekhook"
                  aria-label="Aperçu du rendu en jeu"
                  aria-expanded={apercuOuvert(cleP)}
                  aria-controls={idApercu(cleP)}
                  onfocus={() => (focuses = marquer(focuses, cleP, true))}
                  onblur={() => (focuses = marquer(focuses, cleP, false))}
                >👁</button>
                {#if anomalieEspace(champ)}
                  <p class="anomalie">
                    Champ « {champ.nom} » avec une espace finale sur le disque — Patchouli le lit
                    sans elle : ce nom ne s'affiche jamais en jeu (défaut du pack, pas de cet outil).
                  </p>
                {/if}
                {#if toutesLangues}
                  {#each Object.entries(champ.valeurs) as [loc, txt]}
                    <div class="txt multi"><span class="loc">{localeLabel(loc)}</span>{txt}</div>
                  {:else}
                    <div class="txt vide">Aucune langue ne traduit ce champ.</div>
                  {/each}
                {:else}
                  <div class="cols2">
                    <div class="txt en">{champ.valeurs.en_us ?? "—"}</div>
                    <div class="txt">{champ.valeurs.fr_fr ?? "—"}</div>
                  </div>
                {/if}
                {#if apercuOuvert(cleP)}
                  <Peek id={idApercu(cleP)} en={champ.valeurs.en_us} fr={champ.valeurs.fr_fr} dialecte="patchouli" />
                {/if}
              </div>
            {/each}
          {:else}
            <div class="boite">{p.resume}</div>
          {/if}
        </div>
      {/each}
    {/if}
  </main>
</div>

<style>
  .cols { display:grid; grid-template-columns:268px 1fr; height:100%; overflow:hidden; }
  .tree { background:var(--paper-2); border-right:1px solid var(--rule); overflow-y:auto; }
  .erreur { margin:0; padding:8px 12px; background:var(--rose-soft); color:var(--rose);
            font-size:12px; border-bottom:1px solid var(--rule); }
  .livre { padding:11px 12px 5px; font-family:var(--mono); font-size:9.5px; letter-spacing:.15em;
           text-transform:uppercase; color:var(--faint); display:flex; }
  .livre em { margin-left:auto; font-style:normal; }
  .cat, .ent { display:flex; width:100%; border:0; background:transparent; font:inherit;
               cursor:pointer; text-align:left; align-items:center; }
  .cat { gap:8px; padding:6px 12px 6px 16px; font-size:12.5px; color:var(--muted); }
  .cat:hover, .ent:hover { background:#fff; }
  .cat.open { background:#fff; color:var(--ink); font-weight:500; }
  .cat.sel { border-left:2px solid var(--verdigris); }
  .cat .car { font-size:8px; color:var(--faint); width:8px; flex:none; }
  .cat .lib, .ent { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .cat em { margin-left:auto; padding-left:8px; font-style:normal; font-family:var(--mono);
            font-size:9.5px; color:var(--faint); flex:none; font-variant-numeric:tabular-nums; }
  .ent { padding:5px 12px 5px 38px; font-size:12px; color:var(--muted); border-left:2px solid transparent; }
  .ent.on { background:#fff; color:var(--ink); border-left-color:var(--verdigris); font-weight:500; }
  .cat:focus-visible, .ent:focus-visible, .tool:focus-visible {
    outline:2px solid var(--verdigris); outline-offset:-2px;
  }
  .read { overflow-y:auto; padding:20px 22px 44px; }
  .vide { color:var(--faint); }
  .entete-cat h1 { margin:0 0 4px; font-size:22px; }
  .entete-cat .sous { margin:0 0 10px; color:var(--muted); font-size:14px; font-style:italic; }
  .entete-cat .compte { font-size:13.5px; color:var(--muted); }
  .entete-cat .compte b { font-family:var(--mono); color:var(--ink); }
  .multi-desc { margin-top:10px; padding:10px 12px; background:var(--paper-2);
                border:1px solid var(--rule); border-radius:6px; }
  .titre { display:grid; grid-template-columns:1fr 1fr; gap:22px; padding-bottom:14px;
           border-bottom:2px solid var(--ink); margin-bottom:10px; }
  .titre h1 { margin:0; font-size:22px; line-height:1.2; }
  .titre div:first-child h1 { color:var(--muted); font-weight:400; }
  .lab { font-family:var(--mono); font-size:9px; letter-spacing:.15em; text-transform:uppercase;
         color:var(--faint); margin-bottom:5px; }
  .tool { font-family:var(--mono); font-size:10.5px; padding:5px 10px; border-radius:5px;
          cursor:pointer; border:1px dashed var(--rule); background:#fff; color:var(--muted);
          margin-bottom:8px; }
  .tool.open { border-style:solid; border-color:var(--ink); color:var(--ink); background:var(--paper-2); }
  .page { border-bottom:1px solid var(--rule); padding:13px 0; }
  .phead { display:flex; gap:9px; align-items:center; margin-bottom:8px; }
  .pnum { font-family:var(--mono); font-size:9px; letter-spacing:.1em; color:var(--faint);
          border:1px solid var(--rule); border-radius:3px; padding:1px 6px; }
  .ptype { font-family:var(--mono); font-size:9px; letter-spacing:.12em; text-transform:uppercase;
           color:var(--faint); }
  .ptype.non { background:var(--paper-2); border:1px solid var(--rule); border-radius:3px;
               padding:1px 6px; color:var(--muted); }
  .champ { position:relative; }
  .champ + .champ { margin-top:10px; padding-top:10px; border-top:1px dotted var(--rule); }
  .fld { font-family:var(--mono); font-size:9px; letter-spacing:.12em; text-transform:uppercase;
         color:var(--faint); margin-bottom:5px; }
  /* Aperçu du rendu en jeu (tâche 13) — même mécanisme que QuestsView.svelte : bouton
     toujours présent dans le DOM (accessible au clavier et aux lecteurs d'écran),
     déclenché au survol OU dès que ce bouton reçoit le focus (logique en JS, voir
     apercuOuvert ci-dessus). */
  .champ .peekhook {
    position:absolute; top:0; right:0; width:20px; height:20px; padding:0; z-index:1;
    display:flex; align-items:center; justify-content:center; line-height:1;
    border:1px solid var(--rule); border-radius:5px; background:#fff; color:var(--faint);
    font-size:11px; cursor:pointer;
  }
  .champ .peekhook:hover { color:var(--ink); border-color:var(--verdigris); }
  .champ .peekhook:focus-visible { outline:2px solid var(--verdigris); outline-offset:1px; }
  /* Correctif : Peek n'est plus en position absolue (voir Peek.svelte) et n'est monté
     que lorsqu'ouvert (apercuOuvert) — il réserve sa propre place et pousse le contenu
     qui suit, au lieu de recouvrir le champ suivant et de lui voler ses événements de
     pointeur (mesuré sur une page à deux champs, ex. animals/warped_wooly_cow.json). */
  .champ :global(.peek) { margin-top:8px; }
  .anomalie { margin:0 0 8px; padding:7px 10px; background:var(--amber-soft); border:1px solid var(--amber);
              color:var(--amber); border-radius:5px; font-size:11.5px; line-height:1.5; }
  .cols2 { display:grid; grid-template-columns:1fr 1fr; gap:22px; }
  .txt { line-height:1.7; font-size:13.5px; }
  .txt.en { color:var(--muted); }
  .txt.vide { color:var(--faint); font-style:italic; font-size:12.5px; }
  .txt.multi { display:flex; gap:10px; padding:3px 0; }
  .txt.multi .loc { flex:none; width:150px; font-family:var(--mono); font-size:10px;
                     color:var(--faint); padding-top:3px; }
  .boite { background:var(--paper-2); border:1px dashed var(--rule); border-radius:6px;
           padding:11px 13px; font-size:12.5px; color:var(--muted); font-family:var(--mono); }
</style>
