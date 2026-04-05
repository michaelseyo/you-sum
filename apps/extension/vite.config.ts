import { dirname } from "node:path";
import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { viteStaticCopy } from "vite-plugin-static-copy";
import { defineConfig } from "vitest/config";

const currentDir = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  build: {
    assetsDir: "assets",
    emptyOutDir: true,
    outDir: "dist",
    rollupOptions: {
      input: {
        popup: path.resolve(currentDir, "index.html"),
        background: path.resolve(currentDir, "src/background.ts"),
        content: path.resolve(currentDir, "src/content.ts"),
      },
      output: {
        assetFileNames: "assets/[name][extname]",
        chunkFileNames: "assets/[name].js",
        entryFileNames: (chunkInfo) => {
          if (chunkInfo.name === "background") {
            return "src/background.js";
          }

          if (chunkInfo.name === "content") {
            return "src/content.js";
          }

          return "assets/[name].js";
        },
      },
    },
  },
  plugins: [
    react(),
    viteStaticCopy({
      targets: [{ src: "assets/*", dest: "assets" }],
    }),
  ],
  publicDir: false,
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: [],
  },
});
