import { normalizeEnv } from "./src/lib/env-utils";

export type ExtensionMode = "development" | "production";

export type ExtensionBuildConfig = {
  apiBaseUrl: string;
  manifest: chrome.runtime.ManifestV3;
};

type ExtensionConfigEnv = Partial<
  Record<
    | "EXTENSION_DEV_API_BASE_URL"
    | "EXTENSION_PRODUCTION_API_BASE_URL"
    | "EXTENSION_GOOGLE_CLIENT_ID"
    | "EXTENSION_PUBLIC_KEY",
    string | undefined
  >
>;

function resolveMode(mode: string): ExtensionMode {
  return mode === "production" ? "production" : "development";
}

function readExtensionEnv(
  key: keyof ExtensionConfigEnv,
  loadedEnv: ExtensionConfigEnv,
): string | undefined {
  const processEnvValue = normalizeEnv(process.env[key]);
  return processEnvValue ?? normalizeEnv(loadedEnv[key]);
}

function resolveApiBaseUrl(
  mode: ExtensionMode,
  loadedEnv: ExtensionConfigEnv,
): string {
  if (mode === "development") {
    return (
      readExtensionEnv("EXTENSION_DEV_API_BASE_URL", loadedEnv) ||
      "http://localhost:8000"
    );
  }

  const apiBaseUrl = readExtensionEnv(
    "EXTENSION_PRODUCTION_API_BASE_URL",
    loadedEnv,
  );

  if (!apiBaseUrl) {
    throw new Error("EXTENSION_PRODUCTION_API_BASE_URL is not set.");
  }

  return apiBaseUrl;
}

function resolveGoogleClientId(
  mode: ExtensionMode,
  loadedEnv: ExtensionConfigEnv,
): string {
  void mode;
  const clientId = readExtensionEnv("EXTENSION_GOOGLE_CLIENT_ID", loadedEnv);
  if (!clientId) {
    throw new Error("EXTENSION_GOOGLE_CLIENT_ID is not set.");
  }

  return clientId;
}

// for extension id consistency
function resolveExtensionKey(
  loadedEnv: ExtensionConfigEnv,
): string | undefined {
  const extensionPublicKey = readExtensionEnv(
    "EXTENSION_PUBLIC_KEY",
    loadedEnv,
  );
  if (!extensionPublicKey) {
    throw new Error("EXTENSION_PUBLIC_KEY is not set.");
  }
  return extensionPublicKey;
}

function toHostPermission(apiBaseUrl: string): string {
  const normalizedOrigin = new URL(apiBaseUrl).origin;
  return `${normalizedOrigin}/*`;
}

export function resolveExtensionBuildConfig(
  mode: string,
  loadedEnv: ExtensionConfigEnv = {},
): ExtensionBuildConfig {
  const resolvedMode = resolveMode(mode);
  const apiBaseUrl = resolveApiBaseUrl(resolvedMode, loadedEnv);
  const googleClientId = resolveGoogleClientId(resolvedMode, loadedEnv);
  const extensionKey = resolveExtensionKey(loadedEnv);
  const extensionName = resolvedMode === "production" ? "Yousum" : "Yousum Dev";

  return {
    apiBaseUrl,
    manifest: {
      manifest_version: 3,
      ...(extensionKey ? { key: extensionKey } : {}),
      name: extensionName,
      version: "0.1.0",
      description: "Summarize the current YouTube video.",
      permissions: ["activeTab", "identity", "storage", "sidePanel"],
      host_permissions: [
        "https://www.youtube.com/*",
        toHostPermission(apiBaseUrl),
      ],
      oauth2: {
        client_id: googleClientId,
        scopes: ["openid", "email", "profile"],
      },
      action: {
        default_icon: {
          "16": "assets/icon-16.png",
          "32": "assets/icon-32.png",
        },
        default_title: extensionName,
        default_popup: "index.html",
      },
      side_panel: {
        default_path: "index.html",
      },
      icons: {
        "16": "assets/icon-16.png",
        "32": "assets/icon-32.png",
        "48": "assets/icon-48.png",
        "128": "assets/icon-128.png",
      },
      background: {
        service_worker: "src/background.js",
        type: "module",
      },
      content_scripts: [
        {
          matches: ["https://www.youtube.com/watch*"],
          js: ["src/content.js"],
        },
      ],
    },
  };
}
