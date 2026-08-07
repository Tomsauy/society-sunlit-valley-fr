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
