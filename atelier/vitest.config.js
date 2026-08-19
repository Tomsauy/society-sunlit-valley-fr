import { defineConfig } from "vitest/config";

// Vitest préfère automatiquement ce fichier à vite.config.js dès qu'il existe, et ignore
// alors ce dernier : le greffon apiPlugin() (et donc l'observateur fs.watch) n'est jamais
// chargé pendant les tests. Ainsi l'observateur reste inconditionnel dans api.js — on évite
// de faire piloter du code applicatif par une variable d'environnement propre à l'outil de test.
export default defineConfig({ test: {} });
