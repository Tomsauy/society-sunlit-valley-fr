# Données de cohérence

Lues par `fr-workspace/scripts/verifier.py`. Chaque fichier est requis : un fichier absent arrête le
vérificateur (code 2) en le nommant, car il viderait sinon son contrôle sans bruit, et le rapport
inviterait à retirer de la dette ce qu'il ne cherche plus. Une valeur vide s'écrit explicitement
(`[]`, `{}`). Il en va de même, hors de ce dossier, de `accents/vocabulaire.json`, `provenance.json`,
`KEEP-ENGLISH.md`, `references/mc_en_us.json`, `references/mc_fr_fr.json` et
`society-corrected-en.json`. Leur forme et leurs valeurs sont vérifiées au chargement (celles du tableau
ci-dessous) : un fichier mal formé arrête aussi le vérificateur, en le nommant. Tous s'écrivent en JSON
indenté d'un espace, UTF-8, saut de ligne final.

`--dette-retirer-resolus` ne retire rien d'un passage en échec (code non nul) : ce qui y semble résolu
peut venir d'un contrôle vidé. Le rapport nomme chaque entrée retirée, ou à retirer.
`--dette-base FICHIER` fait échouer le passage si `dette.json` contient une entrée (contrôle, clé,
objet) absente de cette dette de référence, celle de la branche visée par une PR : la dette ne fait que
décroître.

| fichier | forme | qui l'alimente |
|---|---|---|
| `exceptions.json` | liste de `{controle, cle, objet?, motif, date, epingle?, empreinte?, question?}` | à la main, relu en entier dans chaque PR |
| `dette.json` | liste de `{controle, cle, objet, empreinte, detail, source, en_attente_de_decision?}` | établie une fois ; ne fait que décroître (`--dette-retirer-resolus`) |
| `familles.json` | `{familles: [{nom, motif, source, gabarit, anglais, cles_source?, noms_source?}], accords: {clé source: {genre, nombre, propre?}}}` | `generer_derives.py --proposer`, puis relecture |
| `gabarits.json` | `{cle: [[types de l'argument 1], …]}`, types `nom_objet`, `saison`, `autre` | complète ce que les scripts ne disent pas |
| `largeurs.json` | liste de `{cle, limite, motif}` (pixels) | à la main, après mesure en jeu |
| `scripts_patches.json` | `{chemin: {base, motif}}` (`base` : sha du blob amont patché) | à chaque patch d'un script de l'amont |
| `mots_generiques.json` | `{mot ou expression anglaise: motif}` (« Light », « The End ») | tri du contrôle `references` |
| `mods_retires.json` | `{namespace: motif}` | tri du contrôle `couverture` |
| `formes_interdites.json` | liste de `{forme, juste, source}` | chaque faute rencontrée |
| `noms_propres.json` | `{mot ou expression: motif}` (noms propres, noms inventés, sigles) ; `accents`, `casse` et `anglais_residuel` exemptent un mot seul partout, noms d'objets compris, et une expression de plusieurs mots (« Cozy Cafe », « Caverne du Crâne ») là seulement où elle figure en entier ; pour `casse` et `anglais_residuel`, le trait d'union et l'apostrophe séparent aussi les mots (« Tri-bull », « l'Ombre »). `casse` lit la clé telle qu'elle est écrite : un nom inventé employé comme nom commun se déclare en minuscules (« asurine », « sparkstone ») et n'exempte pas une majuscule interne ; en retour, une expression de plusieurs mots déclarée avec sa majuscule (« Foire aux livres ») la garde partout où elle est écrite. Un mot accentué, ou dont le pli est celui d'un mot accentué, ne se déclare jamais seul : `accents` exempterait sa forme sans accent partout ; il se déclare dans une expression (« de Noël », « de Pâques ») | tri de `casse`, `anglais_residuel` et `accents` |
| `majuscules.json` | `{mot: motif}` : mots qui gardent leur majuscule partout, comme un nom de personne (« Slime », « Slimes ») ; lu par `casse` seul, qui accepte leur majuscule dans les noms, les titres et les phrases sans l'imposer, un mot seul partout, une expression de plusieurs mots là seulement où elle figure en entier. Contrairement à `noms_propres.json`, ni `accents` ni `anglais_residuel` ne l'exemptent. Les métiers des villageois et les noms des boutiques, traités de même, ne s'y déclarent pas : `casse` les lit dans les clés `entity.minecraft.villager.<id>`, `entity.minecraft.villager.<mod>.<id>` et `shop.society_trading.<id>` ; dans un nom d'objet, juste après « de », « du », « des » ou « d' », ils redeviennent des noms communs (« Chapeau de sorcière »), pas les mots de ce fichier (« Seau de Slime ») | décisions de l'utilisateur (STYLE §2) |
| `termes_imposes.json` | liste de `{anglais (regex), francais, portee, cles?, interdits?, motif}` | STYLE §6 et §7 |
| `regles.json` | `{casse_textes: bool, pourcentages: "" \| "espace" \| "colle"}` ; depuis le sous-projet 2, `casse_textes` est actif (`casse` lit aussi les noms cités dans les phrases) et `pourcentages` vaut `"espace"` (« 25 % », variables comprises : « %s %% ») | fiche de décisions |
| `double_sens.json` | liste de `{anglais, justes, motif}` | les 16 mots à double sens du vocabulaire |
| `homographes.json` | `{mot plié: motif}` : mots dont la forme sans accent est aussi du français (« ameliore ») | tri du contrôle `accents` |
| `renvois.json` | liste de `{controle, cle, objet?, motif}` : entrées de dette renvoyées au sous-projet 3 | par l'applicateur (action `renvoi`) ; `--cloture` exige que toute la dette y figure |

Une exception sans objet porte l'`empreinte` du texte de sa clé (spec 2 §7) : si le texte change, elle ne couvre
plus rien, le constat revient et l'exception est signalée orpheline ; on corrige, ou on la réaffirme avec
l'empreinte du nouveau texte. Une exception qui porte `question` est provisoire : elle attend la réponse de
l'utilisateur sur la page de relecture. La réponse lue, on corrige ou on la rend définitive : sans `question`,
avec un motif qui cite la question tranchée.

`--cloture` dit si le sous-projet 2 peut se clore : ni bloquant, ni exception sans motif, ni exception
provisoire, ni exception ou renvoi orphelin, ni signalement sans suite, et toute entrée de dette restante
renvoyée au sous-projet 3 (`renvois.json`). Clos le 02/10/2026 : dette et renvois vides
(`fr-workspace/lots/BILAN.md`).

La règle « même mod » de `references` est retirée (spec 2 §7, lots 3a) : un nom d'un seul mot est cité dans un
nom comme dans une phrase, quel que soit son mod. Un matériau (« Cherry Planks ») s'écarte par une exception à
`objet`, un mot qui ne cite jamais son objet par `mots_generiques.json`.

Les mots français identiques à l'anglais (« tunnel », « talc ») s'ajoutent au glossaire de
`provenance.json` (`garde_anglais: false`) ; les termes gardés en anglais aussi (`garde_anglais:
true`) : `anglais_residuel` et `casse` les lisent là.

Une exception couvre les constats de son contrôle sur sa clé ; avec `objet`, seulement ceux qui
visent cet objet. Une exception `epingle: true` du contrôle `references` ne couvre rien : elle
désigne l'objet visé par un texte quand plusieurs objets portent le même nom anglais. Une
référence ambiguë a pour `objet` ce nom anglais : c'est lui que porte l'exception qui l'écarte
quand le texte ne vise aucun de ces objets. Un groupe d'homonymes a pour `objet` la liste triée de
ses clés : une distinction déclarée pour deux objets ne couvre pas un troisième.

Une entrée de dette ne vaut que pour le constat qu'elle a photographié — même contrôle, même clé,
même objet — : il est signalé en dette tant que la valeur française de la clé ne change pas (pour
`homonymes`, ni les variantes du groupe), bloquant sinon. Tout autre constat de la clé reste
bloquant, et seule l'entrée appariée compte comme utile.
