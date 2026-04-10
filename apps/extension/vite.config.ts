import { dirname } from "node:path";
import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import type { ConfigEnv, Plugin } from "vite";
import { loadEnv } from "vite";
import { viteStaticCopy } from "vite-plugin-static-copy";
import { defineConfig } from "vitest/config";
import { resolveExtensionBuildConfig } from "./manifest.config";

const currentDir = dirname(fileURLToPath(import.meta.url));

function generateManifestFile(manifest: object): Plugin {
  return {
    generateBundle() {
      this.emitFile({
        fileName: "manifest.json",
        source: `${JSON.stringify(manifest, null, 2)}\n`,
        type: "asset",
      });
    },
    name: "generate-extension-manifest",
  };
}

export default defineConfig((configEnv: ConfigEnv) => {
  const loadedEnv = loadEnv(configEnv.mode, currentDir, "");

  // Override environment variables with loaded values
  process.env.EXTENSION_PUBLIC_KEY =
    process.env.EXTENSION_PUBLIC_KEY || loadedEnv.EXTENSION_PUBLIC_KEY;
  process.env.EXTENSION_GOOGLE_CLIENT_ID =
    process.env.EXTENSION_GOOGLE_CLIENT_ID ||
    loadedEnv.EXTENSION_GOOGLE_CLIENT_ID;
  process.env.EXTENSION_API_BASE_URL =
    process.env.EXTENSION_API_BASE_URL || loadedEnv.EXTENSION_API_BASE_URL;
  process.env.EXTENSION_DEV_API_BASE_URL =
    process.env.EXTENSION_DEV_API_BASE_URL ||
    loadedEnv.EXTENSION_DEV_API_BASE_URL;
  process.env.EXTENSION_PRODUCTION_API_BASE_URL =
    process.env.EXTENSION_PRODUCTION_API_BASE_URL ||
    loadedEnv.EXTENSION_PRODUCTION_API_BASE_URL;

  const extensionBuildConfig = resolveExtensionBuildConfig(configEnv.mode);

  return {
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
    define: {
      __API_BASE_URL__: JSON.stringify(extensionBuildConfig.apiBaseUrl),
    },
    plugins: [
      react(),
      ...viteStaticCopy({
        targets: [{ src: "assets/*", dest: "assets" }],
      }),
      generateManifestFile(extensionBuildConfig.manifest),
    ],
    publicDir: false,
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: [],
    },
  };
});
