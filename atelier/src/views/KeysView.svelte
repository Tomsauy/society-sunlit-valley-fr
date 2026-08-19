<!-- site/src/views/KeysView.svelte -->
<script>
  import { recherche, locales as chargerLocales } from "../lib/api.js";
  import LangFilter from "./LangFilter.svelte";

  let { onSelect } = $props();
  let q = $state("");
  let champ = $state("texte");
  let colonnes = $state(["fr_fr"]);
  let toutesLocales = $state([]);
  let choixOuvert = $state(false);
  let filtreOuvert = $state(false);
  let avec = $state([]);
  let sans = $state([]);
  let portee = $state("pack_et_mods");
  let res = $state({ total: 0, resultats: [] });
  let selectionne = $state(null);
  let erreur = $state(null);

  // Pagination : le serveur gère `offset` correctement (search.js), mais rien ne
  // l'envoyait jamais ici — la vue affichait toujours "59 941 clés" tout en ne
  // montrant jamais que les 200 premières du premier namespace alphabétique, sans le
  // dire. TAILLE_PAGE reprend la limite déjà en place (200) ; `page` est 1-indexée
  // pour l'affichage.
  const TAILLE_PAGE = 200;
  let page = $state(1);
  let totalPages = $derived(Math.max(1, Math.ceil(res.total / TAILLE_PAGE)));
  let debut = $derived(res.total === 0 ? 0 : (page - 1) * TAILLE_PAGE + 1);
  let fin = $derived(Math.min(page * TAILLE_PAGE, res.total));

  $effect(() => {
    chargerLocales().then(l => (toutesLocales = l))
      .catch(err => console.error("Chargement des langues impossible :", err));
  });

  // Remise à la première page quand la recherche ou les filtres changent — effet
  // séparé, dédié uniquement à ces cinq critères (jamais à `page` elle-même, pour ne
  // pas boucler) : sans ça, changer de recherche pendant qu'on est en page 4 peut
  // atterrir sur une page vide (la nouvelle recherche n'a peut-être que 2 pages) sans
  // qu'on comprenne pourquoi.
  $effect(() => {
    q; champ; avec; sans; portee;
    page = 1;
  });

  // Un délai avant l'envoi évite une requête par caractère tapé pendant la frappe.
  // Le numéro de requête permet d'ignorer toute réponse qui n'est plus la dernière
  // émise : rien ne garantit que les réponses reviennent dans l'ordre d'envoi.
  let derniereRequete = 0;
  $effect(() => {
    const offset = (page - 1) * TAILLE_PAGE;
    const params = { q, champ, limite: TAILLE_PAGE, offset,
                     avec: avec.join(","), sans: sans.join(","), portee };
    const id = ++derniereRequete;
    const minuteur = setTimeout(() => {
      recherche(params)
        .then(r => { if (id === derniereRequete) { res = r; erreur = null; } })
        .catch(err => { if (id === derniereRequete) erreur = err.message; });
    }, 250);
    return () => clearTimeout(minuteur);
  });

  // Filet de sécurité : si le total baisse (correction qui fait sortir des clés du
  // filtre courant, par exemple) pendant qu'on est déjà loin dans la pagination, la
  // page courante peut se retrouver au-delà du total. On se replie sur la dernière
  // page valide plutôt que de rester bloqué sur une page vide.
  $effect(() => {
    if (page > totalPages) page = totalPages;
  });

  const pagePrecedente = () => { if (page > 1) page -= 1; };
  const pageSuivante = () => { if (page < totalPages) page += 1; };
  const allerA = (n) => {
    const p = Math.trunc(Number(n));
    if (Number.isInteger(p) && p >= 1 && p <= totalPages) page = p;
  };

  const bascule = (code) =>
    (colonnes = colonnes.includes(code) ? colonnes.filter(c => c !== code) : [...colonnes, code]);

  const choisir = (e) => { selectionne = e.id; onSelect?.(e.id); };

  // Rend les lignes actionnables au clavier : Entrée et Espace équivalent au clic.
  const surTouche = (ev, e) => {
    if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); choisir(e); }
  };

  const teinte = { jar: "var(--verdigris)", override: "#5B7FA6", aucune: "var(--rose)" };

  // Largeurs de colonnes fixes (clé, anglais, puis chaque langue ajoutée) : la table
  // ne doit jamais retomber en dessous de cette somme, quel que soit le nombre de
  // colonnes. `min-width` seul ne suffit pas à empêcher `table-layout:fixed` de
  // redistribuer l'espace en le rétrécissant proportionnellement ; on impose donc
  // une largeur explicite au moins égale à celle du conteneur (défilement horizontal
  // au-delà, plutôt qu'un écrasement des colonnes).
  const LARGEUR_CLE = 260, LARGEUR_ANGLAIS = 230, LARGEUR_LANGUE = 200;
  let largeurTableau = $derived(LARGEUR_CLE + LARGEUR_ANGLAIS + colonnes.length * LARGEUR_LANGUE);
</script>

<div class="bar">
  <div class="search">
    <input bind:value={q} placeholder="Rechercher une clé, un texte anglais, une traduction…" spellcheck="false" />
  </div>
  <div class="scope">
    {#each [["cle","clé"],["texte","texte"],["toutes","toutes langues"]] as [v, libelle]}
      <button class:on={champ === v} onclick={() => (champ = v)}>{libelle}</button>
    {/each}
  </div>
  <button class="tool" class:open={choixOuvert} onclick={() => (choixOuvert = !choixOuvert)}>+ langue</button>
  <button class="tool" class:open={filtreOuvert} onclick={() => (filtreOuvert = !filtreOuvert)}>Langues</button>
</div>

{#if filtreOuvert}
  <LangFilter {toutesLocales} bind:avec bind:sans bind:portee onFermer={() => (filtreOuvert = false)} />
{/if}

{#if choixOuvert}
  <div class="pop">
    <h5>Colonnes de langue</h5>
    {#each toutesLocales as l}
      <button class="row" class:on={colonnes.includes(l.code)} onclick={() => bascule(l.code)}>
        <span class="cb"></span>{l.libelle}<code>{l.code}</code>
      </button>
    {/each}
    <p class="hint">Les langues listées sont celles trouvées dans les fichiers.</p>
  </div>
{/if}

<div class="meta">
  <b>{res.total.toLocaleString("fr-FR")}</b> clés
  {#if res.total > 0}
    <span class="fenetre">— {debut.toLocaleString("fr-FR")}–{fin.toLocaleString("fr-FR")} affichées</span>
  {/if}
</div>

{#if erreur}
  <p class="erreur" role="alert">La recherche a échoué : {erreur}</p>
{/if}

<div class="scroll">
  <table style="width:max(100%, {largeurTableau}px)">
    <colgroup>
      <col style="width:{LARGEUR_CLE}px" />
      <col style="width:{LARGEUR_ANGLAIS}px" />
      {#each colonnes as c}<col style="width:{LARGEUR_LANGUE}px" />{/each}
    </colgroup>
    <thead>
      <tr>
        <th>Clé</th>
        <th>Anglais</th>
        {#each colonnes as c}<th>{toutesLocales.find(l => l.code === c)?.libelle ?? c}</th>{/each}
      </tr>
    </thead>
    <tbody>
      {#each res.resultats as e (e.id)}
        <tr
          class:sel={selectionne === e.id}
          tabindex="0"
          onclick={() => choisir(e)}
          onkeydown={(ev) => surTouche(ev, e)}
        >
          <td class="key">
            <span class="flag" style="background:{teinte[e.source.origine]}"></span>{e.cle}
          </td>
          <td class="en">{e.source.en ?? "—"}</td>
          <!-- e.traductions ne porte jamais en_us (l'anglais est la source, pas une
               traduction — voir index-build.js) : si la colonne "+langue" choisie est
               en_us, on lit e.source.en, sans quoi la colonne mentirait en affichant
               "—" pour des clés qui ont bel et bien un anglais. -->
          {#each colonnes as c}
            <td class="alt">{(c === "en_us" ? e.source.en : e.traductions[c]) ?? "—"}</td>
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>

{#if res.total > 0}
  <div class="pager">
    <button class="pg" onclick={pagePrecedente} disabled={page <= 1}>‹ Précédent</button>
    <span class="pginfo">Page <b>{page}</b> / {totalPages}</span>
    <label class="pgjump">
      Aller à
      <input
        type="number"
        min="1"
        max={totalPages}
        value={page}
        onchange={(ev) => allerA(ev.currentTarget.value)}
        aria-label="Aller à la page numéro"
      />
    </label>
    <button class="pg" onclick={pageSuivante} disabled={page >= totalPages}>Suivant ›</button>
  </div>
{/if}

<style>
  .bar { padding:11px 16px; border-bottom:1px solid var(--rule); display:flex; gap:9px; align-items:center; }
  .search { flex:1; background:#fff; border:1px solid var(--rule); border-radius:5px; padding:7px 10px; }
  .search input { border:0; outline:0; width:100%; font:inherit; font-size:13.5px; background:transparent; }
  .scope { display:flex; border:1px solid var(--rule); border-radius:5px; overflow:hidden; background:#fff; }
  .scope button { font-family:var(--mono); font-size:11px; padding:7px 9px; color:var(--muted);
                  border:0; background:transparent; cursor:pointer; }
  .scope button.on { background:var(--verdigris); color:#fff; }
  .tool { font-family:var(--mono); font-size:11px; padding:7px 11px; border-radius:5px; cursor:pointer;
          border:1px dashed var(--rule); background:#fff; color:var(--muted); }
  .tool.open { border-style:solid; border-color:var(--ink); color:var(--ink); background:var(--paper-2); }
  .pop { position:absolute; right:16px; top:52px; z-index:9; width:250px; background:#fff;
         border:1px solid var(--rule); border-radius:7px; padding:9px;
         box-shadow:0 12px 34px -10px rgba(21,24,28,.25); max-height:60vh; overflow-y:auto; }
  .pop h5 { margin:3px 5px 7px; font-family:var(--mono); font-size:9.5px; letter-spacing:.14em;
            text-transform:uppercase; color:var(--faint); }
  .row { display:flex; align-items:center; gap:9px; padding:6px 7px; border-radius:4px; width:100%;
         border:0; background:transparent; font:inherit; font-size:13px; cursor:pointer; text-align:left; }
  .row:hover { background:var(--paper-2); }
  .row .cb { width:13px; height:13px; border:1.5px solid var(--rule); border-radius:3px; flex:none; }
  .row.on .cb { background:var(--verdigris); border-color:var(--verdigris); }
  .row code { margin-left:auto; font-family:var(--mono); font-size:10.5px; color:var(--faint); }
  .hint { margin:7px 5px 2px; font-size:11px; color:var(--faint); line-height:1.45;
          border-top:1px solid var(--rule); padding-top:8px; }
  .meta { padding:7px 16px; border-bottom:1px solid var(--rule); background:var(--paper-2);
          font-size:12px; color:var(--muted); }
  .meta b { font-family:var(--mono); color:var(--ink); font-variant-numeric:tabular-nums; }
  .meta .fenetre { color:var(--faint); }
  .erreur { margin:0; padding:8px 16px; background:var(--rose-soft); color:var(--rose);
            font-size:12.5px; border-bottom:1px solid var(--rule); }
  .scroll { flex:1; overflow:auto; }
  table { border-collapse:collapse; table-layout:fixed; }
  thead th { position:sticky; top:0; background:var(--paper); text-align:left; font-family:var(--mono);
             font-size:9.5px; letter-spacing:.13em; text-transform:uppercase; color:var(--faint);
             padding:7px 12px; border-bottom:1px solid var(--rule); }
  tbody td { padding:8px 12px; border-bottom:1px solid var(--rule); vertical-align:top; line-height:1.4; }
  tbody tr { cursor:pointer; }
  tbody tr:hover { background:#fff; }
  tbody tr.sel { background:var(--verdigris-soft); }
  tbody tr:focus-visible { outline:2px solid var(--verdigris); outline-offset:-2px; }
  .key { font-family:var(--mono); font-size:11px; color:var(--muted); word-break:break-all; }
  .en { color:var(--muted); }
  .alt { font-size:13.5px; }
  .flag { display:inline-block; width:6px; height:6px; border-radius:50%; margin-right:7px; vertical-align:1px; }
  .pager { display:flex; align-items:center; justify-content:center; gap:14px; padding:9px 16px;
           border-top:1px solid var(--rule); background:var(--paper-2); flex:none; }
  .pg { font-family:var(--mono); font-size:11.5px; padding:6px 12px; border-radius:5px; cursor:pointer;
        border:1px solid var(--rule); background:#fff; color:var(--muted); }
  .pg:disabled { opacity:.45; cursor:default; }
  .pginfo { font-size:12.5px; color:var(--muted); }
  .pginfo b { font-family:var(--mono); color:var(--ink); font-variant-numeric:tabular-nums; }
  .pgjump { display:inline-flex; align-items:center; gap:6px; font-size:11.5px; color:var(--faint); }
  .pgjump input { width:52px; font:inherit; font-size:12.5px; padding:4px 6px; border-radius:4px;
                  border:1px solid var(--rule); background:#fff; text-align:center;
                  font-variant-numeric:tabular-nums; }
  .pg:focus-visible, .pgjump input:focus-visible { outline:2px solid var(--verdigris); outline-offset:2px; }
</style>
