# Traduction française intégrale de Society: Sunlit Valley — Design

**Date** : 2026-07-31
**Statut** : validé par l'utilisateur (sections 1 à 5)
**Branche de travail** : `traduction-fr` (dans `society-sunlit-valley/`)

**Organisation des fichiers** : la racine du projet est `/Users/thomas/IAPersoProjects/SunlitValley/`. Le dossier `society-sunlit-valley/` est un clone du dépôt upstream : seuls les fichiers fonctionnels y entrent (les `fr_fr.json` chargés par le jeu, le zip du resource pack). Tout le reste — specs, scripts du pipeline, fichiers de travail, rapports — vit à la racine du projet, hors du repo :

```
SunlitValley/
├── docs/specs/                  ← ce document, rapport final
├── fr-workspace/                ← JARs téléchargés, extractions, inventaire, glossaire, index
│   └── scripts/                 ← scripts du pipeline (inventaire, vérification, build du zip)
└── society-sunlit-valley/       ← repo du pack (branche traduction-fr)
    ├── kubejs/assets/*/lang/fr_fr.json   ← les traductions (fonctionnel)
    ├── patchouli_books/*/fr_fr/          ← livres-guides traduits (fonctionnel)
    └── resourcepacks/Society_FR.zip      ← zip généré (fonctionnel)
```

## Contexte

Society: Sunlit Valley est un modpack Minecraft 1.20.1 (Forge 47.4.0, 366 mods gérés par pakku) de type ferme/commerce inspiré de Stardew Valley. L'objectif est une traduction française **fidèle, intégrale et cohérente** de tout le texte visible en jeu, réalisée de manière autonome par Claude via des workflows multi-agents.

### État des lieux constaté

- Une traduction FR communautaire existe dans le repo (items Society, quêtes 100 %, 66 overrides kubejs) mais l'utilisateur la juge insuffisante : **elle est intégralement refaite et ne sert pas de référence**.
- ~117 dossiers `kubejs/assets/MODID/lang/ko_kr.json` prouvent le mécanisme d'override : KubeJS charge `kubejs/assets/` comme resource pack, un `fr_fr.json` y traduit un mod sans toucher à son JAR.
- Les JARs des mods ne sont pas dans le repo (`mods/` gitignoré) ; les URLs de téléchargement sont dans `pakku-lock.json`.
- Le dépôt upstream **refuse les traductions générées par IA** (`TRANSLATIONS.md`, `README.md`).

## Décisions actées

| Décision | Choix |
|---|---|
| Destination | **Usage personnel uniquement** — aucune PR upstream (politique anti-IA du projet respectée) |
| Périmètre mods | **Tout texte visible en jeu** : chaque mod ayant un `en_us.json` et pas de FR complet |
| Traduction FR du modpack (Society, quêtes, 66 overrides, livres Patchouli) | **Intégralement refaite depuis l'anglais** — l'existante est ignorée comme référence |
| Autres langues du pack (ko/zh/pt/th) | **Témoins d'interprétation** : alimentent la liste des termes gardés en anglais et servent de garde-fou contre les contresens sur les chaînes ambiguës |
| FR officiels embarqués dans les JARs | **Conservés** (jugés bons) — pas de retraduction, mais passe de cohérence avec overrides ciblés en cas de divergence terminologique |
| Livrable | **Les deux** : overrides `kubejs/assets/MODID/lang/fr_fr.json` sur branche git + script générant un resource pack zip partageable |
| Contrôle humain | **Un checkpoint** : validation du glossaire maître et du guide de style avant la traduction de masse |
| Pipeline | **Approche C hybride** : traduction par mod avec contexte + réconciliation mécanique finale des chaînes identiques |
| Accents | Vérification du comportement d'EMI en Phase 1 ; si sensible aux accents → **politique hybride** (noms d'items/blocs sans accents, français accentué partout ailleurs) |

## Architecture — 5 phases

```
Phase 1 : Inventaire            (scripts Python déterministes)
Phase 2 : Glossaire + style     (workflow) → ✋ CHECKPOINT UTILISATEUR
Phase 3 : Traduction de masse   (workflows par lots de mods)
Phase 4 : Vérification + réconciliation (scripts + agents)
Phase 5 : Livrables             (fichiers kubejs + resource pack + rapport)
```

Les traductions produites vivent sur la branche `traduction-fr` du repo, commits par phase. Les fichiers de travail (JARs, extractions, index, glossaire) vont dans `fr-workspace/` à la racine du projet, hors du repo.

### Phase 1 — Inventaire (déterministe, sans agents)

1. Parser `pakku-lock.json` → URLs des 366 JARs ; téléchargement en cache dans `fr-workspace/jars/` à la racine du projet (relançable, reprend où il s'est arrêté).
2. Extraire de chaque JAR tous les `assets/*/lang/en_us.json` et `fr_fr.json` (un mod peut avoir plusieurs namespaces).
3. Recenser les sources du pack : `kubejs/assets/society/lang/en_us_template.json` (~1070 clés), `kubejs/assets/ftbquestlocalizer/lang/en_us.json` (~1659 clés), tous les `kubejs/assets/*/lang/en_us.json` (overrides), et les livres Patchouli `patchouli_books/{almanac,fish_finder}/en_us/` (267 fichiers, ~336 Ko dont une large part de structure non traduisible).
4. Produire `fr-workspace/inventaire.json` : par mod → clés EN, FR du JAR (complet/partiel/absent), overrides du pack, nombre de clés à traduire.
5. **Vérification EMI** : inspecter le code de recherche du JAR EMI de la version du pack (normalisation Unicode/NFKD ou non) → détermine la politique accents.
6. **Scan des chaînes en dur du pack** : repérer le texte anglais littéral dans les scripts KubeJS (`client_scripts`, `server_scripts`, `startup_scripts`), les layouts FancyMenu et les fichiers Dialog → liste des candidats à la conversion opportuniste en clés de lang (voir Limites).

Règles de périmètre :
- Mod avec FR complet dans le JAR → **rien à traduire** ; son vocabulaire alimente le glossaire.
- Mod avec FR partiel dans le JAR → **delta uniquement**, aligné sur le style existant du JAR.
- Toute clé présente dans un override EN du pack (`kubejs/assets/MODID/lang/en_us.json`) → **toujours retraduite** depuis l'override (le pack renomme des items ; le FR du JAR traduit l'ancien nom).
- Mods sans texte visible (libs, API) → exclus naturellement (pas de `en_us.json` ou clés purement techniques).

### Phase 2 — Glossaire maître + guide de style (workflow) → CHECKPOINT

Sources par ordre de priorité :
1. **FR officiels des JARs** — vocabulaire établi des mods traduits (Create, Farmer's Delight…), autorité pour leurs termes.
2. **Minecraft vanilla FR officiel** — téléchargé depuis les assets Mojang (version 1.20.1) : matériaux, outils, couleurs, mécaniques vanilla.
3. **Stardew Valley FR officiel** — recherche web pour les concepts hérités : Shipping Bin, Perfection, qualités, saisons…
4. **Traductions communautaires des autres langues du pack** (ko_kr complète, zh_cn, pt_br, th_th) — témoin d'esprit et d'interprétation : les termes que ces traducteurs ont choisi de **garder en anglais** alimentent notre liste de termes non traduits ; leurs choix sur les concepts ambigus servent de garde-fou contre les contresens.
5. **Arbitrage agent** pour les termes récurrents multi-mods restants (détectés par script sur l'index EN global).

Contenu du glossaire (`fr-workspace/glossaire.json` + version lisible) :
- ~100-200 entrées clés : terme EN → terme FR imposé + justification courte.
- **Liste explicite des termes gardés en anglais** : noms propres de mods (Create, Botania…), marques du pack (« Society », « Sunlit Valley »), termes iconiques dont la traduction trahirait l'esprit du jeu.

Guide de style (`fr-workspace/STYLE.md`) :
- **Registre** : tutoiement chaleureux dans quêtes et dialogues (esprit Stardew Valley) ; impersonnel/infinitif type Minecraft FR pour l'interface.
- **Capitalisation** : française (« Golden Hoe » → « Houe dorée », jamais « Houe Dorée »).
- **Typographie** : accents sur majuscules (É, À), apostrophe adaptée à la police Minecraft, espaces avant `!` `?` selon les contraintes d'affichage.
- **Politique accents** (selon résultat Phase 1) : si EMI sensible aux accents → noms d'items/blocs (`item.*`, `block.*`) sans accents pour garantir la recherche, français accentué partout ailleurs (quêtes, tooltips, UI).
- **Codes techniques intouchables** : `%s`, `%1$s`, `§x`, `\n`, JSON échappé, identifiants.

**✋ L'utilisateur valide ou amende le glossaire et le style avant toute traduction de masse.**

### Phase 3 — Traduction de masse (workflows par lots)

- Workflows successifs par lots de mods (~15 agents par workflow, conforme à la consigne de taille) ; un agent par mod.
- Fichiers volumineux (quêtes, Society, gros mods) découpés en tranches de ~200 clés ; chaque tranche reçoit le contexte global du mod.
- Chaque agent traducteur reçoit : glossaire + guide de style + `en_us.json` complet du mod + FR partiel du JAR le cas échéant + consignes techniques + **les traductions ko/zh/pt du même contenu quand elles existent**, comme témoin d'interprétation pour les chaînes ambiguës (elles éclairent le sens, jamais le style).
- **Livres Patchouli** : traduction des dossiers `patchouli_books/{almanac,fish_finder}/en_us/` vers `fr_fr/` en miroir (remplace le fr_fr existant). Seuls les champs textuels (`name`, `text`, `description`…) sont traduits ; patterns de multiblocs, icônes, IDs et marqueurs (🌐, codes `$(...)`/`§x`) sont préservés à l'identique.
- **Sortie structurée** (schéma JSON imposé via l'option `schema` du workflow) : validation mécanique immédiate à la sortie de chaque agent.
- Écriture dans `kubejs/assets/MODID/lang/fr_fr.json` (remplace les fichiers FR existants du modpack).

### Phase 4 — Vérification + réconciliation

Trois couches, dans l'ordre :
1. **Scripts déterministes** : JSON valide, ensemble de clés strictement identique à la source EN, placeholders préservés à l'identique (comparaison des ensembles `%s`/`%n$s`/`§x` entre EN et FR), pas de valeur vide, UTF-8, politique accents respectée sur `item.*`/`block.*` (si hybride active).
2. **Réconciliation mécanique** (garantie « 1 item = 1 traduction ») : index global « chaîne EN → {traductions FR} » sur tout le corpus produit + FR des JARs ; toute divergence → arbitrage par agent avec le glossaire → application mécanique de la traduction retenue partout. Les divergences des FR de JARs vs glossaire sont corrigées par **clés d'override ciblées** dans `kubejs/assets/MODID/lang/fr_fr.json` (les JARs ne sont jamais modifiés).
3. **Relecture qualité intégrale** : agents relecteurs sur tout le corpus produit — orthographe, grammaire, accords, naturel, fidélité au ton, respect du glossaire. Corrections appliquées puis re-passage de la couche 1.

### Phase 5 — Livrables

- Tous les `fr_fr.json` (kubejs) et les dossiers `patchouli_books/*/fr_fr/` committés sur `traduction-fr`, commits par phase.
- `fr-workspace/scripts/build_fr_resourcepack.py` : génère `resourcepacks/Society_FR.zip` (pack.mcmeta `pack_format: 15` pour 1.20.1) depuis les overrides kubejs — relançable à volonté pour partage éventuel.
- `docs/RAPPORT-TRADUCTION-FR.md` (racine du projet) : statistiques (mods/clés traduits, skippés et pourquoi), choix terminologiques majeurs, divergences réconciliées, **limites documentées**.
- Test final : validation mécanique complète + test en jeu par l'utilisateur (langue `fr_fr` dans les options Minecraft).

## Maintenance (mises à jour du pack)

L'inventaire (Phase 1) est relançable après une mise à jour du modpack : il détecte les clés nouvelles/modifiées et seul le **delta** est retraduit, avec le glossaire existant. Les fichiers de travail (`inventaire.json`, index EN→FR, glossaire) sont conservés dans `fr-workspace/` (racine du projet) à cette fin.

## Limites connues et hors périmètre

- **Chaînes codées en dur** : deux cas distincts.
  - *Dans les fichiers du pack* (scripts KubeJS, layouts FancyMenu, fichiers Dialog…) : **traduisibles, en périmètre opportuniste** — quand le framework le permet, le littéral anglais est converti en clé de lang (`Text.translate("clé")` en KubeJS) avec ajout de la clé dans `en_us.json` et `fr_fr.json`, ce qui garde le pack bilingue ; sinon, documentées au rapport. Ces conversions sont recensées dans un commit dédié (elles modifient des scripts, pas seulement des fichiers lang).
  - *Dans le code Java compilé des mods* : intraduisibles sans modifier le JAR — ajouter des clés de lang est sans effet si le code ne les consulte pas. Recensées dans le rapport final. Même catégorie : les rares écrans de configuration affichant le texte brut de leur fichier de config (clés TOML, commentaires). À noter : les écrans de configuration classiques, dont les libellés viennent des fichiers lang (cas majoritaire), sont traduits normalement par le pipeline.
- **Textes incrustés dans des textures** (images des menus FancyMenu, pages illustrées, GUIs) : non traduits pour l'instant, mais **recensés** — un inventaire best-effort (explicitement non exhaustif, alimenté au fil du travail) figure dans le rapport final pour servir de base à un futur chantier.
- **Contribution upstream** : hors périmètre, le projet refuse les traductions IA. Cette traduction reste personnelle ; un partage communautaire éventuel (resource pack étiqueté « traduction non officielle assistée par IA ») resterait hors du repo upstream.

## Critères de réussite

1. 100 % des clés du périmètre traduites (aucune clé EN restante dans les fichiers produits, hors limites documentées).
2. Zéro divergence : une même chaîne EN visible n'a qu'une seule traduction FR dans tout le pack (vérifié mécaniquement).
3. Zéro régression technique : tous les JSON valides, tous les placeholders préservés (vérifié mécaniquement).
4. Glossaire et style validés par l'utilisateur avant la masse ; recherche EMI fonctionnelle selon la politique accents retenue.
