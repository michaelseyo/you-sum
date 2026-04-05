export type ExtensionEnv = "development" | "production";

export const PRODUCTION_API_FALLBACK_URL = "https://api.yousum.app";

const DEFAULT_GOOGLE_CLIENT_ID =
  "253061236495-p8hohm7sna23d0fc8pgkut5c3mornbas.apps.googleusercontent.com";

type ExtensionManifest = {
  action: {
    default_icon: Record<string, string>;
    default_popup: string;
    default_title: string;
  };
  background: {
    service_worker: string;
  };
  content_scripts: Array<{
    js: string[];
    matches: string[];
  }>;
  description: string;
  host_permissions: string[];
  icons: Record<string, string>;
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

  return (
    process.env.EXTENSION_PRODUCTION_API_BASE_URL ||
    process.env.EXTENSION_API_BASE_URL ||
    PRODUCTION_API_FALLBACK_URL
  );
}

function resolveGoogleClientId(env: ExtensionEnv): string {
  if (env === "development") {
    return process.env.EXTENSION_DEV_GOOGLE_CLIENT_ID || DEFAULT_GOOGLE_CLIENT_ID;
  }

  return (
    process.env.EXTENSION_PRODUCTION_GOOGLE_CLIENT_ID ||
    process.env.EXTENSION_GOOGLE_CLIENT_ID ||
    DEFAULT_GOOGLE_CLIENT_ID
  );
}

function toHostPermission(apiBaseUrl: string): string {
  const normalizedOrigin = new URL(apiBaseUrl).origin;
  return `${normalizedOrigin}/*`;
}

export function resolveExtensionBuildConfig(mode: string): ExtensionBuildConfig {
  const env = resolveEnv(mode);
  const apiBaseUrl = resolveApiBaseUrl(env);
  const googleClientId = resolveGoogleClientId(env);
  const extensionName = env === "production" ? "Yousum" : "Yousum Dev";

  return {
    apiBaseUrl,
    env,
    manifest: {
      manifest_version: 3,
      name: extensionName,
      version: "0.1.0",
      description: "Summarize the current YouTube video.",
      permissions: ["activeTab", "identity", "storage"],
      host_permissions: ["https://www.youtube.com/*", toHostPermission(apiBaseUrl)],
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
