<!-- site/src/views/DetailPanel.svelte -->
<script>
  import { detail } from "../lib/api.js";
  import { localeLabel } from "../../server/locales.js";

  let { id, onMarque } = $props();
  let d = $state(null);
  let brouillon = $state("");
  let problemes = $state([]);
  let sauve = $state(false);
  let enregistrement = $state(false);
  let noteRevoir = $state("");
  let pourQui = $state("ia");
  let marquageEnCours = $state(false);
  let marquageErreur = $state("");
  // Distingue « rien n'est sélectionné » d'« une entrée est sélectionnée mais son
  // chargement a échoué » — même traitement que KeysView.svelte : un message visible,
  // factuel, plutôt qu'un retour silencieux à l'état "aucune sélection" qui ferait
  // passer une panne serveur pour une absence de sélection de l'utilisateur.
  let chargementErreur = $state("");

  // Le numéro de requête permet d'ignorer toute réponse qui n'est plus la dernière
  // émise : rien ne garantit qu'une sélection plus récente reçoive sa réponse avant
  // une sélection précédente encore en vol (même garde que KeysView.svelte). Réutilisé
  // par rafraichir() ci-dessous après un enregistrement réussi, pour la même raison.
  //
  // brouillon/problemes/sauve — et de la même façon noteRevoir/pourQui/marquageErreur
  // ci-dessous — ne se réinitialisent qu'ici, sur un changement d'`id` — jamais sur un
  // simple changement de `d`. rafraichir() réaffecte `d` sans repasser par `id` : un
  // effet qui les aurait réinitialisés sur tout changement de `d` aurait effacé ce que
  // l'utilisateur vient d'écrire (traduction en cours d'édition, ou note de marquage)
  // et masqué la confirmation juste après l'enregistrement ou le marquage.
  let derniereRequete = 0;
  $effect(() => {
    d = null;
    brouillon = ""; problemes = []; sauve = false;
    noteRevoir = ""; pourQui = "ia"; marquageErreur = ""; chargementErreur = "";
    if (!id) return;
    const requete = ++derniereRequete;
    detail(id)
      .then(x => {
        if (requete !== derniereRequete) return;
        d = x;
        brouillon = x.entree.traductions.fr_fr ?? "";
        noteRevoir = x.marque?.note ?? "";
        pourQui = x.marque?.pour ?? "ia";
      })
      .catch(err => {
        if (requete !== derniereRequete) return;
        d = null;
        chargementErreur = err.message;
      });
  });

  // Recharge l'entrée après un enregistrement réussi, pour que le reste du panneau
  // (mention « identique à l'anglais », glossaire…) reflète la valeur qui vient
  // d'être écrite sur disque — sans passer par l'effet ci-dessus, qui effacerait le
  // brouillon et la confirmation.
  async function rafraichir() {
    const requete = ++derniereRequete;
    try {
      const x = await detail(id);
      if (requete === derniereRequete) d = x;
    } catch {
      // Le fichier vient d'être écrit avec succès ; si le rechargement échoue, on
      // garde l'affichage courant plutôt que de faire disparaître la confirmation.
    }
  }

  async function enregistrer() {
    enregistrement = true;
    try {
      const r = await fetch("/api/corriger", {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ id: d.entree.id, valeur: brouillon }),
      });
      const x = await r.json();
      if (x.ok) {
        sauve = true;
        problemes = [];
        await rafraichir();
      } else {
        sauve = false;
        problemes = x.problemes ?? (x.erreur ? [x.erreur] : ["Échec de l'enregistrement."]);
      }
    } catch (err) {
      sauve = false;
      problemes = [`Échec de la requête : ${err.message}`];
    } finally {
      enregistrement = false;
    }
  }

  // Recharge via rafraichir() plutôt qu'un fetch direct de /api/detail : rafraichir()
  // porte déjà la garde anti-réponse-périmée (derniereRequete) partagée avec l'effet
  // ci-dessus — la contourner ici referait exactement l'erreur qu'elle existe pour
  // éviter, pour une action différente.
  async function marquer() {
    marquageEnCours = true;
    marquageErreur = "";
    try {
      const r = await fetch("/api/revoir", {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ id: d.entree.id, note: noteRevoir, pour: pourQui }),
      });
      const x = await r.json();
      if (!r.ok) {
        marquageErreur = x.erreur ?? "Échec du marquage.";
        return;
      }
      await rafraichir();
      onMarque?.();
    } catch (err) {
      marquageErreur = `Échec de la requête : ${err.message}`;
    } finally {
      marquageEnCours = false;
    }
  }

  // Object.entries(d.entree.traductions) n'a une entrée "fr_fr" que si la clé a déjà
  // une traduction française quelque part (pack ou mod) : ~15 % des clés n'en ont
  // aucune (mesuré sur le pack : 8822/59941). Sans ce complément, le champ éditable
  // ci-dessous n'apparaîtrait jamais pour ces clés — alors que traduire un mod pas
  // encore couvert doit justement être possible depuis le site.
  let languesAffichees = $derived(
    d
      ? "fr_fr" in d.entree.traductions
        ? Object.entries(d.entree.traductions)
        : [["fr_fr", undefined], ...Object.entries(d.entree.traductions)]
      : []
  );

  const ORIGINE = {
    jar: "Fichier du mod", override: "Renommé par le pack", aucune: "Aucune source anglaise",
  };

  // Le chemin complet contient toujours "society-sunlit-valley/", mais un chemin qui
  // ne l'aurait pas se replie sur lui-même plutôt que d'afficher "undefined" à l'écran.
  const cheminCourt = (fichier) => {
    const morceaux = fichier.split("society-sunlit-valley/");
    return morceaux.length > 1 ? morceaux[1] : fichier;
  };
</script>

<aside class="panel">
  {#if !d}
    {#if chargementErreur}
      <p class="vide erreur" role="alert">Chargement du détail impossible : {chargementErreur}</p>
    {:else}
      <p class="vide">Sélectionne une entrée.</p>
    {/if}
  {:else}
    <div class="head">
      <div class="key">{d.entree.cle}</div>
      <div class="sub">{ORIGINE[d.entree.source.origine]}</div>
    </div>

    <div class="body">
      <p class="lbl">Langues</p>
      <div class="stack">
        {#if d.entree.source.en}
          <div class="lang src">
            <div class="code"><b>en_us</b> Anglais · source</div>
            <div class="txt">{d.entree.source.en}</div>
          </div>
        {/if}
        {#each languesAffichees as [loc, txt]}
          <div class="lang" class:fr={loc === "fr_fr"} class:same={txt === d.entree.source.en}>
            <div class="code"><b>{loc}</b> {localeLabel(loc)}</div>
            {#if loc === "fr_fr"}
              <textarea
                class="draft"
                bind:value={brouillon}
                oninput={() => (sauve = false)}
                aria-label="Traduction française pour {d.entree.cle}"
              ></textarea>
              {#if problemes.length}
                <ul class="pb" role="alert">{#each problemes as p}<li>{p}</li>{/each}</ul>
              {/if}
              <div class="row">
                <button class="btn pri" onclick={enregistrer} disabled={enregistrement}>
                  {enregistrement ? "Enregistrement…" : "Enregistrer"}
                </button>
                {#if sauve}<span class="ok" role="status">Enregistré</span>{/if}
              </div>
            {:else}
              <div class="txt">{txt}</div>
            {/if}
            {#if txt === d.entree.source.en}
              <div class="note">Identique à l'anglais — non traduit</div>
            {/if}
          </div>
        {/each}
      </div>

      <p class="lbl">Marquer</p>
      <div class="revoir" class:actif={!!d.marque}>
        <textarea
          bind:value={noteRevoir}
          placeholder="Pourquoi ? (facultatif)"
          aria-label="Note pour la marque à revoir de {d.entree.cle}"
        ></textarea>
        <div class="qui" role="radiogroup" aria-label="Destinataire de la marque">
          {#each [["ia","à traiter par l'IA"],["utilisateur","je m'en occupe"]] as [v, libelle]}
            <button
              type="button"
              role="radio"
              aria-checked={pourQui === v}
              class:on={pourQui === v}
              onclick={() => (pourQui = v)}
            >
              <i aria-hidden="true">{pourQui === v ? "●" : "○"}</i>{libelle}
            </button>
          {/each}
          <button class="btn warn" onclick={marquer} disabled={marquageEnCours}>
            {marquageEnCours ? "…" : (d.marque ? "Mettre à jour" : "À revoir")}
          </button>
        </div>
        {#if marquageErreur}<p class="pb" role="alert">{marquageErreur}</p>{/if}
      </div>

      <p class="lbl">Origine</p>
      <div class="box">
        <div><span>Mod</span><b>{d.entree.contexte.mod}</b></div>
        <div><span>Version</span><b class="path">{d.entree.contexte.version}</b></div>
        <div><span>Fichier</span><b class="path">{cheminCourt(d.entree.emplacement.fichier)}</b></div>
      </div>

      {#if d.provenance.evenements.length}
        <p class="lbl">Décisions</p>
        {#if d.provenance.attributionIncertaine}
          <p class="garde">
            Attribution incertaine — cette clé existe dans {d.provenance.namespaces} mods ;
            ces décisions pourraient concerner un autre mod.
          </p>
        {/if}
        {#each d.provenance.evenements as ev, i}
          <div class="ev" class:now={i === d.provenance.evenements.length - 1}>
            <div class="t">{ev.type.replaceAll("_", " ")}{ev.certitude ? ` · ${ev.certitude}` : ""}</div>
            {#if ev.fr}<div class="v">{ev.fr}</div>{/if}
            {#if ev.raison}<div class="why">{ev.raison}</div>{/if}
            {#if ev.verification_adverse}
              <div class="why">Vérification adverse · {ev.verification_adverse.verdict} — {ev.verification_adverse.raison}</div>
            {/if}
          </div>
        {/each}
      {/if}

      {#if d.glossaire.length}
        <p class="lbl">Glossaire appliqué</p>
        <div class="box">
          {#each d.glossaire as g}
            <div><span>{g.en}</span><b>{g.garde_anglais ? "gardé en anglais" : g.fr}
              <span class="path">— {g.origine}</span></b></div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</aside>

<style>
  .panel { background:var(--paper); border-left:1px solid var(--rule); display:flex;
           flex-direction:column; overflow:hidden; }
  .vide { padding:24px 16px; color:var(--faint); font-size:12.5px; }
  .vide.erreur { color:var(--rose); }
  .head { padding:13px 16px 11px; border-bottom:1px solid var(--rule); }
  .key { font-family:var(--mono); font-size:10.5px; word-break:break-all; }
  .sub { margin-top:5px; font-size:11.5px; color:var(--faint); }
  .body { flex:1; overflow-y:auto; padding:14px 16px 18px; }
  .lbl { font-family:var(--mono); font-size:9.5px; letter-spacing:.15em; text-transform:uppercase;
         color:var(--faint); margin:0 0 7px; }
  .stack { border-left:2px solid var(--ink); padding-left:12px; margin-bottom:16px; }
  .lang { padding:7px 0; }
  .lang + .lang { border-top:1px dotted var(--rule); }
  .lang .code { font-family:var(--mono); font-size:9.5px; letter-spacing:.1em; color:var(--faint); }
  .lang .code b { color:var(--muted); }
  .lang .txt { margin-top:2px; font-size:13.5px; line-height:1.45; }
  .lang.src .txt { color:var(--muted); font-style:italic; }
  .lang.fr .txt { font-weight:600; }
  .lang.fr .code b { color:var(--verdigris); }
  .lang.same { background:var(--amber-soft); margin-left:-12px; padding-left:12px; border-radius:0 4px 4px 0; }
  .lang.same .code b { color:var(--amber); }
  .lang .note { font-size:11px; color:var(--amber); margin-top:3px; }
  .draft { width:100%; margin-top:6px; border:1px solid var(--verdigris); border-radius:4px;
           background:#fff; font:inherit; font-size:13.5px; padding:7px 8px; resize:vertical;
           min-height:52px; }
  .pb { margin:7px 0 0; padding-left:16px; color:var(--rose); font-size:11.5px; line-height:1.5; }
  .row { display:flex; align-items:center; gap:9px; margin-top:7px; }
  .btn { font:inherit; font-size:12.5px; padding:6px 12px; border-radius:5px;
         border:1px solid var(--rule); background:#fff; cursor:pointer; }
  .btn.pri { background:var(--verdigris); border-color:var(--verdigris); color:#fff; font-weight:500; }
  .btn:disabled { opacity:.6; cursor:default; }
  .ok { font-size:11.5px; color:var(--verdigris); }
  .draft:focus-visible, .btn:focus-visible { outline:2px solid var(--verdigris); outline-offset:2px; }
  .box { background:var(--paper-2); border:1px solid var(--rule); border-radius:5px;
         padding:10px 12px; font-size:12.5px; margin-bottom:16px; }
  .box div { display:flex; gap:8px; padding:2px 0; }
  .box span { color:var(--faint); font-family:var(--mono); font-size:10px; letter-spacing:.06em;
              text-transform:uppercase; width:62px; flex:none; padding-top:2px; }
  .path { font-family:var(--mono); font-size:11px; color:var(--muted); word-break:break-all; }
  .garde { margin:0 0 10px; padding:7px 9px; background:var(--amber-soft); color:var(--amber);
           border-radius:4px; font-size:11.5px; line-height:1.45; }
  .ev { position:relative; padding:0 0 13px 18px; border-left:1px solid var(--rule); margin-left:4px; }
  .ev:last-child { border-left-color:transparent; padding-bottom:0; }
  .ev::before { content:""; position:absolute; left:-4px; top:4px; width:7px; height:7px;
                border-radius:50%; background:var(--paper); border:1.5px solid var(--muted); }
  .ev.now::before { border-color:var(--verdigris); background:var(--verdigris); }
  .ev .t { font-family:var(--mono); font-size:9.5px; letter-spacing:.1em; text-transform:uppercase;
           color:var(--faint); }
  .ev .v { margin-top:2px; font-size:13px; }
  .ev .why { margin-top:3px; font-size:12px; color:var(--muted); line-height:1.45; }
  .revoir { border:1px solid var(--rule); background:var(--paper-2); border-radius:6px;
            padding:10px 11px; margin-bottom:16px; }
  .revoir.actif { border-color:var(--amber); background:var(--amber-soft); }
  .revoir textarea { width:100%; border:1px solid var(--rule); border-radius:4px; background:#fff;
                     font:inherit; font-size:12.5px; padding:7px 8px; resize:vertical; min-height:48px; }
  .qui { display:flex; gap:6px; margin-top:8px; align-items:center; flex-wrap:wrap; }
  .qui button { display:inline-flex; align-items:center; gap:5px; font-family:var(--mono);
                font-size:10.5px; padding:4px 8px; border-radius:999px;
                border:1px solid var(--rule); background:#fff; color:var(--muted); cursor:pointer; }
  .qui button.on { background:var(--ink); border-color:var(--ink); color:#fff; }
  .qui button i { font-style:normal; font-size:9px; line-height:1; }
  .btn.warn { margin-left:auto; border-color:var(--amber); color:var(--amber);
              background:var(--amber-soft); font-weight:500; border-radius:5px; }
  .qui button:focus-visible, .revoir textarea:focus-visible {
    outline:2px solid var(--verdigris); outline-offset:2px;
  }
</style>
