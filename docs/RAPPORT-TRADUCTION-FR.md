# Traduction française de Society: Sunlit Valley — Rapport final

**Date** : 4 août 2026
**Branche** : `traduction-fr` (dans `society-sunlit-valley/`), 15 commits
**Version du pack** : 4.1.1 — Minecraft 1.20.1 / Forge 47.4.0 / 366 mods

## Vue d'ensemble

| Indicateur | Valeur |
|---|---|
| Clés traduites | **31 565** |
| Unités de traduction | 573 |
| Fichiers `fr_fr.json` produits (kubejs) | 258 |
| Fichiers de livres Patchouli produits | 267 |
| Entrées de glossaire | 1 697 |
| Corrections de relecture appliquées | 1 436 |
| Divergences terminologiques résolues | 574 unifications |
| Erreurs mécaniques résiduelles | **0** |

## Ce qui est traduit

| Contenu | Clés | Modèle |
|---|---|---|
| Items et blocs Society | 2 017 | Fable 5 |
| Overrides du pack (66 mods renommés) | 3 118 | Fable 5 |
| Quêtes FTB | 1 659 | Fable 5 |
| Livres Patchouli (almanach, guide de pêche) | 801 champs | Fable 5 |
| Mods sans traduction FR (175 mods) | 18 417 | Opus 5 |
| Compléments de mods partiellement traduits (63 mods) | 5 553 | Opus 5 |

La relecture qualité finale a été faite par Fable 5 (cœur narratif et 24 lots de mods) puis
Opus 5 (10 lots restants), soit 1 436 corrections appliquées sur l'ensemble.

## Ce qui n'est pas traduit, et pourquoi

- **27 mods déjà 100 % traduits en français dans leur JAR** (Create, Farmer's Delight,
  Aquaculture, Autumnity, Bountiful…) : conservés tels quels, conformément à la décision de
  départ. Leur vocabulaire a servi de référence au glossaire (481 entrées en proviennent).
- **63 termes volontairement gardés en anglais** : titres d'œuvres d'art des mods de peintures,
  noms propres (artistes, personnages, marques : Create, CurseForge, Modrinth, Discord),
  créatures à jeu de mots intraduisible (Chapple, Wraptor, Sneep Snorp), noms officiels FR
  inchangés (Creeper, Enderman, Phantom, Allay, Mooshroom). Détail complet dans
  `fr-workspace/KEEP-ENGLISH.md`.
- **600 valeurs identiques EN/FR légitimes** (mots identiques dans les deux langues, noms
  d'espèces, onomatopées, identifiants techniques) : recensées dans `fr-workspace/invariants.json`
  après arbitrage explicite, jamais par défaut.
- **Chaînes codées en dur dans le code Java des mods** : intraduisibles sans modifier les JARs.
  Non recensées exhaustivement (elles ne sont pas détectables sans décompilation systématique).
- **Textes incrustés dans des textures** (images de menus, illustrations) : hors périmètre.
  Aucun inventaire exhaustif n'a été produit — c'est une limite assumée de ce travail, à traiter
  dans un futur chantier si besoin.
- **42 chaînes en dur des scripts KubeJS du pack** : analysées ; 33 étaient en réalité déjà
  couvertes par une clé de lang, les 9 restantes correspondaient à des `displayName` que
  l'extraction avait mal reconstitués (templates de forge, cristaux de regret, bières) — corrigées
  directement dans le fichier de langue. Aucune conversion de script n'a été nécessaire.

## Décisions terminologiques structurantes

**Politique accents (hybride).** Le code de recherche d'EMI (`emi-1.1.24+1.20.1+forge.jar`) ne
contient aucune normalisation Unicode : taper « ble » ne trouve pas « Blé ». Les **noms d'items,
blocs et entités** (clés à 3 segments `item.*`, `block.*`, `entity.*` dont la valeur est un libellé
court) sont donc écrits **sans accents** pour que la recherche fonctionne. Tout le reste — quêtes,
dialogues, tooltips, descriptions, livres, interface — est en **français correctement accentué**.

**Sources du glossaire, par ordre d'autorité** :

| Origine | Entrées | Rôle |
|---|---|---|
| Mods déjà traduits (fr_fr des JARs) | 481 | vocabulaire établi de chaque mod |
| Vanilla Minecraft (officiel Mojang 1.20.1) | 321 | matériaux, outils, créatures, couleurs |
| Stardew Valley (wiki officiel FR) | 66 | concepts hérités du genre |
| Arbitrage de traduction | 822 | items du pack sans référence officielle |

Exemples de choix issus de Stardew Valley FR : *Shipping Bin* → « Bac d'expédition »,
*Keg* → « Tonneau », *Preserves Jar* → « Bocal », *Prismatic Shard* → « Tesson prismatique »,
*Scarecrow* → « Épouvantail », *Sprinkler* → « Arroseur ». *Fertilizer* → « Engrais » sur
arbitrage de l'utilisateur (contre « Fertilisant » hérité d'un mod).

**Conventions de nommage des créatures** : trait d'union pour les noms composés d'espèces
(« Poisson-obsidienne », « Poisson-os »), préposition « de » pour la provenance
(« Poisson de cirque »), conformément à l'usage français (poisson-chat, poisson-globe).

## Cohérence : « une chaîne anglaise = une traduction française »

Un index global de toutes les paires EN→FR du corpus (fichiers produits **et** traductions
officielles des JARs telles que le joueur les voit en jeu, overrides appliqués) a révélé
**682 divergences**. Après arbitrage :

- **574 unifications** — une traduction canonique imposée partout (« Music Disc » → « Disque »,
  « Save » → « Sauvegarder », « Off » → « Désactivé »…).
- **108 distinctions conservées** — variantes légitimes selon le contexte : accords grammaticaux
  (Aucun/Aucune selon le nom qualifié), polysémie réelle (« Back » = « Retour » sur un bouton,
  « Dos » en anatomie).

Les divergences venant d'un JAR sont corrigées par une clé d'override ciblée dans
`kubejs/assets/<mod>/lang/fr_fr.json` : **aucun JAR de mod n'a été modifié**.

## Garanties de qualité

Un validateur mécanique (développé en TDD, 19 tests) vérifie sur l'ensemble du corpus :
ensemble de clés strictement identique à la source anglaise, préservation exacte des
placeholders (`%s`, `%1$s`, `§x`, `$(...)`, `\n`, `{0}`), absence de valeur vide, respect de la
politique accents, et détection des valeurs restées en anglais. **Résultat final : 0 erreur.**

Chaque valeur identique à l'anglais a été soumise à un agent arbitre avant d'être tolérée :
631 cas examinés sur la vague mods, dont 12 vraies traductions manquantes rattrapées
(« Booze » → « Bibine », « Minimap » → « Minicarte », « Jukebox » → « Juke-box »,
« Boombox » → « Radiocassette », « Skin » → « Apparence »…).

## Livrables

- **Traductions en place** : `kubejs/assets/*/lang/fr_fr.json` (258 fichiers) et
  `patchouli_books/{almanac,fish_finder}/fr_fr/` (267 fichiers), chargés automatiquement par le jeu.
- **Resource pack** : `resourcepacks/Society_FR.zip` (258 fichiers lang, `pack_format` 15) —
  pour une autre instance du pack. Ne contient pas les livres Patchouli, qui se chargent depuis
  le dossier `patchouli_books/`.
- **Outillage** : `fr-workspace/scripts/` (téléchargement des JARs, extraction, inventaire,
  validateur, lots, réconciliation, build du zip, suivi des workflows).

## Comment tester en jeu

Lancer le jeu sur cette instance, puis Options → Langue → **Français (France)**.
Points de contrôle suggérés :

1. Items Society dans l'inventaire (gemmes « immacule », « Bac d'expedition »)
2. Recherche EMI : taper « ble » doit trouver les items concernés (politique sans accents)
3. Livre de quêtes FTB : chapitres, descriptions tutoyées
4. Dialogues de PNJ (le banquier, la sorcière)
5. Almanach Patchouli : entrée « Aubergine 🍂 », guide de pêche
6. Écrans de mods tiers (Sophisticated Backpacks, Supplementaries, Functional Storage)

## Maintenance lors des mises à jour du pack

Le pipeline est relançable et ne retraduit que le delta :

```bash
cd /Users/thomas/IAPersoProjects/SunlitValley
python3 fr-workspace/scripts/download_jars.py      # nouveaux JARs (cache sha1)
python3 fr-workspace/scripts/extract_langs.py      # ré-extraction
python3 fr-workspace/scripts/build_inventory.py    # détecte les clés nouvelles/modifiées
python3 fr-workspace/scripts/make_batches.py --kinds mod,override,society,quests,patchouli
```

Les lots générés ne contiennent que ce qui manque ; le glossaire, les invariants et le guide de
style sont conservés dans `fr-workspace/`. Après traduction : `apply_translations.py`,
`reconcile.py`, puis `build_fr_resourcepack.py`.

## Statut vis-à-vis du dépôt d'origine

Ce travail est **à usage personnel**. Le projet Society: Sunlit Valley refuse explicitement les
traductions générées par IA (`TRANSLATIONS.md`, `README.md`) : aucune contribution n'a été
soumise en amont et aucune ne doit l'être en l'état.
