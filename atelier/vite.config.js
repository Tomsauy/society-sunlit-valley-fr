import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { apiPlugin } from "./server/api.js";
export default defineConfig({ plugins: [svelte(), apiPlugin()], server: { port: 5180 } });
