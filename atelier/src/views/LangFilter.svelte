<!-- site/src/views/LangFilter.svelte -->
<script>
  let { toutesLocales = [], avec = $bindable([]), sans = $bindable([]),
        portee = $bindable("pack_et_mods"), onFermer } = $props();
  let ouvertPour = $state(null);

  const ajouter = (clause, code) => {
    if (clause === "avec") avec = [...new Set([...avec, code])];
    else sans = [...new Set([...sans, code])];
    ouvertPour = null;
  };
  const retirer = (clause, code) => {
    if (clause === "avec") avec = avec.filter(c => c !== code);
    else sans = sans.filter(c => c !== code);
  };
  const libelle = (code) => toutesLocales.find(l => l.code === code)?.libelle ?? code;
</script>

<div class="builder">
  <h5>Filtrer par langues</h5>
  <p class="hint">Trouve les trous : ce que d'autres ont traduit et pas nous, ou l'inverse.</p>

  {#each [["avec","Avec",avec],["sans","Sans",sans]] as [clause, mot, valeurs]}
    <div class="clause">
      <span class="verb {clause}">{mot}</span>
      <div class="picks">
        {#each valeurs as code}
          <span class="lg">{libelle(code)} <code>{code}</code>
            <button class="x" onclick={() => retirer(clause, code)} aria-label="Retirer {libelle(code)}">×</button></span>
          <span class="or">{clause === "avec" ? "ou" : "ni"}</span>
        {/each}
        <button class="lg plus" onclick={() => (ouvertPour = ouvertPour === clause ? null : clause)}>+ langue</button>
      </div>
      {#if ouvertPour === clause}
        <div class="menu">
          {#each toutesLocales as l}
            <button onclick={() => ajouter(clause, l.code)}>{l.libelle} <code>{l.code}</code></button>
          {/each}
        </div>
      {/if}
    </div>
  {/each}

  <div class="scopebox">
    <span>Chercher dans :</span>
    {#each [["pack_et_mods","le pack et les mods"],["pack","le pack seul"]] as [v, libelleP]}
      <button class="radio" class:on={portee === v} onclick={() => (portee = v)}><i></i>{libelleP}</button>
    {/each}
    <button class="btn pri" onclick={onFermer}>Appliquer</button>
  </div>
</div>

<style>
  .builder { position:absolute; top:52px; left:16px; right:16px; z-index:9; background:#fff;
             border:1px solid var(--rule); border-radius:8px; padding:14px 16px 12px;
             box-shadow:0 16px 44px -12px rgba(21,24,28,.3); }
  h5 { margin:0 0 3px; font-family:var(--mono); font-size:9.5px; letter-spacing:.14em;
       text-transform:uppercase; color:var(--faint); }
  .hint { margin:0 0 12px; font-size:12px; color:var(--faint); }
  .clause { display:flex; align-items:flex-start; gap:10px; padding:9px 0; position:relative; }
  .clause + .clause { border-top:1px dashed var(--rule); }
  .verb { font-family:var(--mono); font-size:11px; letter-spacing:.06em; text-transform:uppercase;
          padding:5px 9px; border-radius:4px; width:64px; text-align:center; flex:none; }
  .verb.avec { background:var(--verdigris-soft); color:var(--verdigris); }
  .verb.sans { background:var(--rose-soft); color:var(--rose); }
  .picks { display:flex; flex-wrap:wrap; gap:6px; align-items:center; flex:1; }
  .lg { display:inline-flex; align-items:center; gap:6px; border:1px solid var(--rule);
        background:var(--paper-2); border-radius:999px; padding:4px 10px; font-size:12.5px; }
  .lg code { font-family:var(--mono); font-size:10px; color:var(--faint); }
  .lg .x { border:0; background:transparent; color:var(--faint); cursor:pointer; font-size:14px; padding:0; }
  .lg.plus { border-style:dashed; background:#fff; color:var(--muted); cursor:pointer; font:inherit; font-size:12.5px; }
  .or { font-family:var(--mono); font-size:10px; color:var(--faint); }
  .menu { position:absolute; top:100%; left:74px; z-index:12; background:#fff; border:1px solid var(--rule);
          border-radius:6px; padding:6px; max-height:240px; overflow-y:auto; width:230px;
          box-shadow:0 10px 26px -8px rgba(21,24,28,.25); }
  .menu button { display:flex; width:100%; gap:8px; padding:5px 7px; border:0; background:transparent;
                 font:inherit; font-size:12.5px; cursor:pointer; border-radius:4px; text-align:left; }
  .menu button:hover { background:var(--paper-2); }
  .menu code { margin-left:auto; font-family:var(--mono); font-size:10px; color:var(--faint); }
  .scopebox { display:flex; align-items:center; gap:16px; margin-top:11px; padding-top:11px;
              border-top:1px solid var(--rule); font-size:12.5px; color:var(--muted); }
  .radio { display:inline-flex; align-items:center; gap:7px; border:0; background:transparent;
           font:inherit; font-size:12.5px; color:var(--muted); cursor:pointer; }
  .radio i { width:12px; height:12px; border-radius:50%; border:1.5px solid var(--rule); flex:none; }
  .radio.on i { border-color:var(--verdigris); border-width:4px; }
  .btn { font:inherit; font-size:12.5px; padding:6px 13px; border-radius:5px;
         border:1px solid var(--rule); background:#fff; cursor:pointer; }
  .btn.pri { margin-left:auto; background:var(--verdigris); border-color:var(--verdigris);
             color:#fff; font-weight:500; }
  button:focus-visible { outline:2px solid var(--verdigris); outline-offset:2px; }
</style>
