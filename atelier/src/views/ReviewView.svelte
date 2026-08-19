<!-- site/src/views/ReviewView.svelte -->
<script>
  import { revoir } from "../lib/api.js";

  let { onSelect, onChange } = $props();
  let marques = $state([]);
  let erreur = $state("");

  // Aligné sur le traitement déjà en place dans KeysView.svelte : un statut non-ok
  // devient une exception (revoir(), comme recherche()/locales(), passe par le helper
  // j() de lib/api.js, qui vérifie r.ok avant de renvoyer le JSON) et un message
  // visible, factuel, plutôt qu'un silence — sur une file corrompue, le serveur répond
  // 500 avec un message explicite (voir review-queue.js/api.js) qu'il faut afficher,
  // pas absorber dans une liste vide qui se lirait comme « rien à revoir ».
  function charger() {
    return revoir()
      .then(m => { marques = m; erreur = ""; })
      .catch(err => { erreur = `Chargement impossible : ${err.message}`; });
  }

  $effect(() => { charger(); });

  async function retirer(identifiant) {
    try {
      const r = await fetch(`/api/revoir/${encodeURIComponent(identifiant)}`, { method: "DELETE" });
      if (!r.ok) {
        // Même garde que /corriger côté DetailPanel : sur une file corrompue, le
        // serveur renvoie 500 avec un message explicite (retirerMarque refuse
        // d'écrire) — sans ce contrôle, l'interface rechargeait en silence, la carte
        // restait affichée et rien n'indiquait que le retrait avait échoué.
        const x = await r.json().catch(() => ({}));
        erreur = x.erreur ?? `Échec du retrait (${r.status}).`;
        return;
      }
      erreur = "";
      await charger();
      onChange?.();
    } catch (err) {
      erreur = `Échec de la requête : ${err.message}`;
    }
  }
</script>

<!-- Correctif post-revue : sur une file corrompue, l'ancien code affichait le message
     d'erreur EN PLUS de « 0 entrée à revoir » et « Rien à revoir. » — trois affirmations
     qui se contredisent (une panne n'est pas une liste vide, voir le motif déjà fermé
     ailleurs sur cette branche). Le compte et l'état vide ne s'affichent donc plus tant
     qu'une erreur est active : soit on montre ce qu'on sait (le compte, les cartes, ou
     "rien à revoir"), soit on dit qu'on ne sait pas (l'erreur) — jamais les deux. -->
{#if erreur}
  <p class="erreur" role="alert">{erreur}</p>
{:else}
  <div class="meta"><b>{marques.length}</b> entrée{marques.length > 1 ? "s" : ""} à revoir</div>
{/if}
<div class="scroll">
  {#each marques as m (m.id ?? m.cle)}
    <article class="carte" class:ia={m.pour === "ia"}>
      <header>
        <span class="cle">{m.cle}</span>
        <span class="pour">{m.pour === "ia" ? "pour l'IA" : "pour moi"}</span>
        <span class="date">{m.ajoute_le}</span>
      </header>
      <p class="actuel">{m.fr_actuel}</p>
      {#if m.note}<p class="note">{m.note}</p>{/if}
      <footer>
        {#if m.id}
          <button onclick={() => onSelect?.(m.id)}>Ouvrir</button>
        {:else}
          <!-- Marque antérieure au champ id (correction A) : sa clé nue ne suffit pas
               à reconstruire un identifiant fiable (le namespace n'est pas déductible
               de la clé — ex. society_tips.tip.villager_decor). Un bouton qui mènerait
               vers un identifiant inventé resterait muet ; on l'omet plutôt. -->
          <span class="sanslien">Pas de lien direct (marque antérieure)</span>
        {/if}
        <button onclick={() => retirer(m.id ?? m.cle)}>Retirer</button>
      </footer>
    </article>
  {:else}
    {#if !erreur}<p class="vide">Rien à revoir.</p>{/if}
  {/each}
</div>

<style>
  .meta { padding:7px 16px; border-bottom:1px solid var(--rule); background:var(--paper-2);
          font-size:12px; color:var(--muted); }
  .meta b { font-family:var(--mono); color:var(--ink); }
  .erreur { margin:0; padding:8px 16px; background:var(--rose-soft); color:var(--rose);
            font-size:12.5px; border-bottom:1px solid var(--rule); }
  .scroll { flex:1; overflow-y:auto; padding:14px 16px; display:flex; flex-direction:column; gap:10px; }
  .carte { border:1px solid var(--rule); border-left:3px solid var(--muted); border-radius:6px;
           padding:11px 13px; background:#fff; }
  .carte.ia { border-left-color:var(--amber); }
  header { display:flex; align-items:baseline; gap:9px; margin-bottom:6px; }
  .cle { font-family:var(--mono); font-size:11px; color:var(--muted); word-break:break-all; }
  .pour { font-family:var(--mono); font-size:9.5px; text-transform:uppercase; letter-spacing:.1em;
          color:var(--amber); }
  .date { margin-left:auto; font-family:var(--mono); font-size:10px; color:var(--faint); }
  .actuel { margin:0 0 5px; font-size:13.5px; }
  .note { margin:0; font-size:12.5px; color:var(--muted); line-height:1.5; }
  footer { display:flex; align-items:center; gap:7px; margin-top:9px; }
  footer button { font:inherit; font-size:12px; padding:5px 10px; border-radius:5px;
                  border:1px solid var(--rule); background:var(--paper-2); cursor:pointer; }
  footer button:focus-visible { outline:2px solid var(--verdigris); outline-offset:2px; }
  .sanslien { font-size:11.5px; color:var(--faint); font-style:italic; }
  .vide { color:var(--faint); font-size:12.5px; }
</style>
