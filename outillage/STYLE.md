# Guide de style FR — Sunlit Valley

Modpack Minecraft 1.20.1 dans l'esprit de Stardew Valley : ferme, saisons, villageois,
quêtes chaleureuses. Ce guide s'applique à TOUTES les traductions françaises du pack
(fichiers `lang`, quêtes FTB, livres Patchouli, tooltips, interface).

---

## 1. Registre

Deux registres distincts selon le contexte :

### Quêtes et dialogues : tutoiement chaleureux (esprit Stardew Valley)

Les quêtes, les dialogues de PNJ et les textes narratifs s'adressent au joueur avec un
tutoiement amical, direct, jamais froid ni administratif.

- ✅ « Bienvenue à la vallée ! Plante tes premières graines et récolte ta première culture. »
- ✅ « Tu as bien mérité une pause. Passe voir Pierre à la boutique, il a quelque chose pour toi. »
- ❌ « Veuillez planter des graines afin de compléter cet objectif. »
- ❌ « Le joueur doit récolter une culture. »

### Interface : impersonnel / infinitif (convention Minecraft FR)

Les boutons, menus, options et tooltips d'action suivent la convention Minecraft FR
officielle : infinitif ou tournure nominale, jamais de tutoiement ni de vouvoiement.

- ✅ Bouton : « Trier l'inventaire »
- ✅ Tooltip d'action : « Clic droit pour arroser »
- ✅ Menu : « Paramètres du monde »
- ❌ « Triez votre inventaire »
- ❌ « Clique ici pour arroser »

---

## 2. Capitalisation française

Le français ne met PAS de majuscule à chaque mot (pas de Title Case anglais). Seul le
premier mot d'un nom d'objet prend une majuscule ; le reste est en minuscules, sauf noms
propres.

- ✅ « Houe dorée » — ❌ « Houe Dorée »
- ✅ « Graines de chou-fleur » — ❌ « Graines De Chou-Fleur »
- ✅ « Arrosoir en cuivre » — ❌ « Arrosoir En Cuivre »

Dans le corps d'une phrase, les noms communs restent en minuscules même s'ils désignent
un objet du jeu :

- ✅ « Utilise ta houe dorée pour labourer la terre, puis remplis ton arrosoir. »
- ❌ « Utilise ta Houe Dorée pour labourer la terre, puis remplis ton Arrosoir. »

---

## 3. Politique accents (décision figée — voir DECISION-ACCENTS.md)

Décision issue de l'inspection d'`emi-1.1.24+1.20.1+forge.jar` : la recherche EMI ne
normalise pas les diacritiques (aucun usage de `java/text/Normalizer`, `NFKD`, `NFD`) —
taper « ble » ne matche pas « Blé ». Politique hybride validée par l'utilisateur au
brainstorming :

- `accent_free_prefixes = ["item.", "block.", "entity."]`
- Les valeurs des clés `item.*`, `block.*`, `entity.*` sont écrites **SANS accents**
  (recherche fiable en jeu).
- Tout le reste (quêtes, tooltips, descriptions, interface, livres Patchouli) est en
  **français correctement accentué**.

Exemples :

| Clé | Valeur | Pourquoi |
|---|---|---|
| `item.croptopia.ble` | `Ble` | préfixe `item.` → sans accents |
| `block.farmersdelight.serre` | `Serre chauffee` | préfixe `block.` → sans accents |
| `entity.minecraft.bee` | `Abeille` (pas d'accent requis ici de toute façon) | préfixe `entity.` → sans accents |
| Quête FTB | « Récolte du blé pour préparer ta première miche. » | hors préfixes → accents complets |
| Tooltip descriptif | « Cet arroseur automatique irrigue les cultures adjacentes. » | hors préfixes → accents complets |

---

## 4. Typographie

- **Accents sur les majuscules** : É, À, È, Ç sont obligatoires (hors clés `item.*`,
  `block.*`, `entity.*` où les accents sont supprimés partout).
  - ✅ « Épée en fer » (tooltip), « À la ferme ! » — ❌ « Epee », « A la ferme ! » (hors préfixes concernés)
- **Apostrophe droite `'`** (compatible police Minecraft), jamais l'apostrophe typographique `’`.
  - ✅ « L'arrosoir d'Émilie » — ❌ « L’arrosoir d’Émilie »
- **Espace simple avant `!` et `?`** — pas d'espace insécable (elle s'affiche mal ou casse
  les retours à la ligne dans Minecraft).
  - ✅ « Bien joué ! Tu veux continuer ? » — ❌ « Bien joué&nbsp;! » ni « Bien joué! »
- **Guillemets droits `"..."`** plutôt que « ... » dans les textes courts d'interface
  (boutons, tooltips, messages système). Les guillemets français restent acceptables dans
  les longs textes narratifs (quêtes, livres) si la place le permet.
  - ✅ Tooltip : `Renommer en "Ferme du Soleil"` — ❌ Tooltip : `Renommer en « Ferme du Soleil »`

---

## 5. Codes intouchables — recopier tels quels

Ne JAMAIS traduire, déplacer, supprimer ni reformater les codes suivants. Les recopier
strictement à l'identique dans la traduction :

| Code | Rôle | Exemple |
|---|---|---|
| `%s` | substitution simple | `« %s a rejoint la partie »` |
| `%1$s` | substitution positionnelle (l'ordre peut changer dans la phrase FR, pas le code) | `« %2$s offert par %1$s »` |
| `§x` | codes de formatage Minecraft (couleur/style : `§a`, `§l`, `§r`…) | `« §6Houe dorée§r »` |
| `$(...)` | macros Patchouli | `« $(item)Arrosoir$() »` |
| `{0}` | placeholders style Java/FTB | `« Récompense : {0} pièces »` |
| `\n` | saut de ligne littéral dans les JSON lang | `« Ligne 1\nLigne 2 »` |
| `%%` | pourcent littéral échappé | `« +10%% de vitesse »` |
| `🌐` | emoji/symboles présents dans la source | conserver tel quel |

Règle d'or : le nombre et la nature des placeholders dans la traduction doivent être
identiques à la source. `%s` reste `%s`, jamais « %S », « % s » ni supprimé.

---

## 6. Faux-amis et pièges du domaine

Lexique imposé (esprit ferme/Stardew Valley) — ne pas traduire littéralement :

| Anglais | ✅ Traduction | ❌ Piège à éviter |
|---|---|---|
| crop | culture | « récolte » (harvest), « crop » laissé tel quel |
| watering can | arrosoir | « canette d'arrosage », « bidon » |
| mill | moulin | « usine », « broyeur » (sauf contexte machine explicite) |
| seed | graine | « semence » (registre trop technique), « graines » au singulier |
| quality | qualité | « qualitatif » |
| bait | appât | « amorce » |
| tackle | accessoire de pêche | « plaquage », « matériel » seul |
| roe | œufs de poisson | « rogue » seul, « caviar » (produit transformé distinct) |
| coop | poulailler | « coopérative », « coop » laissé tel quel |
| barn | grange | « étable » (sauf si le contexte est exclusivement bovin), « ferme » |
| greenhouse | serre | « maison verte » |
| sprinkler | arroseur automatique | « gicleur », « sprinkleur » |
| forage | cueillette | « fourrage » (foin pour animaux !), « fourrager » |

Exemples en contexte :

- ✅ « Améliore ton arrosoir au moulin ? Non — chez le forgeron ! L'arroseur automatique,
  lui, se fabrique à l'établi. »
- ✅ « La cueillette de printemps : ramasse pissenlits et poireaux sauvages. »
- ❌ « Le forage de printemps » (contresens total : forage = drilling).
- ✅ « Construis un poulailler pour tes poules et une grange pour tes vaches. »

---

## 7. Distinctions à ne pas uniformiser

Certains mots anglais ont deux sens dans le pack et doivent garder deux traductions.
Une passe de cohérence ne doit pas les fusionner.

### Crimson → toujours « carmin »

Terme vanilla officiel de Mojang (`Crimson Planks` → « Planches carmin »), retenu pour
TOUS les emplois, qu'il s'agisse de la matière du Nether (bois carmin, NetherVinery,
gabarits EveryCompat) ou d'un simple qualificatif de couleur (briques carmin d'Unusual
Fish, scorpion carmin). Un terme anglais = une traduction française.

« Cramoisi » a été écarté : plus littéraire, plus rude, et il introduisait une double
traduction sans bénéfice perceptible pour le joueur.

ACCORD : « carmin » est un nom de couleur employé comme adjectif, donc INVARIABLE —
« briques carmin », jamais « briques carmines ». Mojang applique la même règle.

### Shale → « shale », jamais « schiste »

Le mod Windswept nomme cette pierre « shale » dans sa propre traduction française
officielle (« Shale poli », « Dalle en shale taillé »). Traduire par « schiste » la
seule entrée `block.windswept.shale` créerait une exception au sein de sa famille.

### Conventions de nommage des blocs dérivés (Mojang)

- `*_stairs` → « **Escalier** en X » au SINGULIER (`Brick Stairs` → « Escalier en briques »),
  jamais « Escaliers ».
- `*_wall` → « **Muret** de X » (`Brick Wall` → « Muret de briques »), jamais « Mur ».
  Exception : les clés `sconce_*_wall` désignent des appliques murales, pas des murets →
  « Applique ».
- `*_slab` → « Dalle de X ».

Ces trois familles ne se réconcilient PAS automatiquement : la comparaison de cohérence
ne rapproche que des chaînes anglaises identiques, or « Chalcedony Stairs » et
« Crabapple Stairs » sont deux chaînes distinctes. Vérifier par requête sur le suffixe
de la clé lors d'une mise à jour.

### Cranberry → « cranberry », pas « canneberge »

Anglicisme retenu sur choix de l'utilisateur : c'est la forme courante dans le commerce
en France, même si « canneberge » est le terme français normé. Exception assumée au
principe « tout traduire » — les autres baies restent en français (Blueberry → Myrtille,
Currant → Groseille, Boysenberry → Baie de Boysen).
Accord : « une cranberry », « des cranberries ».

### Fruits : nom du fruit, de l'arbre, et recherche EMI

Conventions du mod Pam's, à respecter :
- item `X`          → nom du fruit          (Apple → Pomme)
- bloc `X Fruit`    → « Fruit de <arbre> »  (Apple Fruit → Fruit de pommier)
- bloc `X Sapling`  → « Pousse de <arbre> » (Apple Sapling → Pousse de pommier)

Ces conventions ne valent QUE si le nom de l'arbre partage un radical avec celui du
fruit : pomme/pommier, cerise/cerisier, vanille/vanillier, passion/passiflore. La
recherche EMI compare des sous-chaînes (`toLowerCase().contains`), donc taper « vanill »
ou « passi » retrouve bien le fruit, le bloc et la pousse.

EXCEPTION — dragonfruit : « pitaya » ne partage aucune lettre avec « dragon », ce qui
rendait la pousse et le bloc introuvables. Toute la famille est donc sur « fruit du
dragon », y compris « Pousse de fruit du dragon » — seule pousse du pack à ne pas nommer
un arbre. « Dragonnier » était indisponible (déjà pris par verdantvibes:dragon_tree,
Dracaena marginata). Le choix préserve aussi le jeu de mots « Fruit de l'Ender Dragon ».

### Les cinq Maîtrises — formulation unique

Nom canonique du talent (arbre de compétences) : « Maîtrise de l'agriculture »,
« Maîtrise de l'aventure », « Maîtrise du minage », « Maîtrise de la pêche »,
« Maîtrise de l'élevage ». Majuscule à Maîtrise : c'est un nom propre de talent.
Reprendre cette forme EXACTE partout — quêtes, tooltips JEI, livres de compétences,
messages de blocs. Ne pas écrire « maîtrise en agriculture » ni « maîtrise de minage ».

### Registre des messages du pack

Les namespaces `society*` tutoient le joueur, y compris dans les descriptions d'objets
et les messages de blocs (« Te téléporte… », « Tu dois avoir débloqué… »). Aucun
vouvoiement ne doit subsister.

### Casse des cinq compétences

Agriculture, Élevage, Minage, Pêche, Aventure prennent la MAJUSCULE quand on nomme le
talent (« l'expérience en Agriculture », « la compétence d'Élevage »), et restent en
minuscule au sens courant (« la pêche est une joie sereine », « corde d'agriculture »,
« dimension de minage »).
