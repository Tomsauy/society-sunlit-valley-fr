# Atelier

L'Atelier est une application web locale pour parcourir, chercher et corriger les
traductions françaises du modpack Minecraft *Society: Sunlit Valley*. Elle lit les
fichiers source (clés de langue, quêtes FTB Quests, livres Patchouli) à chaque
démarrage et se met à jour quand ils changent sur disque — ce n'est pas un export
figé. Les corrections faites depuis le site s'écrivent directement dans les fichiers
source ; git sert d'historique.

## Disposition de dossiers attendue

Par défaut, l'Atelier suppose que ce dossier `site/` est un sous-dossier d'un dépôt
plus large qui contient aussi le modpack et l'espace de travail de traduction, à côté :

```
SunlitValley/                          (ROOT)
├── site/                              ce dossier — l'Atelier lui-même
├── society-sunlit-valley/             (PACK) le modpack
│   ├── kubejs/assets/*/lang/*.json    traductions du pack, toutes langues
│   ├── patchouli_books/               les livres en jeu
│   └── config/ftbquests/quests/       (QUESTS_CONFIG) structure du livre de quêtes
└── fr-workspace/                      (WORKSPACE) espace de travail de traduction
    ├── provenance.json                décisions de traduction documentées
    ├── a-revoir.json                  file « à revoir »
    └── extracted/<jar>/<ns>/*.json    (EXTRACTED) langues extraites des JARs des mods
```

Cette disposition — celle du disque de son auteur — reste le comportement par défaut,
sans rien à configurer.

## Changer les chemins

Les quatre racines réelles ci-dessus (`PACK`, `WORKSPACE`, `EXTRACTED`,
`QUESTS_CONFIG`, définies dans `server/paths.js`) sont réglables individuellement par
variable d'environnement, pour un autre disque ou un dépôt qui ne partage pas cette
disposition :

| Variable | Par défaut | Fixe |
|---|---|---|
| `ATELIER_PACK` | `../society-sunlit-valley` | le modpack |
| `ATELIER_WORKSPACE` | `../fr-workspace` | l'espace de travail |
| `ATELIER_EXTRACTED` | `<WORKSPACE>/extracted` | les langues extraites des mods |
| `ATELIER_QUESTS_CONFIG` | `<PACK>/config/ftbquests/quests` | la config des quêtes |

`EXTRACTED` et `QUESTS_CONFIG` dérivent par défaut de `WORKSPACE`/`PACK` — c'est la
disposition habituelle — mais chacun peut être fixé à part : rien n'empêche de garder
les langues extraites ailleurs que dans `fr-workspace/`, par exemple.

Une valeur relative (`ATELIER_PACK=../un-autre-dossier`) se résout par rapport à la
racine du dépôt (`site/..`), pas par rapport au dossier courant du terminal — le
résultat ne dépend donc pas de l'endroit d'où `npm run dev` est lancé. Une valeur
absolue est prise telle quelle.

Exemple, pour lancer l'Atelier avec un pack ailleurs sur le disque :

```sh
ATELIER_PACK=/chemin/vers/un/autre/pack npm run dev
```

## Lancer l'Atelier

```sh
npm install
npm run dev
```

Le serveur (API + interface) écoute sur <http://localhost:5180>. Une seule commande :
pas de build séparé, pas de second process pour l'API.

Autres commandes utiles :

```sh
npx vitest run   # ou : npm test — 147 tests, quelques secondes
npm run build    # build de production (site/dist/) — non requis pour l'usage local
```

### Depuis le dépôt du pack

L'Atelier est aussi publié à l'intérieur du dépôt de traduction, dans `atelier/`, à côté
du pack et de son `outillage/`. La disposition n'y est pas la même — le pack **est** la
racine du dépôt, et l'espace de travail s'appelle `outillage/` — d'où une commande dédiée :

```sh
npm run dev:integre
```

Elle ne fait que fixer `ATELIER_PACK` et `ATELIER_WORKSPACE` avant de lancer le serveur.
Deux sources manquent dans ce dépôt et y manqueront toujours : `config/ftbquests/`, absent
du miroir, et les langues extraites des mods, 47 Mo que git ne suit pas. L'Atelier démarre
quand même et le dit à l'écran — voir la section suivante. Pour retrouver la vue Quêtes et
l'anglais source des mods, il faut un environnement complet : le pack entier et un dossier
de langues extraites, désignés par les deux variables.

## Quand une source manque

Aucune des quatre racines n'est requise pour démarrer : l'Atelier lit ce qui est là et
signale le reste, plutôt que de refuser de démarrer.

| Racine absente | Ce qui se dégrade |
|---|---|
| `PACK` (ou son sous-dossier `kubejs/assets`) | vue **Clés** réduite à ce que les mods fournissent (anglais brut, sans le français ni les overrides du pack) ; vues **Quêtes** et **Livres** vides, `patchouli_books/` et les titres de quêtes vivant eux aussi sous `PACK` |
| `EXTRACTED` | vue **Clés** réduite à ce que le pack fournit seul (sans l'anglais ni les autres langues des mods) |
| `QUESTS_CONFIG` | vue **Quêtes** vide |
| `WORKSPACE` | traçabilité, glossaire et file **À revoir** vides (dégradait déjà proprement avant cette tâche) |

Dans tous les cas, `/api/sante` répond 200 (jamais 500 pour cette seule raison). Son
champ `manquantes` nomme les racines absentes parmi `PACK`/`EXTRACTED`/`QUESTS_CONFIG`
ainsi que la variable d'environnement pour les fixer ; le même message apparaît dans la
console du serveur et dans un bandeau en haut de l'interface. C'est distinct d'un
fichier *illisible* (présent mais corrompu), signalé séparément dans `illisibles` au
même endroit. `WORKSPACE` et `patchouli_books/` dégradent silencieusement (pas
d'entrée dans `manquantes`) : ils l'ont toujours fait sans planter, avant même cette
tâche.
