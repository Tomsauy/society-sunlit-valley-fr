<!-- site/src/lib/Rail.svelte -->
<script>
  let { vue = $bindable("cles"), compteurs = {} } = $props();
  const onglets = [["cles","Clés"],["quetes","Quêtes"],["livres","Livres"]];
</script>

<aside class="rail">
  <div class="brand"><b>Atelier</b><span>Sunlit Valley 4.1.1</span></div>
  <nav>
    {#each onglets as [id, libelle]}
      <button class:on={vue === id} onclick={() => (vue = id)}>
        <i>{libelle}</i><em>{compteurs[id]?.toLocaleString("fr-FR") ?? "…"}</em>
      </button>
    {/each}
    <div class="sep"></div>
    <button class="queue" class:on={vue === "revoir"} onclick={() => (vue = "revoir")}>
      <i>À revoir</i><em>{compteurs.revoir ?? 0}</em>
    </button>
  </nav>
</aside>

<style>
  .rail { background:var(--bench); border-right:1px solid var(--bench-line);
          display:flex; flex-direction:column; }
  .brand { padding:16px 14px 14px; }
  .brand b { display:block; font-family:var(--mono); font-size:12px; letter-spacing:.14em;
             text-transform:uppercase; color:#EDF1F5; }
  .brand span { display:block; margin-top:3px; font-size:10.5px; color:#6F7B89; }
  nav { padding:6px 8px; display:flex; flex-direction:column; gap:1px; }
  nav button { display:flex; align-items:baseline; gap:8px; padding:8px 10px; border-radius:5px;
               color:var(--bench-ink); cursor:pointer; border:0; border-left:2px solid transparent;
               background:transparent; font:inherit; width:100%; text-align:left; }
  nav button.on { background:var(--bench-2); color:#F2F6FA; border-left-color:var(--verdigris); }
  nav i { font-style:normal; font-size:13px; }
  nav em { margin-left:auto; font-style:normal; font-family:var(--mono); font-size:10.5px;
           color:#5E6B79; font-variant-numeric:tabular-nums; }
  .sep { height:1px; background:var(--bench-line); margin:9px 10px; }
  .queue em { background:var(--amber); color:#1B2027; border-radius:999px; padding:1px 6px; }
</style>
