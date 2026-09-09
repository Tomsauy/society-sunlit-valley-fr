# Décision accents (spec §Phase 1.5)

- Version EMI inspectée : `emi-1.1.24+1.20.1+forge.jar`
- Méthode : scan binaire des constantes de toutes les classes du JAR (recherche de
  `java/text/Normalizer`, `NFKD`, `NFD`), en particulier `dev/emi/emi/search/*`
  (NameQuery, EmiSearch, etc.)
- Résultat : **aucune normalisation Unicode trouvée** — la recherche EMI compare les noms
  sans plier les diacritiques ; taper « ble » ne matche pas « Blé »
- Décision : politique hybride (validée par l'utilisateur au brainstorming)
  - accent_free_prefixes = ["item.", "block.", "entity."]
  - Les valeurs des clés `item.*`, `block.*`, `entity.*` sont écrites SANS accents
    (recherche fiable en jeu)
  - Tout le reste (quêtes, tooltips, descriptions, interface, livres Patchouli) est en
    français correctement accentué

## Révision du 29/08/2026 — la contrainte semblait levable

EMI accepte des **alias de recherche** déclarés dans `assets/emi/aliases/*.json`, dont le
champ `text` est une clé de langue. `EmiSearch$CompiledQuery` ajoute `AliasQuery` sans
aucun test de configuration puis l'unit à `NameQuery` par un `LogicalOrQuery` : les alias
comptent dans la recherche par défaut, sans préfixe à taper. Vérifié en jeu.

Les 11 144 noms ont donc été réaccentués. 3 214 mots jugés par dix agents voyant les
occurrences réelles et sept langues témoins, arbitrés par un onzième ; 637 mots accentués,
16 à double sens (`séché`/`sèche`, `sale`/`salé`, `mur`/`mûr`).

## Retour arrière du 09/09/2026 — Refined Storage n'a pas d'alias

Essai en jeu : la recherche du grid de craft de Refined Storage filtre les accents. Lecture
du bytecode de la 1.12.4 :

- `NameGridFilter` fait `getHoverName().toLowerCase().contains(requête)` — ni `Normalizer`,
  ni `Collator`, comme EMI.
- **Aucun système d'alias dans le mod** — le mot n'apparaît nulle part.
- Les préfixes existent (`@` mod, `#` tag, `$` infobulle, `|` OU) mais une requête **sans
  préfixe ne construit qu'un `NameGridFilter`**, jamais une union. C'est toute la
  différence avec EMI.
- Les « modes » de la barre ne concernent que l'auto-sélection et la synchronisation JEI.
- L'infobulle passe par `ItemStack.getTooltipLines`, donc une ligne ajoutée par KubeJS y
  serait visible — mais seulement avec le préfixe `$`.

Mesures qui ont pesé : 42 % des noms étaient accentués ; 95 % offraient un mot entier sans
accent (« morue » trouve « Ragoût de morue »), mais 222 n'en offraient aucun. Et 2 989 noms
restent accentués quoi qu'on fasse, venant du français embarqué des mods.

**Décision : retour aux noms sans accents.** Les alias EMI sont conservés pour ces 2 939
noms de mods. Le chantier est archivé — branche `chantier-accents` (dépôt racine) et
`accents-noms` (clone du pack), vocabulaire complet dans `fr-workspace/accents/`.

**Si la question revient :** le correctif propre est en amont, un appel à `Normalizer` dans
le `NameGridFilter` de Refined Storage. Il réglerait toutes les langues à accents d'un coup.
