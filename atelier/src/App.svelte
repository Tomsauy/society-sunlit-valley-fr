<!-- site/src/App.svelte -->
<script>
  import Rail from "./lib/Rail.svelte";
  import KeysView from "./views/KeysView.svelte";
  import DetailPanel from "./views/DetailPanel.svelte";
  import ReviewView from "./views/ReviewView.svelte";
  import QuestsView from "./views/QuestsView.svelte";
  import BooksView from "./views/BooksView.svelte";
  import { sante, revoir } from "./lib/api.js";

  let vue = $state("cles");
  let compteurs = $state({});
  let choisi = $state(null);
  // Aligné sur le traitement déjà en place dans KeysView.svelte : un message visible,
  // factuel, plutôt qu'un rejet de promesse non géré. sante()/revoir() passent par le
  // helper j() de lib/api.js, qui lève sur un statut non-ok — sans .catch ici, un 500
  // laissait les compteurs du rail bloqués sur "…" indéfiniment, en silence.
  //
  // Correctif post-revue : un seul état partagé entre les deux sources faisait que
  // chacune effaçait l'erreur de l'autre dès qu'elle réussissait elle-même — sur
  // /api/sante en 500 et /api/revoir en 200, le succès de actualiserRevoir() effaçait
  // le message posé par l'échec de sante(), et rien n'était affiché tout en laissant
  // les compteurs cles/quêtes/livres bloqués sur "…" indéfiniment (reproduit : le
  // symptôme visé par le commentaire ci-dessus n'était donc fermé qu'à moitié). Deux
  // états distincts : chaque source ne pose et n'efface plus que SA propre erreur.
  let erreurSante = $state("");
  let erreurRevoir = $state("");
  // Distinct des deux erreurs ci-dessus : /api/sante répond 200, mais signale dans
  // `manquantes` qu'une racine configurable (pack, langues extraites, config des
  // quêtes) n'est pas là — voir paths.js/read-pack.js/read-mods.js/read-quests.js. Sans
  // ce message, les vues concernées se contenteraient d'apparaître vides, sans dire
  // pourquoi.
  let avisManquantes = $state("");

  // Partagé entre le montage initial et les actions qui changent la file (marquer
  // depuis DetailPanel, retirer depuis ReviewView) : le rail doit refléter le compte
  // à jour sans attendre un remontage de l'app.
  function actualiserRevoir() {
    revoir()
      .then(m => { compteurs = { ...compteurs, revoir: m.length }; erreurRevoir = ""; })
      .catch(err => { erreurRevoir = `Chargement de la file à revoir impossible : ${err.message}`; });
  }

  $effect(() => {
    sante()
      .then(s => {
        compteurs = { ...compteurs, cles: s.fichiers, quetes: s.quetes, livres: s.livres };
        erreurSante = "";
        avisManquantes = s.manquantes?.length ? s.manquantes.join(" · ") : "";
      })
      .catch(err => { erreurSante = `État du serveur indisponible : ${err.message}`; });
    actualiserRevoir();
  });

  // Quêtes et Livres portent chacune leur propre panneau de lecture (arbre + bilingue) :
  // le panneau de détail, qui affiche une entrée de la vue Clés, n'a rien de pertinent à
  // y montrer pour elles.
  const vuePleine = (v) => v === "quetes" || v === "livres";
</script>

<div class="app" class:pleine={vuePleine(vue)}>
  <Rail bind:vue {compteurs} />
  <main class="surface">
    {#if erreurSante}<p class="bandeau-erreur" role="alert">{erreurSante}</p>{/if}
    {#if avisManquantes}<p class="bandeau-avis" role="status">{avisManquantes}</p>{/if}
    {#if erreurRevoir}<p class="bandeau-erreur" role="alert">{erreurRevoir}</p>{/if}
    {#if vue === "cles"}
      <KeysView onSelect={(id) => (choisi = id)} />
    {:else if vue === "revoir"}
      <ReviewView onSelect={(id) => (choisi = id)} onChange={actualiserRevoir} />
    {:else if vue === "quetes"}
      <QuestsView />
    {:else if vue === "livres"}
      <BooksView />
    {:else}
      <p class="attente">La vue « {vue} » arrive à une tâche suivante.</p>
    {/if}
  </main>
  {#if !vuePleine(vue)}
    <!-- Voir le commentaire sur vuePleine ci-dessus : laisserait sinon une colonne
         vide de 306px pour ces deux vues. -->
    <DetailPanel id={choisi} onMarque={actualiserRevoir} />
  {/if}
</div>

<style>
  .app { display:grid; grid-template-columns:176px 1fr 306px; height:100vh; }
  .app.pleine { grid-template-columns:176px 1fr; }
  .surface { background:var(--paper); display:flex; flex-direction:column;
             overflow:hidden; position:relative; }
  .attente { padding:32px; color:var(--faint); }
  .bandeau-erreur { margin:0; padding:8px 16px; background:var(--rose-soft); color:var(--rose);
                     font-size:12.5px; border-bottom:1px solid var(--rule); }
  .bandeau-avis { margin:0; padding:8px 16px; background:var(--amber-soft); color:var(--amber);
                   font-size:12.5px; border-bottom:1px solid var(--rule); }
</style>
