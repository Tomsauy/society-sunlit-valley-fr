<!-- site/src/lib/Peek.svelte -->
<!--
  Aperçu du rendu « en jeu » d'un champ, anglais et français côte à côte, plus une
  alerte si les deux langues ne portent pas les mêmes codes de mise en forme (§8 du
  brief, codesDe : les validations existantes vérifient la PRÉSENCE des codes, pas
  leur IDENTITÉ — un &o italique rendu par un &3 cyan est une erreur invisible en
  lecture brute).

  Ce composant est un simple panneau HTML sans aucun élément focusable (pas de bouton,
  lien ou champ à l'intérieur) : ce qui déclenche son affichage — survol ou clavier —
  est porté par l'appelant (QuestsView.svelte / BooksView.svelte), jamais par Peek
  lui-même. Ainsi le focus ne peut jamais rester « piégé » dedans : Tab le traverse
  sans s'y arrêter, plancher d'accessibilité demandé pour la tâche 13.

  Correctif (relecture) : ce composant n'est monté par l'appelant QUE lorsqu'il doit
  être visible — jamais laissé dans le DOM masqué par une visibilité CSS. `.peek` est
  donc un bloc normal (pas de position absolue) : une fois monté, il réserve sa propre
  place dans la mise en page et pousse le contenu qui suit, au lieu de flotter par-dessus
  le champ suivant et de lui voler ses événements de pointeur — défaut mesuré en
  pilotant l'appli sur une page à deux champs (le bouton du second devenait inatteignable
  en ligne droite à la souris dès que le panneau du premier dépassait le petit espace
  entre les deux).
-->
<script>
  import { rendre, codesDe } from "./mc-render.js";

  // `id`, optionnel : l'appelant le fournit pour relier son bouton déclencheur à ce
  // panneau via aria-controls (voir QuestsView.svelte/BooksView.svelte) — sans quoi un
  // lecteur d'écran qui tabule sur le bouton n'est averti d'aucun contenu qui vient de
  // se révéler (relevé en revue : role="note" seul ne relie rien au bouton).
  let { en = "", fr = "", dialecte = "quest", id = undefined } = $props();

  // On ne signale un écart que si l'anglais existe : un champ non traduit (fr absent)
  // relève déjà de la traçabilité (tâche 8), pas d'un désaccord de codes.
  const ecart = $derived(!!en && codesDe(en).join("|") !== codesDe(fr).join("|"));
</script>

<div class="peek {dialecte}" role="note" {id}>
  {#if ecart}
    <div class="alerte">
      Codes différents : l'anglais a {codesDe(en).join(" ") || "aucun"}, la traduction
      {codesDe(fr).join(" ") || "aucun"}.
    </div>
  {/if}
  <div class="deux">
    <div>
      <div class="ph">Anglais · en jeu</div>
      <div class="mc">{@html rendre(en, dialecte)}</div>
    </div>
    <div>
      <div class="ph">Français · en jeu</div>
      <div class="mc">{@html rendre(fr, dialecte)}</div>
    </div>
  </div>
</div>

<style>
  .peek {
    /* Bloc normal, pas de position absolue : voir la note de correctif ci-dessus.
       display:block par défaut suffit (l'appelant place ce composant en fin de conteneur
       et lui donne, via :global(.peek), le grid-column/margin nécessaires à son contexte). */
    border-radius: 7px; padding: 11px 13px; box-shadow: 0 6px 18px -8px rgba(0, 0, 0, .35);
  }
  .peek.quest { background: #101318; border: 1px solid #2B323B; }
  .peek.patchouli { background: #F3E9D2; border: 1px solid #C6AF83; }
  .deux { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
  .ph {
    font-family: var(--mono); font-size: 8.5px; letter-spacing: .16em; text-transform: uppercase;
    margin-bottom: 5px;
  }
  .quest .ph { color: #5E6B79; }
  .patchouli .ph { color: #9A8155; }
  .mc { font-family: var(--mono); font-size: 13px; line-height: 1.7; word-break: break-word; }
  .quest .mc { color: #E8EDF2; text-shadow: 1.5px 1.5px 0 rgba(0, 0, 0, .55); }
  .patchouli .mc { color: #3B2E1C; }
  .alerte {
    font-size: 11.5px; margin-bottom: 8px; padding: 5px 8px; border-radius: 4px;
    background: rgba(158, 66, 56, .18); color: #FF9E93;
  }
  .patchouli .alerte { background: rgba(158, 66, 56, .12); color: #8B2318; }
  :global(.mc .puce) { display: block; }
  :global(.mc .puce)::before { content: "• "; color: #9A8155; }
  .quest :global(.mc .puce)::before { color: #5E6B79; }
  :global(.mc .piece) {
    display: inline-block; width: 11px; height: 11px; border-radius: 50%;
    background: radial-gradient(circle at 35% 35%, #F4D477, #B8862B); vertical-align: -1px;
    margin-right: 3px; box-shadow: inset 0 0 0 1px rgba(0, 0, 0, .25);
  }
  :global(.mc .lien) { text-decoration: underline; text-underline-offset: 2px; }
  .quest :global(.mc .lien) { color: #7FD9C4; }
  .patchouli :global(.mc .lien) { color: #6B4A1E; }
  /* &k (brouillé) : pas d'équivalent statique fidèle à l'animation en jeu — un indice
     visuel approximatif plutôt que de fuiter le code ou de rendre le texte tel quel. */
  :global(.mc .brouille) { filter: blur(.4px); letter-spacing: .02em; opacity: .82; }
</style>
