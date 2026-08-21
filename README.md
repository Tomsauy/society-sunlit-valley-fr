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
| Mods & modpack | `kubejs/assets/*/lang/fr_fr.json` | Items, blocs, interfaces et infobulles (258 fichiers, 238 mods) |
| Quetes | `kubejs/assets/ftbquestlocalizer/lang/fr_fr.json` | Livre de quetes complet (1 659 entrees) |
| Dialog NPC | `kubejs/assets/dialog/lang/fr_fr.json` | Dialogues de tous les PNJ (1 475 repliques) |
| Almanac | `patchouli_books/almanac/fr_fr/` | Guide en jeu sur les cultures et animaux |
| Fish Finder | `patchouli_books/fish_finder/fr_fr/` | Guide de peche |
| Journal des modifications | `config/fancymenu/assets/changelog_fr_fr.markdown` | Journal affiche sur l'ecran titre (nouveau en 4.1.2) |

Plus de 31 500 entrees traduites au total.

## Documentation et outillage

| Chemin | Contenu |
|--------|---------|
| `outillage/STYLE.md` | Guide de style : registre, capitalisation, politique d'accents, conventions de nommage |
| `outillage/GLOSSAIRE.md` | Glossaire (1 698 termes) classe par origine : vanilla Mojang, traductions officielles des mods, terminologie Stardew Valley |
| `outillage/KEEP-ENGLISH.md` | Termes volontairement laisses en anglais, avec justification et emplacements |
| `outillage/provenance.json` | Tracabilite de 2 408 decisions : arbitrages, corrections de relecture et leurs motifs |
| `outillage/scripts/` | Pipeline complet : inventaire, validation mecanique, reconciliation, generation du pack |
| `docs/` | Specification, plan de travail et rapport final |

Le pipeline est relancable a chaque mise a jour du modpack : il detecte les cles nouvelles
ou modifiees et ne retraduit que le delta. Voir `docs/RAPPORT-TRADUCTION-FR.md`.

## Contribuer

Les contributions sont les bienvenues ! Consultez le [guide de contribution](CONTRIBUTING.md) pour savoir comment participer.

**En bref :**
1. Demandez l'acces collaborateur (via les [Discussions](../../discussions))
2. Clonez le repo et creez une branche
3. Ouvrez une Pull Request

Vous pouvez aussi [signaler une erreur](../../issues/new?template=erreur-traduction.yml) ou [demander une traduction manquante](../../issues/new?template=traduction-manquante.yml).

## Version

A jour pour Society: Sunlit Valley **v4.1.2**.

Les noms d'objets, de blocs et de creatures sont volontairement ecrits **sans accents** :
la recherche d'EMI compare les chaines sans normaliser les diacritiques, donc taper
« ble » doit pouvoir trouver « Ble ». Tout le reste — quetes, dialogues, descriptions,
livres — est accentue normalement. Voir `outillage/DECISION-ACCENTS.md`.

## Licence

Ce projet est distribue sous licence [CC BY-NC-SA 4.0](LICENSE).
