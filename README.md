# Society: Sunlit Valley — Traduction Francaise

[![Licence: CC BY-NC-SA 4.0](https://img.shields.io/badge/Licence-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
[![PRs Welcome](https://img.shields.io/badge/PRs-bienvenues-brightgreen.svg)](CONTRIBUTING.md)

Traduction communautaire francaise du modpack Minecraft [Society: Sunlit Valley](https://github.com/Chakyl/society-sunlit-valley).

## Installation

1. Telecharger le ZIP depuis les [Releases](../../releases) (TODO pas encore fait)
2. Extraire le contenu directement dans le dossier de votre instance Minecraft
3. Les fichiers se placent automatiquement aux bons emplacements

## Contenu traduit

| Categorie | Chemin | Description |
|-----------|--------|-------------|
| Mods & modpack | `kubejs/assets/*/lang/fr_fr.json` | Items, blocs, interfaces et infobulles (259 fichiers) |
| Quetes | `kubejs/assets/ftbquestlocalizer/lang/fr_fr.json` | Livre de quetes complet (1 659 entrees) |
| Dialog NPC | `kubejs/assets/dialog/lang/fr_fr.json` | Dialogues de tous les PNJ (1 542 repliques) |
| Almanac | `patchouli_books/almanac/fr_fr/` | Guide en jeu sur les cultures et animaux |
| Fish Finder | `patchouli_books/fish_finder/fr_fr/` | Guide de peche |
| Journal des modifications | `config/fancymenu/assets/changelog_fr_fr.markdown` | Journal affiche sur l'ecran titre (132 puces, depuis 4.1.2) |

32 065 entrees traduites au total.

## Documentation et outillage

| Chemin | Contenu |
|--------|---------|
| `outillage/STYLE.md` | Guide de style : registre, capitalisation, politique d'accents, conventions de nommage |
| `outillage/GLOSSAIRE.md` | Glossaire (1 678 termes) classe par origine : vanilla Mojang, traductions officielles des mods, terminologie Stardew Valley |
| `outillage/KEEP-ENGLISH.md` | Termes volontairement laisses en anglais, avec justification et emplacements |
| `outillage/provenance.json` | Tracabilite de 2 432 cles et 2 552 decisions : arbitrages, corrections de relecture et leurs motifs |
| `outillage/scripts/` | Pipeline complet : inventaire, validation mecanique, reconciliation, generation du pack |
| `docs/` | Specification, plan de travail et rapport final |

Le pipeline est relancable a chaque mise a jour du modpack : il detecte les cles nouvelles
ou modifiees et ne retraduit que le delta. Voir `docs/RAPPORT-TRADUCTION-FR.md`.

## Verifier la traduction

`outillage/scripts/verifier.py` relit tout le francais du pack et fait foi avant chaque
publication. Il enchaine seize controles (couverture, codes de formatage, accents,
terminologie, casse, familles de noms, largeur d'affichage, decisions tracees dans
`provenance.json`...). Ses donnees sont dans `outillage/coherence/` (voir son `LISEZMOI.md`) :
un ecart volontaire s'y inscrit comme exception motivee, et la dette connue
(`dette.json`) ne peut que decroitre — un nouvel ecart non motive bloque.

```sh
python3 outillage/scripts/verifier.py --instantane outillage/instantane/$(cat outillage/version-du-pack.txt).json.gz
```

L'instantane de la version visee (`outillage/instantane/`) remplace les jars et les scripts
du pack : la commande tourne sur ce depot seul. Chaque Pull Request la passe en integration
continue (`.github/workflows/verifier.yml`), avec les tests de l'outillage ; la verification
echoue si le verdict n'est pas `OK`.

## Contribuer

Les contributions sont les bienvenues ! Consultez le [guide de contribution](CONTRIBUTING.md) pour savoir comment participer.

**En bref :**
1. Demandez l'acces collaborateur (via les [Discussions](../../discussions))
2. Clonez le repo et creez une branche
3. Ouvrez une Pull Request

Vous pouvez aussi [signaler une erreur](../../issues/new?template=erreur-traduction.yml) ou [demander une traduction manquante](../../issues/new?template=traduction-manquante.yml).

## Version

A jour pour Society: Sunlit Valley **v4.1.5**.

## Accents

**Tout est accentue**, noms d'objets et de blocs compris : « Cle rouge » s'ecrit
« Cle rouge » avec son accent. Ce n'etait pas le cas jusqu'a la 4.1.5 — les noms
s'ecrivaient sans accents, parce que les barres de recherche du jeu comparent les
chaines sans normaliser les diacritiques et que taper « ble » ne trouvait alors pas
« Ble » accentue.

La recherche en jeu fonctionne toujours, mais a la lettre : il faut taper le nom avec
ses accents. Le mod [Accent Fold](https://github.com/Tomsauy/accent-fold), **facultatif**,
leve cette contrainte dans les neuf ecrans de recherche du pack — inventaire creatif,
EMI, JEI, Refined Storage, Quark, Create, Sophisticated, FTB Library, Patchouli et
l'index corporea de Botania.

Les alias de recherche EMI, qui palliaient partiellement le probleme, ont ete retires :
ils ne couvraient qu'un ecran sur neuf. Voir `outillage/DECISION-ACCENTS.md`.

## Licence

Ce projet est distribue sous licence [CC BY-NC-SA 4.0](LICENSE).
