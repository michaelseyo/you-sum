import { afterEach, describe, expect, it } from "vitest";
import { resolveExtensionBuildConfig } from "../../manifest.config";

describe("resolveExtensionBuildConfig", () => {
  afterEach(() => {
    delete process.env.EXTENSION_GOOGLE_CLIENT_ID;
    delete process.env.EXTENSION_PUBLIC_KEY;
    delete process.env.EXTENSION_DEV_API_BASE_URL;
    delete process.env.EXTENSION_PRODUCTION_API_BASE_URL;
  });

  it("returns development defaults", () => {
    process.env.EXTENSION_PUBLIC_KEY = "stable-extension-key";
    process.env.EXTENSION_GOOGLE_CLIENT_ID =
      "extension-client-id.apps.googleusercontent.com";
    const config = resolveExtensionBuildConfig("development");

    expect(config.apiBaseUrl).toBe("http://localhost:8000");
    expect(config.manifest.name).toBe("Yousum Dev");
    expect(config.manifest.host_permissions).toContain(
      "http://localhost:8000/*",
    );
    expect(config.manifest.action.default_popup).toBe("index.html");
    expect(config.manifest.background.type).toBe("module");
    expect(config.manifest.key).toBe("stable-extension-key");
    expect(config.manifest.permissions).toContain("sidePanel");
    expect(config.manifest.side_panel.default_path).toBe("index.html");
    expect(config.manifest.oauth2.client_id).toBe(
      "extension-client-id.apps.googleusercontent.com",
    );
  });

  it("returns production defaults", () => {
    process.env.EXTENSION_PUBLIC_KEY = "stable-extension-key";
    process.env.EXTENSION_GOOGLE_CLIENT_ID =
      "extension-client-id.apps.googleusercontent.com";
    process.env.EXTENSION_PRODUCTION_API_BASE_URL = "https://api.yousum.app";
    const config = resolveExtensionBuildConfig("production");

    expect(config.apiBaseUrl).toBe("https://api.yousum.app");
    expect(config.manifest.name).toBe("Yousum");
    expect(config.manifest.host_permissions).toContain(
      "https://api.yousum.app/*",
    );
    expect(config.manifest.background.service_worker).toBe("src/background.js");
    expect(config.manifest.background.type).toBe("module");
    expect(config.manifest.key).toBe("stable-extension-key");
    expect(config.manifest.oauth2.client_id).toBe(
      "extension-client-id.apps.googleusercontent.com",
    );
  });

  it("uses the development fallback when EXTENSION_DEV_API_BASE_URL is undefined", () => {
    process.env.EXTENSION_PUBLIC_KEY = "stable-extension-key";
    process.env.EXTENSION_GOOGLE_CLIENT_ID =
      "extension-client-id.apps.googleusercontent.com";
    process.env.EXTENSION_DEV_API_BASE_URL = undefined;

    const config = resolveExtensionBuildConfig("development");

    expect(config.apiBaseUrl).toBe("http://localhost:8000");
    expect(config.manifest.host_permissions).toContain(
      "http://localhost:8000/*",
    );
  });

  it('uses loaded env values and ignores weird "undefined" env strings', () => {
    process.env.EXTENSION_GOOGLE_CLIENT_ID = "undefined";
    process.env.EXTENSION_PUBLIC_KEY = "   ";

    const config = resolveExtensionBuildConfig("development", {
      EXTENSION_DEV_API_BASE_URL: "http://localhost:9000",
      EXTENSION_GOOGLE_CLIENT_ID:
        "extension-client-id.apps.googleusercontent.com",
      EXTENSION_PUBLIC_KEY: "stable-extension-key",
    });

    expect(config.apiBaseUrl).toBe("http://localhost:9000");
    expect(config.manifest.oauth2.client_id).toBe(
      "extension-client-id.apps.googleusercontent.com",
    );
    expect(config.manifest.key).toBe("stable-extension-key");
    expect(config.manifest.host_permissions).toContain(
      "http://localhost:9000/*",
    );
  });

  it("throws when the extension Google client ID is missing", () => {
    expect(() => resolveExtensionBuildConfig("development")).toThrow(
      "EXTENSION_GOOGLE_CLIENT_ID is not set.",
    );
  });

  it("throws when the extension public key is missing", () => {
    process.env.EXTENSION_GOOGLE_CLIENT_ID =
      "extension-client-id.apps.googleusercontent.com";

    expect(() => resolveExtensionBuildConfig("development")).toThrow(
      "EXTENSION_PUBLIC_KEY is not set.",
    );
  });

  it("throws when the production API base URL is missing", () => {
    process.env.EXTENSION_PUBLIC_KEY = "stable-extension-key";
    process.env.EXTENSION_GOOGLE_CLIENT_ID =
      "extension-client-id.apps.googleusercontent.com";

    expect(() => resolveExtensionBuildConfig("production")).toThrow(
      "EXTENSION_PRODUCTION_API_BASE_URL is not set.",
    );
  });
});
