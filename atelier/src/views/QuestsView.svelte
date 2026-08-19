<!-- site/src/views/QuestsView.svelte -->
<script>
  import { quetes } from "../lib/api.js";
  import { localeLabel } from "../../server/locales.js";
  import Peek from "../lib/Peek.svelte";

  let groupes = $state([]);
  let erreur = $state("");
  let ouverts = $state(new Set());
  // { type: "chapitre", chapitre } | { type: "quete", quete } | null — un clic sur un
  // chapitre choisit son en-tête (titre, sous-titre, compte traduisibles/bruts) dans le
  // panneau de lecture, sans empêcher par ailleurs de le déplier/replier dans l'arbre.
  let selection = $state(null);
  let masqueesVisibles = $state(true);
  let toutesLangues = $state(false);

  // Aperçu du rendu en jeu (tâche 13, correctif) — Peek n'est monté dans le DOM que
  // lorsqu'il est effectivement affiché, pour qu'il réserve sa place dans la mise en
  // page au lieu de flotter par-dessus le champ suivant. Un panneau en position absolue
  // recouvrait le champ suivant ET interceptait ses événements de pointeur dès que son
  // contenu dépassait le petit espace entre deux paragraphes — mesuré en pilotant
  // l'appli : le bouton d'aperçu du champ suivant devenait inatteignable en ligne droite
  // à la souris. Deux ensembles (survol / focus clavier) plutôt qu'un seul : la souris
  // qui quitte le paragraphe ne doit pas fermer un aperçu encore focalisé au clavier, et
  // inversement — même logique que `ouverts` ci-dessus (copie, mutation, réaffectation).
  let survoles = $state(new Set());
  let focuses = $state(new Set());
  const marquer = (ensemble, cle, present) => {
    const s = new Set(ensemble);
    present ? s.add(cle) : s.delete(cle);
    return s;
  };
  const apercuOuvert = (cle) => survoles.has(cle) || focuses.has(cle);

  // La fermeture au survol est différée, pas immédiate — sans quoi la mise en page ci-
  // dessus crée un second défaut, plus discret mais réel (mesuré au pilotage) : le champ
  // qui referme son aperçu remonte le champ SUIVANT exactement au moment où la souris
  // franchit leur frontière commune, et une descente continue peut alors atterrir dans
  // l'espace vide qui vient de se libérer, entre les deux. Différer laisse le temps à la
  // souris d'entrer dans le champ suivant — TOUJOURS à sa position encore poussée vers
  // le bas à cet instant — avant que le premier ne se referme et ne le fasse remonter ;
  // une fois survolé, un champ le reste tant que la souris ne l'a pas réellement quitté,
  // le remontée sous un curseur immobile ne déclenche aucun événement de survol.
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
  // Identifiant DOM stable dérivé de la clé du champ (déjà unique, voir read-quests.js) —
  // relie le bouton au panneau qu'il déclenche via aria-controls (voir plus bas).
  const idApercu = (cle) => `peek-${cle.replace(/[^a-zA-Z0-9_-]/g, "-")}`;

  $effect(() => {
    quetes()
      .then(g => { groupes = g; erreur = ""; })
      .catch(err => { erreur = `Chargement impossible : ${err.message}`; });
  });

  // Reconstruit, côté client, l'équivalent du parQuete du serveur : une dépendance peut
  // désigner une quête d'un AUTRE chapitre (mesuré sur le livre réel — armor_weapons__tools
  // dépend par exemple d'une quête de getting_started), donc la résolution ne peut pas se
  // limiter au chapitre courant.
  let parQuete = $derived(new Map(
    groupes.flatMap(g => g.chapitres).flatMap(c => c.quetes).map(q => [q.questId, q])
  ));

  const basculer = (fichier) => {
    const s = new Set(ouverts);
    s.has(fichier) ? s.delete(fichier) : s.add(fichier);
    ouverts = s;
  };

  const choisirChapitre = (c) => {
    basculer(c.fichier);
    selection = { type: "chapitre", chapitre: c };
  };
  const choisirQuete = (q) => { selection = { type: "quete", quete: q }; };

  const champsTexte = (q) => q.champs.filter(c => !c.nom.startsWith("task."));
  const champsTaches = (q) => q.champs.filter(c => c.nom.startsWith("task."));

  // Vingt-quatre quêtes du chapitre II (67 traduisibles, 43 titrées) n'ont pas de champ
  // title: mais portent quand même un autre champ traduisible (description, sous-titre,
  // intitulé de tâche) — c'est ce champ-là qu'on affiche en repère dans l'arbre plutôt que
  // l'identifiant technique brut, qui ne dit rien de la quête à l'utilisateur.
  const libelleQuete = (q) => {
    if (q.titre.fr_fr) return q.titre.fr_fr;
    if (q.titre.en_us) return q.titre.en_us;
    const autre = q.champs.find(c => c.nom !== "title" && (c.valeurs.fr_fr || c.valeurs.en_us));
    if (autre) {
      const txt = autre.valeurs.fr_fr ?? autre.valeurs.en_us;
      return txt.length > 64 ? `${txt.slice(0, 61)}…` : txt;
    }
    return `Quête sans titre (${q.questId.replace(/^quest/, "")})`;
  };

  // Une dépendance vers une quête sans aucun champ traduisible (jalon de collection à
  // simple icône, par exemple) n'a pas d'entrée dans parQuete : elle reste réelle et doit
  // être signalée, pas masquée faute de titre — d'où le repli explicite plutôt qu'un
  // filtrage silencieux de la liste des prérequis.
  const libelleDependance = (id) => {
    const cible = parQuete.get(id);
    if (!cible) return { texte: "Quête sans texte traduisible", sousTexte: id.replace(/^quest/, "") };
    const fr = cible.titre.fr_fr, en = cible.titre.en_us;
    return { texte: libelleQuete(cible), sousTexte: fr && en && fr !== en ? en : null };
  };
</script>

<div class="cols">
  <aside class="tree">
    <label class="switch">
      <input type="checkbox" bind:checked={masqueesVisibles} />
      afficher les quêtes masquées en jeu
    </label>
    {#if erreur}<p class="erreur" role="alert">{erreur}</p>{/if}
    {#each groupes as g}
      {#if g.chapitres.length}
        <div class="grp">{g.titre}</div>
        {#each g.chapitres as c}
          <button
            class="ch"
            class:open={ouverts.has(c.fichier)}
            class:sel={selection?.type === "chapitre" && selection.chapitre.fichier === c.fichier}
            aria-expanded={ouverts.has(c.fichier)}
            onclick={() => choisirChapitre(c)}
          >
            <span class="car" aria-hidden="true">{ouverts.has(c.fichier) ? "▾" : "▸"}</span>
            <span class="lib">{c.titre}</span>
            <em>{c.quetes.length}{c.quetes.length !== c.totalQuetes ? `/${c.totalQuetes}` : ""}</em>
          </button>
          {#if ouverts.has(c.fichier)}
            {#each c.quetes.filter(q => masqueesVisibles || !q.masquee) as q}
              <button
                class="q"
                class:on={selection?.type === "quete" && selection.quete.questId === q.questId}
                onclick={() => choisirQuete(q)}
              >
                <span class="lib">{libelleQuete(q)}</span>
                {#if q.masquee}
                  <span class="hid" aria-hidden="true" title="Masquée jusqu'aux prérequis">◐</span>
                  <span class="sr-only"> — masquée en jeu jusqu'aux prérequis</span>
                {/if}
              </button>
            {:else}
              <p class="rien">Aucune quête visible en jeu dans ce chapitre.</p>
            {/each}
          {/if}
        {/each}
      {/if}
    {/each}
  </aside>

  <main class="read">
    {#if !selection}
      <p class="vide">Choisis un chapitre ou une quête.</p>
    {:else if selection.type === "chapitre"}
      {@const c = selection.chapitre}
      <div class="entete-chapitre">
        <h1>{c.titre}</h1>
        {#if c.sousTitre}<p class="sous">{c.sousTitre}</p>{/if}
        <p class="compte">
          <b>{c.quetes.length.toLocaleString("fr-FR")}</b> quête{c.quetes.length > 1 ? "s" : ""}
          traduisible{c.quetes.length > 1 ? "s" : ""} sur {c.totalQuetes.toLocaleString("fr-FR")}.
        </p>
        {#if c.totalQuetes > c.quetes.length}
          <p class="note">
            {c.totalQuetes - c.quetes.length} objet{c.totalQuetes - c.quetes.length > 1 ? "s" : ""}
            de ce chapitre ne porte{c.totalQuetes - c.quetes.length > 1 ? "nt" : ""} aucun champ de
            texte (icône seule, jalon de collection…) — rien à relire, donc absent de la liste
            ci-contre.
          </p>
        {/if}
      </div>
    {:else}
      {@const quete = selection.quete}
      {#if quete.masquee}
        <div class="avis">
          <p>Masquée en jeu jusqu'à ce que ses prérequis soient terminés{quete.dependances.length ? " :" : "."}</p>
          {#if quete.dependances.length}
            <ul class="deps">
              {#each quete.dependances as d}
                {@const l = libelleDependance(d)}
                <li>{l.texte}{#if l.sousTexte}<span class="en"> ({l.sousTexte})</span>{/if}</li>
              {/each}
            </ul>
          {/if}
        </div>
      {/if}
      <div class="titre">
        <div><div class="lab">Anglais</div><h1>{quete.titre.en_us ?? "—"}</h1></div>
        <div><div class="lab">Français</div><h1>{quete.titre.fr_fr ?? "—"}</h1></div>
      </div>
      <button class="tool" class:open={toutesLangues} onclick={() => (toutesLangues = !toutesLangues)}>
        {toutesLangues ? "Anglais / Français seulement" : "Toutes les langues"}
      </button>
      {#each champsTexte(quete) as c}
        {#if c.nom !== "title"}
          <!-- svelte-ignore a11y_no_static_element_interactions -- ce div n'est pas
               lui-même l'affordance interactive : le survol n'est qu'un confort souris
               en plus du bouton .peekhook ci-dessous, qui porte son propre chemin
               clavier indépendant (focus/blur) et son propre aria-expanded. -->
          <div
            class="para"
            onmouseenter={() => survolerDedans(c.cle)}
            onmouseleave={() => survolerDehors(c.cle)}
          >
            <div class="fld">{c.nom}</div>
            <!-- Aperçu du rendu en jeu (tâche 13) : visible au survol de tout le
                 paragraphe, ou dès que ce bouton reçoit le focus clavier — Peek
                 lui-même ne contient aucun élément focusable, donc Tab le traverse
                 sans jamais y piéger le focus. -->
            <button
              type="button"
              class="peekhook"
              aria-label="Aperçu du rendu en jeu"
              aria-expanded={apercuOuvert(c.cle)}
              aria-controls={idApercu(c.cle)}
              onfocus={() => (focuses = marquer(focuses, c.cle, true))}
              onblur={() => (focuses = marquer(focuses, c.cle, false))}
            >👁</button>
            {#if toutesLangues}
              {#each Object.entries(c.valeurs) as [loc, txt]}
                <div class="txt multi"><span class="loc">{localeLabel(loc)}</span>{txt}</div>
              {:else}
                <div class="txt vide">Aucune langue ne traduit ce champ.</div>
              {/each}
            {:else}
              <div class="txt en">{c.valeurs.en_us ?? "—"}</div>
              <div class="txt">{c.valeurs.fr_fr ?? "—"}</div>
            {/if}
            {#if apercuOuvert(c.cle)}
              <Peek id={idApercu(c.cle)} en={c.valeurs.en_us} fr={c.valeurs.fr_fr} dialecte="quest" />
            {/if}
          </div>
        {/if}
      {/each}
      {#if champsTaches(quete).length}
        <div class="taches">
          <div class="lab">Objectifs</div>
          {#each champsTaches(quete) as c}
            <!-- svelte-ignore a11y_no_static_element_interactions -- même raison que
                 .para ci-dessus : .peekhook porte l'affordance et le chemin clavier. -->
            <div
              class="tache"
              onmouseenter={() => survolerDedans(c.cle)}
              onmouseleave={() => survolerDehors(c.cle)}
            >
              <button
                type="button"
                class="peekhook"
                aria-label="Aperçu du rendu en jeu"
                aria-expanded={apercuOuvert(c.cle)}
                aria-controls={idApercu(c.cle)}
                onfocus={() => (focuses = marquer(focuses, c.cle, true))}
                onblur={() => (focuses = marquer(focuses, c.cle, false))}
              >👁</button>
              <div class="en">{c.valeurs.en_us ?? "—"}</div>
              <div>{c.valeurs.fr_fr ?? "—"}</div>
              {#if apercuOuvert(c.cle)}
                <Peek id={idApercu(c.cle)} en={c.valeurs.en_us} fr={c.valeurs.fr_fr} dialecte="quest" />
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    {/if}
  </main>
</div>

<style>
  .cols { display:grid; grid-template-columns:268px 1fr; height:100%; overflow:hidden; }
  .tree { background:var(--paper-2); border-right:1px solid var(--rule); overflow-y:auto; }
  .switch { display:flex; gap:7px; align-items:center; padding:10px 12px; font-size:11.5px;
            color:var(--muted); border-bottom:1px solid var(--rule); }
  .erreur { margin:0; padding:8px 12px; background:var(--rose-soft); color:var(--rose);
            font-size:12px; border-bottom:1px solid var(--rule); }
  .grp { padding:11px 12px 5px; font-family:var(--mono); font-size:9.5px; letter-spacing:.15em;
         text-transform:uppercase; color:var(--faint); }
  .ch, .q { display:flex; width:100%; border:0; background:transparent; font:inherit; cursor:pointer;
            text-align:left; align-items:center; }
  .ch { gap:8px; padding:6px 12px 6px 16px; font-size:12.5px; color:var(--muted); }
  .ch:hover, .q:hover { background:#fff; }
  .ch.open { background:#fff; color:var(--ink); font-weight:500; }
  .ch.sel { border-left:2px solid var(--verdigris); }
  .ch .car { font-size:8px; color:var(--faint); width:8px; flex:none; }
  .ch .lib, .q .lib { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .ch em { margin-left:auto; padding-left:8px; font-style:normal; font-family:var(--mono);
           font-size:9.5px; color:var(--faint); flex:none; font-variant-numeric:tabular-nums; }
  .q { padding:5px 12px 5px 38px; font-size:12px; color:var(--muted); gap:6px;
       border-left:2px solid transparent; }
  .q.on { background:#fff; color:var(--ink); border-left-color:var(--verdigris); font-weight:500; }
  .hid { color:var(--amber); font-size:10px; flex:none; }
  .rien { margin:0; padding:6px 12px 6px 38px; font-size:11.5px; color:var(--faint); font-style:italic; }
  .sr-only { position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0);
             white-space:nowrap; }
  .ch:focus-visible, .q:focus-visible, .tool:focus-visible {
    outline:2px solid var(--verdigris); outline-offset:-2px;
  }
  .read { overflow-y:auto; padding:20px 22px 44px; }
  .vide { color:var(--faint); }
  .entete-chapitre h1 { margin:0 0 4px; font-size:22px; }
  .entete-chapitre .sous { margin:0 0 10px; color:var(--muted); font-size:14px; font-style:italic; }
  .entete-chapitre .compte { font-size:13.5px; color:var(--muted); }
  .entete-chapitre .compte b { font-family:var(--mono); color:var(--ink); }
  .entete-chapitre .note { margin-top:8px; padding:8px 11px; background:var(--paper-2);
                            border:1px solid var(--rule); border-radius:6px; font-size:12px;
                            color:var(--muted); line-height:1.5; }
  .avis { background:var(--amber-soft); border:1px solid var(--amber); color:var(--amber);
          border-radius:6px; padding:9px 12px; font-size:12.5px; margin-bottom:14px; }
  .avis p { margin:0; }
  .deps { margin:6px 0 0; padding-left:18px; }
  .deps li { margin-top:2px; }
  .deps .en { color:var(--muted); font-style:italic; }
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
  .para { position:relative; display:grid; grid-template-columns:1fr 1fr; gap:22px; padding:11px 0;
          border-bottom:1px solid var(--rule); }
  .para:has(.multi) { grid-template-columns:1fr; }
  .fld { grid-column:1/-1; font-family:var(--mono); font-size:9px; letter-spacing:.12em;
         text-transform:uppercase; color:var(--faint); margin-bottom:-4px; }
  /* Aperçu du rendu en jeu (tâche 13) — bouton discret, toujours dans le DOM (jamais
     seulement au survol : un lecteur d'écran ou un clavier doit pouvoir l'atteindre),
     déclenché au survol de la souris OU dès que ce bouton reçoit le focus, pour un
     équivalent clavier réel (logique en JS, voir apercuOuvert ci-dessus). */
  .para .peekhook, .tache .peekhook {
    position:absolute; top:8px; right:0; width:20px; height:20px; padding:0; z-index:1;
    display:flex; align-items:center; justify-content:center; line-height:1;
    border:1px solid var(--rule); border-radius:5px; background:#fff; color:var(--faint);
    font-size:11px; cursor:pointer;
  }
  .para .peekhook:hover, .tache .peekhook:hover { color:var(--ink); border-color:var(--verdigris); }
  .para .peekhook:focus-visible, .tache .peekhook:focus-visible {
    outline:2px solid var(--verdigris); outline-offset:1px;
  }
  /* Correctif : Peek n'est plus en position absolue. Monté seulement quand ouvert
     (voir apercuOuvert), il occupe une vraie ligne de la grille et pousse le reste du
     contenu — jamais de recouvrement du champ suivant ni de vol de ses événements de
     pointeur, quelle que soit la hauteur de son contenu (cas mesuré : liste de
     couleurs Patchouli sur plusieurs lignes, plus haute que l'espace entre deux
     champs). */
  .para :global(.peek), .tache :global(.peek) { grid-column:1/-1; margin-top:8px; }
  .txt { line-height:1.65; }
  .txt.en { color:var(--muted); }
  .txt.vide { color:var(--faint); font-style:italic; font-size:12.5px; }
  .txt.multi { display:flex; gap:10px; padding:3px 0; }
  .txt.multi .loc { flex:none; width:150px; font-family:var(--mono); font-size:10px;
                     color:var(--faint); padding-top:3px; }
  .taches { margin-top:18px; background:var(--paper-2); border:1px solid var(--rule);
            border-radius:6px; padding:12px 14px; }
  .tache { position:relative; display:grid; grid-template-columns:1fr 1fr; gap:22px; padding:5px 0; font-size:13px; }
  .tache + .tache { border-top:1px dotted var(--rule); }
  .tache .en { color:var(--muted); }
</style>
