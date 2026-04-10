export type ExtensionEnv = "development" | "production";

type ExtensionManifest = {
  action: {
    default_icon: Record<string, string>;
    default_popup: string;
    default_title: string;
  };
  background: {
    service_worker: string;
    type: "module";
  };
  content_scripts: Array<{
    js: string[];
    matches: string[];
  }>;
  description: string;
  host_permissions: string[];
  icons: Record<string, string>;
  key?: string;
  manifest_version: 3;
  name: string;
  oauth2: {
    client_id: string;
    scopes: string[];
  };
  permissions: string[];
  version: string;
};

export type ExtensionBuildConfig = {
  apiBaseUrl: string;
  env: ExtensionEnv;
  manifest: ExtensionManifest;
};

function resolveEnv(mode: string): ExtensionEnv {
  return mode === "production" ? "production" : "development";
}

function resolveApiBaseUrl(env: ExtensionEnv): string {
  if (env === "development") {
    return process.env.EXTENSION_DEV_API_BASE_URL || "http://localhost:8000";
  }

  const apiBaseUrl =
    process.env.EXTENSION_PRODUCTION_API_BASE_URL ||
    process.env.EXTENSION_API_BASE_URL;

  if (!apiBaseUrl) {
    throw new Error(
      "EXTENSION_PRODUCTION_API_BASE_URL or EXTENSION_API_BASE_URL is not set.",
    );
  }

  return apiBaseUrl;
}

function resolveGoogleClientId(env: ExtensionEnv): string {
  void env;
  const clientId = process.env.EXTENSION_GOOGLE_CLIENT_ID?.trim();

  if (!clientId) {
    throw new Error("EXTENSION_GOOGLE_CLIENT_ID is not set.");
  }

  return clientId;
}

// for extension id consistency
function resolveExtensionKey(): string | undefined {
  return process.env.EXTENSION_PUBLIC_KEY;
}

function toHostPermission(apiBaseUrl: string): string {
  const normalizedOrigin = new URL(apiBaseUrl).origin;
  return `${normalizedOrigin}/*`;
}

export function resolveExtensionBuildConfig(
  mode: string,
): ExtensionBuildConfig {
  const env = resolveEnv(mode);
  const apiBaseUrl = resolveApiBaseUrl(env);
  const googleClientId = resolveGoogleClientId(env);
  const extensionKey = resolveExtensionKey();
  const extensionName = env === "production" ? "Yousum" : "Yousum Dev";

  return {
    apiBaseUrl,
    env,
    manifest: {
      manifest_version: 3,
      ...(extensionKey ? { key: extensionKey } : {}),
      name: extensionName,
      version: "0.1.0",
      description: "Summarize the current YouTube video.",
      permissions: ["activeTab", "identity", "storage"],
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
