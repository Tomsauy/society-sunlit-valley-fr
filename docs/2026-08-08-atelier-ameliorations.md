# Atelier — améliorations reportées

**Statut** : première version acceptée le 19 août 2026. Rien ici ne bloque l'usage ;
tout a été trouvé, mesuré et sciemment reporté pendant la construction ou la revue
finale. Le détail des mesures et le motif de chaque report sont dans le journal des
décisions, `.superpowers/sdd/2026-08-08-atelier-traductions/progress.md`.

Spécification : `docs/specs/2026-08-08-atelier-traductions-design.md` — elle a été mise
en accord avec ce que la première version fait réellement, y compris ce qu'elle ne fait pas.

---

## 1. Le grand chantier : quêtes et livres en lecture seule

Le modèle d'entrée unifié de la spécification n'est implémenté que pour les clés de
langue. Les quêtes et les livres Patchouli sont **lus et parcourus, mais pas cherchables,
pas traçables et pas modifiables** depuis le site.

Conséquence à connaître : `provenance.json` porte **121 décisions documentées sur des
textes Patchouli**, indexées par pointeur de page, qu'aucun écran ne sait montrer.
Les textes de quêtes s'en tirent indirectement — ils vivent dans des fichiers de langue,
donc la vue Clés les atteint — mais rien dans la vue Quêtes n'y mène.

Ce que cela demanderait : étendre l'index aux deux autres natures (`kind: "quest"` et
`kind: "patchouli"`), brancher le panneau de traçabilité sur les onglets correspondants,
et écrire un écrivain Patchouli. Le lecteur calcule déjà un `pointeur` pour les 524 pages —
champ que rien ne consomme aujourd'hui, faute d'écrivain.

C'est le seul point de cette liste qui change ce que l'outil sait faire. Tout le reste
est du polissage.

## 2. Fonctions de la conception non livrées

- **Groupement par mod repliable** dans la vue des clés, avec la version du JAR en tête
  de groupe. La version reste visible dans le panneau de traçabilité, et le filtre par
  namespace joue le même rôle.
- **Filtres complémentaires** dans un panneau replié : origine de l'anglais, présence
  d'une correction de relecture, sens incertain, termes gardés en anglais. Le filtre par
  origine existe côté serveur sans interface — à manier avec prudence, la valeur `aucune`
  couvrant 11 412 clés dont l'immense majorité est du bruit de mods mal synchronisés.
- **Filtres enregistrés** — des requêtes nommées, réutilisables en un clic.

## 3. Justesse

- **Une valeur `""` compte comme « langue présente ».** 200 valeurs vides dans le corpus,
  dont **10 où le français est vide alors qu'une autre langue a du contenu réel** (par
  exemple `create.schematic.tool.flip.description.2`). Le filtre Avec/Sans les masque donc.
  Non corrigé parce que la politique de traduction connaît des clés délibérément vides
  (code `should_be_empty` du validateur) et qu'inverser la sémantique produirait des faux
  positifs. À traiter comme un signalement distinct, pas comme une redéfinition de « présent ».
- **`retirerMarque` garde un repli par clé nue.** Deux marques antérieures sans `id` sur une
  même clé partagée seraient retirées ensemble. Inatteignable par l'interface — toute marque
  posée par le site porte un `id` — mais le chemin existe pour un fichier édité à la main.
- **La comparaison de codes du site et le validateur d'écriture sont en désaccord** : le
  premier compte les `&x`, le second les ignore (comme `validate_translation.py`). Une
  correction faite depuis le panneau Clés sur une description de quête qui perd un `&6` est
  acceptée sans un mot, alors que la vue Quêtes l'aurait signalée.
- **`en === null` est supposé équivalent à l'origine « aucune »** sans être vérifié. Aucun
  `en_us.json` du corpus ne porte de valeur nulle littérale aujourd'hui.

## 4. Poids et coûts

- **`/api/quetes` renvoie l'arbre entier** — 1,58 Mo, 528 quêtes × 12 langues — à chaque
  ouverture de l'onglet, sans pagination ni cache client. `/api/livres` pèse 574 Ko, dont un
  champ `pointeur` sur 524 pages que rien ne consomme faute d'écrivain Patchouli.
- **La recherche recalcule les minuscules** de chaque entrée à chaque requête : environ
  105 ms en mode « toutes langues ». Pré-calcul possible à la construction de l'index.
- **La construction de l'index** boucle en clés × locales, environ 0,6 s sur 2,3 s, le reste
  étant dominé par les entrées-sorties.
- **`EXTRACTED` reste surveillé** alors que `WORKSPACE` le couvre : deux déclencheurs pour
  un même changement.

## 5. Interface et confort

- **L'interface ne s'interroge pas d'elle-même.** Le rechargement à chaud fonctionne pour
  les cinq sources, mais hors de la vue Clés — qui rappelle le serveur à chaque frappe — il
  faut recharger la page pour voir un changement.
- **Le sélecteur « + langue » liste les 105 locales globales**, là où la conception disait
  « parmi les langues réellement présentes pour les entrées affichées ». Ajouter une colonne
  donne souvent 200 tirets.
- **Les deux panneaux se recouvrent** — « + langue » pour les colonnes et « Langues » pour le
  filtre — s'ils sont ouverts ensemble : même `z-index`, pas d'exclusion mutuelle.
- **Après retrait d'une langue du filtre**, le focus clavier retombe sur le corps de la page.
- **Aucun message ne marque le retour à la normale** après réparation d'un fichier illisible.
  `/api/sante` reflète l'état réel, mais qui surveille le seul flux console reste sans
  confirmation.
- **`Rail.svelte` replie le compteur de la file à revoir sur `0`** là où les trois autres
  onglets affichent `…` quand la valeur est inconnue.
- **Palette** : fonds `#fff` littéraux dans la vue Clés et gris en dur dans le rail, là où des
  variables CSS existent.

## 6. Dette technique mineure

- **Une route `/api` inconnue tombe sur le repli SPA** — 200 HTML — au lieu d'un 404 JSON.
  Combiné à l'affichage des erreurs, une route mal orthographiée se lit comme une erreur
  d'analyse JSON dans la vue.
- **Aucun test d'intégration sur les routes**, y compris `/corriger`, le premier chemin
  d'écriture. Conforme aux conventions du dépôt — aucune route n'est testée — mais notable.
- **`evenementsPourNamespace` a un troisième cas non nommé** : un événement dont le `fichier`
  ne contient pas `assets/<ns>/` est écarté pour tous les namespaces. 121 événements réels,
  tous Patchouli, donc inoffensif tant que ces textes ne sont pas indexés.
- **`BooksView` compose sa clé d'ouverture avec l'id du livre pour les catégories mais pas
  pour les entrées.** Vérifié dormant : 191 chemins almanac, 69 fish_finder, aucun en commun.
- Champs par défaut inertes dans `package.json` ; cinq vulnérabilités npm transitives dans
  la chaîne d'outils de développement ; un commentaire de `parse-lang.js` cite « 190 clés »
  quand le jar actuel en compte 189.

---

## Hors périmètre, décidé à la conception

Publication en ligne, rendu des icônes d'objets, édition des fichiers de quêtes `.snbt`,
traduction automatique depuis le site.
