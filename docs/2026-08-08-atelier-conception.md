# Atelier — explorateur des traductions de Society: Sunlit Valley

**Date** : 8 août 2026
**Statut** : conception validée par maquettes
**Emplacement du code** : `site/` à la racine du projet

## Objet

Une application web locale pour parcourir, rechercher et corriger les traductions du modpack.
Elle lit les fichiers source à chaque démarrage et se met à jour quand ils changent : ce n'est
pas un export figé. Elle couvre les trois natures de contenu — clés de langue, livre de quêtes,
livres Patchouli — avec un affichage adapté à chacune, et expose pour chaque texte son origine
et l'historique des décisions de traduction.

## Décisions actées

| Décision | Choix |
|---|---|
| Exécution | **Local d'abord** ; conçue pour permettre une publication en lecture seule plus tard |
| Technique | **Node + Vite + Svelte**, API en middleware Vite (une seule commande `npm run dev`) |
| Corrections | **Écriture directe** dans les fichiers source ; git sert d'historique |
| Traçabilité | Origine de l'anglais, chemin exact, décisions issues de `provenance.json`, glossaire appliqué |
| Langues | **Aucune liste figée** : toute locale au format `xx_yy` trouvée dans les fichiers |
| Marquage | File « à revoir » persistée, avec destinataire : moi ou l'IA |

## Sources de données

Le site lit **trois racines**, dont deux hors du repo du pack :

| Racine | Contenu | Rôle |
|---|---|---|
| `society-sunlit-valley/kubejs/assets/*/lang/*.json` | traductions du pack, toutes langues | source principale |
| `society-sunlit-valley/patchouli_books/*/<locale>/**` | livres, un arbre complet par langue | livres |
| `society-sunlit-valley/config/ftbquests/` | `chapter_groups.snbt`, `chapters/*.snbt` | **structure** du livre de quêtes |
| `fr-workspace/extracted/<jar>/<ns>/<locale>.json` | langues officielles des mods | anglais source et langues tierces |
| `fr-workspace/provenance.json` | 2 408 décisions documentées | panneau de traçabilité |
| `fr-workspace/glossaire.json` | 1 698 termes et leur origine | termes appliqués |

**Volumétrie mesurée** : 3 863 fichiers, 47 Mo, **106 locales distinctes**.

## Architecture

Un seul processus en développement : Vite sert l'interface Svelte, un greffon Vite monte l'API
en middleware. Trois modules séparés, testables isolément :

```
site/
├── server/
│   ├── readers/      lecture par type : lang, quest, patchouli, provenance
│   ├── index/        index en mémoire, recherche, filtres
│   └── writer/       application d'une correction, file « à revoir »
└── src/              interface Svelte
```

Les caches sont construits au démarrage et invalidés **par racine surveillée** lors d'un
changement sur disque : chaque racine ne remet à zéro que les caches qu'elle peut réellement
affecter. Toucher un livre Patchouli ne reconstruit donc pas l'index des clés de langue.
Descendre au fichier près a été jugé disproportionné : l'invalidation par racine ramène déjà
le coût d'une écriture de 1,6 s à 0,02 s.

La recherche est serveur : 47 Mo ne peuvent pas être envoyés au navigateur.

### Modèle d'entrée unifié

Les trois natures de contenu partagent une seule structure ; elles ne diffèrent que par la
façon de **lire** et d'**écrire**.

```
{
  id: "lang:brewery:item.brewery.hop_trellis_seed",
  kind: "lang" | "quest" | "patchouli",
  source:      { en: "Hop Trellis Seed" | null, origine: "jar" | "override" | "script" | "aucune" },
  traductions: { fr_fr: "Graines de houblon", ko_kr: "홉 씨앗", … },
  emplacement: { fichier: "kubejs/assets/brewery/lang/fr_fr.json", pointeur: null },
  contexte:    { mod: "brewery", version: "letsdo-brewery-forge-2.0.3" },
  provenance:  [ { type: "sans_source_anglaise", certitude: "incertain", … } ]
}
```

Recherche, filtres, panneau de traçabilité et écriture partagent ce modèle. Seuls les lecteurs
et l'écrivain sont spécifiques : clé plate pour `lang`, clé structurée en chapitre/quête/champ
pour `quest`, pointeur JSON dans un fichier de livre pour `patchouli`.

**État de la première version.** Ce modèle unifié n'est implémenté que pour `lang`. Les quêtes
et les livres sont **lus et parcourus, mais pas cherchables, pas traçables et pas modifiables**
depuis le site. Conséquence à connaître : `provenance.json` porte 121 décisions documentées sur
des textes Patchouli, indexées par pointeur de page, qu'aucun écran ne sait montrer aujourd'hui.
Les textes de quêtes s'en tirent indirectement — ils vivent dans des fichiers de langue, donc la
vue Clés les atteint — mais rien dans la vue Quêtes n'y mène. Étendre les trois capacités aux
deux autres natures est le chantier suivant identifié.

### Lecture des fichiers de langue

L'analyseur doit **tolérer les commentaires** `//`, que Minecraft accepte dans les fichiers
lang. Un analyseur JSON strict masque des mods entiers en silence : le défaut a réellement
caché `vintagedelight` (190 clés) et `shouldersurfing` pendant tout le projet de traduction.
Tout fichier illisible malgré cette tolérance doit être **signalé**, jamais ignoré.

## Les trois vues

### Clés de langue

Table dense, **paginée** par tranches de 200 : la pagination résout le coût de rendu que la
virtualisation visait, pour une fraction du travail, et le parcours réel passe par la recherche
et les filtres bien plus que par le défilement de 59 941 lignes. L'affichage dit toujours où
l'on est dans le total — une table qui annonce 59 941 clés et n'en montre que 200 sans le dire
serait le genre de mensonge d'interface que cet outil existe pour débusquer.

**Trois colonnes par défaut** — clé, anglais, français — et un sélecteur « + langue » qui ajoute
dynamiquement les colonnes voulues. Une pastille de couleur encode l'origine de l'anglais.

Le groupement par mod repliable, avec la version du JAR en tête de groupe, n'est pas livré dans
cette version : la version du JAR reste visible dans le panneau de traçabilité, et le filtre par
namespace joue le même rôle.

### Quêtes

La structure ne se trouve pas dans les fichiers de langue : elle se reconstitue en croisant
`chapter_groups.snbt` (groupes et leur ordre), chaque `chapters/*.snbt` (groupe d'appartenance,
`order_index`, icône) et le fichier de langue pour les titres, reliés par le **nom de fichier**
du chapitre (`ftbquests.chapter.<fichier>.title`).

Arborescence à trois niveaux — groupe › chapitre › quête — conforme au jeu : Bienvenue hors
groupe, puis Tutoriel, Centre communautaire, Guides, Collection. **4 groupes, 29 chapitres,
1 556 quêtes dont 528 traduisibles, 1 659 clés.**

Une quête n'entre dans l'outil que si elle porte au moins un champ traduisible : les autres
tirent leur nom de leur tâche et n'ont rien à relire. L'en-tête de chapitre affiche les deux
nombres, pour que l'écart avec le livre en jeu reste visible.

Lecture bilingue en regard : titre, paragraphes numérotés, objectifs. Une quête portant
`hide_until_deps_complete: true` est **affichée mais signalée « masquée en jeu »** avec ses
prérequis — 47 quêtes sont dans ce cas, dont 39 des 43 du chapitre II. Un filtre permet de
n'afficher que les quêtes visibles.

### Livres Patchouli

Chaque langue possède un arbre de fichiers complet. L'entrée s'affiche page par page, bilingue,
avec le type de chaque page.

La traduisibilité d'une page se détermine par **la présence d'un champ de texte, jamais par son
type**. Recensement des fichiers réels : les 524 pages des deux livres portent du texte —
`text` et `title` sur les 261 pages `patchouli:text`, `text` et `name` sur les 153 pages
`patchouli:entity`, et `name ` — avec une espace finale — sur les 110 pages
`patchouli:multiblock`. Trois pages en portent deux à la fois.

Les arbres de langue ne se superposent pas non plus : l'anglais, le français et le chinois
coïncident, le coréen diverge en 40 endroits. Le lecteur lit donc les noms de champs dans le
fichier qu'il ouvre, et calcule le pointeur d'écriture par langue.

**2 livres, 7 catégories, 524 pages, 4 langues** (anglais, français, coréen, chinois).

## Recherche et filtres

**Recherche** sur la clé, le texte anglais, la traduction française, ou toutes langues à la fois.

**Filtre par langues** — construit comme une phrase, `Avec ⟨langues⟩ · Sans ⟨langues⟩`, chaque
clause acceptant plusieurs langues en « ou ». Une portée obligatoire accompagne le filtre :
*le pack seul* — parmi ce que nous maintenons — ou *le pack et les mods*, dans tout le jeu.
Cette distinction n'est pas cosmétique : sur « avec espagnol, sans français », elle sépare
**4 lacunes réelles** de 738 résultats à l'échelle du jeu entier ; sur « avec coréen », 7 452
contre 765. Le sens de l'écart dépend de la langue demandée, la portée élargissant la clause
*avec* en même temps qu'elle durcit la clause *sans*.

Ce filtre a valeur de détecteur : il a mis au jour 4 clés du namespace `society` que
l'espagnol, le coréen et le portugais possèdent sans que le français les ait.

**Filtres complémentaires** et **filtres enregistrés** ne sont pas livrés dans cette version.
Le filtre par origine de l'anglais existe côté serveur mais n'a pas d'interface ; il faudrait
d'ailleurs le manier avec prudence, la valeur `aucune` couvrant 11 412 clés dont l'immense
majorité est du bruit de mods mal synchronisés — le même piège que le couple 1 984/56 ci-dessus.

## Codes de formatage

Le texte s'affiche **brut**, codes visibles en pastilles discrètes : c'est ce qu'on relit.
Au **survol d'un paragraphe**, un aperçu montre le rendu tel qu'en jeu, dans les deux langues
côte à côte — fond sombre pour les quêtes, parchemin pour Patchouli. Les codes disparaissent,
les couleurs et la mise en forme apparaissent.

Le site **compare les codes** entre l'anglais et la traduction et signale les écarts : un `&o`
italique rendu par un `&3` cyan est une erreur invisible en lecture brute. La validation
mécanique existante vérifie la présence des codes, pas leur identité — c'est un complément.

## Traçabilité

Le panneau latéral montre, pour l'entrée sélectionnée :

- **Les langues disponibles**, empilées derrière un filet, l'anglais source en tête. Une langue
  dont la valeur est identique à l'anglais est signalée « non traduit » plutôt qu'affichée comme
  une traduction — cas réel de l'allemand sur les quêtes.
- **L'origine** : mod et version du JAR, fichier cible, script créateur le cas échéant.
- **Les décisions** issues de `provenance.json` : arbitrages, corrections de relecture avec leur
  motif, verdicts de vérification adverse, en ordre chronologique.
- **Les termes de glossaire** appliqués, avec leur source d'autorité.

## Corrections et file « à revoir »

**Correction directe** : le champ de traduction est éditable dans le panneau ; l'enregistrement
écrit dans le fichier source. La validation mécanique (`validate_translation.py`) est appliquée
avant écriture : codes préservés, politique d'accents respectée. Un refus explique ce qui bloque.

Le fichier est réécrit **trié alphabétiquement et indenté à deux espaces** — la convention des
258 fichiers français du pack, tous déjà dans cette forme, si bien qu'une correction produit un
diff d'exactement une ligne. Le fichier est en revanche refusé si sa lecture n'a réussi qu'en
tolérant des commentaires : `JSON.stringify` les effacerait, et ce projet ne détruit pas en
silence ce qu'il ne sait pas reproduire.

**File « à revoir »** : un marquage pose une entrée dans `fr-workspace/a-revoir.json` — clé,
note libre, destinataire (`utilisateur` ou `ia`), date. Le destinataire est ce qui rend la file
utile : les cas adressés à l'IA peuvent être repris en lot avec leur contexte. La file est
consultable comme une vue à part entière.

## Hors périmètre

- **Publication en ligne** : l'architecture la permet (figer les réponses de l'API en fichiers
  statiques), mais elle n'est pas construite maintenant.
- **Rendu des icônes d'objets** : les identifiants (`society:prismatic_shard`) sont affichés en
  texte ; extraire les textures des JARs est un chantier distinct.
- **Édition des fichiers de quêtes `.snbt`** : le site lit la structure, il ne la modifie pas.
- **Traduction automatique** depuis le site : les corrections sont écrites à la main ; le
  traitement en lot passe par la file « à revoir » et le pipeline existant.

## Critères de réussite

1. Une modification d'un fichier source apparaît dans l'interface sans redémarrage — pour les
   cinq sources. L'interface ne s'interroge cependant pas d'elle-même : hors de la vue Clés,
   qui rappelle le serveur à chaque frappe, il faut recharger la page pour voir le changement.
2. Les trois natures de contenu sont parcourables, chacune avec son affichage propre. Seules
   les clés de langue sont aussi cherchables, traçables et modifiables (voir « Modèle d'entrée
   unifié »).
3. Le filtre « Avec ⟨langues⟩ · Sans ⟨langues⟩ » sépare les lacunes réelles du bruit : sur
   « avec espagnol, sans français », 4 clés à l'échelle du pack contre 738 à celle du jeu.
4. Une correction écrite depuis le site est valide pour `validate_translation.py`.
5. L'arborescence des quêtes correspond à celle du livre en jeu, quêtes masquées signalées.
6. Aucune liste de langues n'est codée en dur : une locale ajoutée apparaît seule.
