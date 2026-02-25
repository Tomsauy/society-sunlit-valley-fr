# Contribuer aux traductions

Merci de votre interet pour la traduction francaise de Society: Sunlit Valley !

## Comment contribuer

### 1. Fork et branche

1. Forkez ce repo
2. Creez une branche depuis `main` (ex: `trad/nom-du-mod` ou `fix/correction-description`)
3. Faites vos modifications
4. Ouvrez une Pull Request vers `main`

### 2. Conventions de traduction

- **Vouvoiement** : tous les dialogues PNJ vers le joueur utilisent le vouvoiement
- **Typographie francaise** : espace insecable avant `!`, `?`, `:`, `;`
- **Noms propres** : ne pas traduire les noms de PNJ, lieux du jeu, noms de mods
- **Glossaire** : respecter les termes etablis (voir ci-dessous)
- **Structure JSON** : conserver les memes cles et le meme ordre que le fichier EN source
- **Marqueurs** : preserver tous les marqueurs techniques (`@i`, `%s`, `%d`, codes `§`)

### 3. Termes standardises (extrait du glossaire)

| Anglais | Francais |
|---------|----------|
| Coin / Spur / Crown | Piece / Eperon / Couronne (monnaie) |
| Shipping Bin | Bac d'expedition |
| Skull Cavern | Caverne du Crane |
| Quest | Quete |
| Crop | Culture |
| Livestock | Betail |

Le glossaire complet est maintenu par les mainteneurs du projet.

### 4. Qualite attendue

- Traductions fideles au texte anglais original
- Francais naturel et soigne (pas de traduction automatique)
- Ton adapte au personnage/contexte
- Relecture avant soumission

## Structure des fichiers

```
kubejs/assets/MODID/lang/fr_fr.json    # Traductions mods
patchouli_books/almanac/fr_fr/          # Guide Almanac
patchouli_books/fish_finder/fr_fr/      # Guide Fish Finder
```

## Processus de review

1. Ouvrez votre PR avec une description claire de ce qui est traduit/corrige
2. Un mainteneur relira la traduction
3. Des corrections peuvent etre demandees
4. Une fois approuvee, la PR est mergee dans `main`

## Signaler un probleme

- **Erreur de traduction** : ouvrez une issue avec le template "Erreur de traduction"
- **Traduction manquante** : ouvrez une issue avec le template "Traduction manquante"

## Code de conduite

Soyez respectueux et constructif dans vos echanges. Nous sommes tous la pour ameliorer l'experience de jeu en francais.
