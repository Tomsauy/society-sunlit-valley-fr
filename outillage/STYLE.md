# Guide de style FR — Sunlit Valley

Modpack Minecraft 1.20.1 dans l'esprit de Stardew Valley : ferme, saisons, villageois, quêtes chaleureuses. Ce guide
vaut pour tout le français du pack : fichiers `lang`, quêtes FTB, livres Patchouli, infobulles, interface, journal
du menu titre.

Il énonce les règles en vigueur, chacune avec sa raison. Les exemples sont des textes du jeu. L'historique des
décisions est dans `provenance.json` et dans `docs/specs/`. Les termes un par un sont dans `GLOSSAIRE.md`, les
termes gardés en anglais dans `KEEP-ENGLISH.md` ; les deux sont générés depuis `provenance.json`.

---

## 1. Registre

### Society : tutoiement chaleureux

Les quêtes, les dialogues des villageois, les livres de Society (almanach, guide des poissons), les astuces et tous
les textes des namespaces `society*` s'adressent au joueur en le tutoyant, d'un ton amical et direct, comme Stardew
Valley. Les descriptions d'objets et les messages de blocs de Society aussi.

- « Fabrique un tonneau à vin pour transformer tes fruits en vin. »
- « Achète quelque chose ou passe ton chemin. »
- « Te téléporte un niveau plus bas dans la Caverne du Crâne »

### Interface : infinitif ou tournure nominale

Les boutons, menus, options et infobulles d'action ne tutoient ni ne vouvoient : infinitif ou nom, comme Mojang.

- « Trier », « Masquer », « Afficher le bouton "Terminé" »

### Les autres mods : le registre de chaque texte reste tel qu'il est

Hors Society, beaucoup de textes viennent de la traduction officielle d'un mod ou la prolongent ; nombre d'entre eux
vouvoient. On ne change pas le registre d'un mod, et on ne réaligne pas les textes d'un mod sur sa forme majoritaire
(décision de l'utilisateur) : un « vous » dans un texte de Botania ou de Quark n'est pas une faute.

Ce qui vaut partout : **un même texte ne mélange pas tu et vous.**

---

## 2. Capitalisation

Pas de majuscule à chaque mot : seul le premier mot d'un nom prend la majuscule, plus les noms propres.

- « Arrosoir en cuivre », « Graines de chou », « Houe en or »

**Métiers et boutiques.** Le métier d'un villageois et le nom d'une boutique prennent la majuscule quand ils
désignent ce villageois ou cette boutique, comme un nom de personne, dans un nom, un titre ou une phrase :
« Villageois Pêcheur », « Maison de villageois - Berger », « Il est vendu au &6Marché&r et chez le &6Berger&r »,
« auprès d'un Banquier ». Au
sens courant, le mot est un nom commun, en minuscules : « un simple fermier comme toi », « les fermiers » ; de même
dans un nom d'objet, après « de », « du », « des » ou « d' » : « Chapeau de sorcière », « Pain du fermier ».

**Slime** garde sa majuscule partout, comme un nom de personne : « Coeur de Slime », « Seau de Slime ». Les noms de
Mojang ne sont pas surchargés pour autant : « Bloc de slime », « Boule de slime ».

**Créatures gardées en anglais.** Un nom de créature gardé en anglais prend la majuscule, comme chez Mojang (« Oeuf
d'apparition d'Enderman », « Mayonnaise de Wraptor ») ; un nom devenu un mot français reste en minuscules (axolotl,
panda, zombie).

**Lieux.** Les six salles du Centre communautaire sont des noms de lieu : Garde-manger, Salle d'artisanat, Aquarium,
Chaufferie, Coffre-fort, Ferme abandonnée.

**Noms inventés.** Un nom inventé par un mod reste en minuscules dans une phrase : « de la sparkstone ».

**Mise en valeur.** Dans une phrase, un nom d'objet mis en valeur par un code couleur garde sa majuscule ; sans mise
en valeur, il reste en minuscules.

- « Il est vendu au &6Marché&r et chez le &6Berger&r »

**Effets, enchantements, sorts et capacités.** Cité comme tel, le nom garde la majuscule de son premier mot, comme
chez Mojang : c'est un nom de règle du jeu, et la minuscule rendrait ambigus ceux qui sont aussi des mots courants
(fortune, force, poison). Employé comme nom commun, il passe en minuscule.

- « Toucher de soie », « Poison III », « Chances accrues avec Fortune » ; mais « un effet de lévitation »

**Fiches et étiquettes.** Dans les fiches de l'almanach, du guide des poissons et du compendium de Wilder Nature, la
valeur après l'étiquette est un nom affiché seul et garde sa majuscule ; une valeur qui n'est pas un nom reste en
minuscules. De même pour les infobulles « Étiquette : valeur » et les préfixes de mod.

- « Butin : Boeuf cru », « Machines compatibles : … » ; mais « Cueillette : fruits communs aléatoires »

**Les cinq compétences** (Agriculture, Élevage, Minage, Pêche, Aventure) prennent la majuscule quand on nomme le
talent (« l'expérience en Agriculture ») et restent en minuscules au sens courant (« corde d'agriculture », « dimension de minage »).

---

## 3. Accents et orthographe

**Tout est accentué**, noms d'objets compris, majuscules comprises : É, À, È, Ç (« Épée en fer », « À la ferme »).
La recherche en jeu reste fiable pour un joueur qui tape sans accents grâce au mod
[Accent Fold](https://github.com/Tomsauy/accent-fold), qui rend insensibles aux accents les barres de recherche du
pack : inventaire créatif, JEI, EMI, Refined Storage, Quark, Create, Sophisticated, FTB, Patchouli, Botania. Sans le
mod, la recherche marche toujours, mais à la lettre.

**« oe », jamais la ligature « œ »** : « coeur », « oeuf », « noeud », « Oeufs de morue ». Les autres accents restent :
« poêle ».

**Mots à double sens.** Le vocabulaire accentué est figé dans `accents/vocabulaire.json`, dont seize mots à double sens
(`séché`/`sèche`, `sale`/`salé`, `mur`/`mûr`) ; le contrôle `accents` du vérificateur l'applique.

**Noms inventés par les mods : intouchés**, c'est-à-dire non traduits : « Sparkstone », « Shrooma », « Ochrum »,
« Ether ». Leur casse suit le §2.

**« Locométal » est l'exception** : mot-valise de Create: Steam 'n' Rails (locomotive + métal) dont les deux moitiés
sont françaises, il est francisé et accentué partout, noms d'objets compris.

---

## 4. Typographie

- **Apostrophe droite** `'`, jamais `’` : c'est celle de la police de Minecraft.
- **Espace simple avant `!` et `?`**, jamais d'espace insécable : Minecraft l'affiche mal et elle casse les retours à
  la ligne. « Tu as rendez-vous ? »
- **Guillemets droits** `"…"` dans les textes courts d'interface : « Afficher le bouton "Terminé" ». Les guillemets
  français restent possibles dans les longs textes narratifs (quêtes, livres).
- **Pourcentages** : « 25 % », avec une espace simple, comme Mojang ; le code `%%` suit la même règle : « Saumure et Châtiment +100 %% ».
- **Points de suspension** : trois points « ... », comme Mojang, jamais le caractère « … ».

---

## 5. Codes intouchables

Recopier à l'identique, sans traduire, déplacer, supprimer ni reformater :

| Code | Rôle | Exemple |
|---|---|---|
| `%s` | substitution simple | `%s a rejoint la partie` |
| `%1$s` | substitution positionnelle : l'ordre peut changer dans la phrase, pas le code | `%2$s offert par %1$s` |
| `§x`, `&x` | codes de formatage Minecraft et FTB (couleur, style) | `&6Marché&r` |
| `$(...)` | macros Patchouli | `$(item)Arrosoir$()` |
| `{0}` | placeholders style Java ou FTB | `Récompense : {0} pièces` |
| `\n` | saut de ligne littéral dans les JSON | `Ligne 1\nLigne 2` |
| `%%` | pourcent littéral échappé | `+100 %%` |

Le nombre et la nature des placeholders sont identiques à la source : `%s` reste `%s`, jamais « %S » ni « % s ».

---

## 6. Vocabulaire du domaine

Termes de la ferme et de Stardew Valley, à ne pas traduire littéralement :

| Anglais | Français | Piège |
|---|---|---|
| crop | culture | « récolte », qui est le harvest |
| forage | cueillette (« Lot de cueillette ») | « fourrage », le foin des animaux ; « forage », le drilling |
| seed | graine (« Graines de chou ») | « semence », trop technique |
| sprinkler | arroseur (« Arroseur en fer ») | « gicleur », « sprinkleur » |
| watering can | arrosoir | « canette d'arrosage » |
| bait | appât (« Appât pour carpe ») | « amorce » |
| tackle box | boîte de pêche | « plaquage », le sens sportif de tackle |
| roe | oeufs de poisson (« Oeufs de morue ») | « caviar », un produit distinct |
| coop | poulailler | « coopérative » |
| barn | grange | « étable », « ferme » |
| greenhouse | serre | « maison verte » |
| bundle (Centre communautaire) | lot | « sac », réservé au contenant de Mojang |

---

## 7. Distinctions et familles de noms

Certains choix tiennent à une famille entière ; une passe de cohérence ne doit pas les défaire.

**Crimson → « carmin », partout.** Terme de Mojang (« Planches carmin »), pour la matière du Nether comme pour la
couleur. Nom de couleur employé comme adjectif, il est invariable : « Briques carmin », jamais « carmines ».
« Cramoisi » est écarté.

**Shale → « shale », jamais « schiste ».** C'est le nom de la pierre de Windswept dans sa propre traduction (« Shale
poli »). « Schiste » reste à Schist de Twigs, une autre roche.

**Blocs dérivés, comme Mojang :**

- escalier : « **Escalier en** X », au singulier (« Escalier en briques », « Escalier en tuf ») ;
- muret : « **Muret de** X » (« Muret de briques ») ; les clés `sconce_*_wall` sont des appliques murales :
  « Applique » ;
- dalle : « **Dalle en** X » pour un bois (« Dalle en chêne »), « Dalle carmin », « Dalle biscornue » pour les bois
  du Nether, « **Dalle de** X » pour une pierre (« Dalle de roche », « Dalle de tuf poli ») ;
- porte et objet fait d'une matière : « en » (« Porte en cuivre »).

La comparaison de cohérence ne rapproche que des anglais identiques : « Chalcedony Stairs » et « Crabapple Stairs »
ne se comparent pas. À chaque mise à jour, vérifier ces familles par le suffixe de la clé.

**Cranberry → « cranberry ».** Anglicisme retenu, forme courante dans le commerce en France ; « une cranberry », « des
cranberries ». Les autres baies sont en français : Myrtille, Groseille, Baie de Boysen.

**Fruits de Pam's.** L'objet porte le nom du fruit, le bloc « Fruit de <arbre> », la pousse « Pousse de <arbre> »
(« Fruit de pommier », « Pousse de pommier »), tant que l'arbre partage un radical avec le fruit : la recherche
compare des morceaux de mots, et « pomm » trouve les trois. Le fruit du dragon fait exception : « pitaya » ne partage
rien avec « dragon », et toute la famille dit « fruit du dragon », jusqu'à « Pousse de fruit du dragon ».

**Les cinq Maîtrises**, forme exacte partout : « Maîtrise de l'agriculture », « Maîtrise de l'aventure », « Maîtrise
du minage », « Maîtrise de la pêche », « Maîtrise de l'élevage ». Majuscule à Maîtrise, nom propre du talent.

---

## 8. Où vivent les autres règles

| fichier | contenu |
|---|---|
| `GLOSSAIRE.md` | les termes un par un, avec leur sens quand un anglais en a plusieurs ; généré |
| `KEEP-ENGLISH.md` | les termes gardés en anglais et pourquoi ; généré |
| `coherence/termes_imposes.json` | les termes imposés partout et leurs anciennes formes interdites |
| `accents/vocabulaire.json` | le vocabulaire accentué figé |
| `provenance.json` | chaque décision, clé par clé, avec sa raison |
