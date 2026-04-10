import { afterEach, describe, expect, it } from "vitest";
import { resolveExtensionBuildConfig } from "../../manifest.config";

describe("resolveExtensionBuildConfig", () => {
  afterEach(() => {
    delete process.env.EXTENSION_GOOGLE_CLIENT_ID;
    delete process.env.EXTENSION_PUBLIC_KEY;
    delete process.env.EXTENSION_API_BASE_URL;
    delete process.env.EXTENSION_PRODUCTION_API_BASE_URL;
  });

  it("returns development defaults", () => {
    delete process.env.EXTENSION_PUBLIC_KEY;
    process.env.EXTENSION_GOOGLE_CLIENT_ID =
      "extension-client-id.apps.googleusercontent.com";
    const config = resolveExtensionBuildConfig("development");

    expect(config.env).toBe("development");
    expect(config.apiBaseUrl).toBe("http://localhost:8000");
    expect(config.manifest.name).toBe("Yousum Dev");
    expect(config.manifest.host_permissions).toContain(
      "http://localhost:8000/*",
    );
    expect(config.manifest.action.default_popup).toBe("index.html");
    expect(config.manifest.background.type).toBe("module");
    expect(config.manifest.key).toBeUndefined();
  });

  it("returns production defaults", () => {
    delete process.env.EXTENSION_PUBLIC_KEY;
    process.env.EXTENSION_GOOGLE_CLIENT_ID =
      "extension-client-id.apps.googleusercontent.com";
    process.env.EXTENSION_PRODUCTION_API_BASE_URL = "https://api.yousum.app";
    const config = resolveExtensionBuildConfig("production");

    expect(config.env).toBe("production");
    expect(config.apiBaseUrl).toBe("https://api.yousum.app");
    expect(config.manifest.name).toBe("Yousum");
    expect(config.manifest.host_permissions).toContain(
      "https://api.yousum.app/*",
    );
    expect(config.manifest.background.service_worker).toBe("src/background.js");
    expect(config.manifest.background.type).toBe("module");
    expect(config.manifest.key).toBeUndefined();
  });

  it("includes env-provided extension key and client IDs", () => {
    process.env.EXTENSION_PUBLIC_KEY = "stable-extension-key";
    process.env.EXTENSION_GOOGLE_CLIENT_ID =
      "extension-client-id.apps.googleusercontent.com";
    process.env.EXTENSION_PRODUCTION_API_BASE_URL = "https://api.yousum.app";

    const devConfig = resolveExtensionBuildConfig("development");
    const prodConfig = resolveExtensionBuildConfig("production");

    expect(devConfig.manifest.key).toBe("stable-extension-key");
    expect(devConfig.manifest.oauth2.client_id).toBe(
      "extension-client-id.apps.googleusercontent.com",
    );
    expect(prodConfig.manifest.key).toBe("stable-extension-key");
    expect(prodConfig.manifest.oauth2.client_id).toBe(
      "extension-client-id.apps.googleusercontent.com",
    );
  });

  it("throws when the extension Google client ID is missing", () => {
    expect(() => resolveExtensionBuildConfig("development")).toThrow(
      "EXTENSION_GOOGLE_CLIENT_ID is not set.",
    );
  });

  it("throws when the production API base URL is missing", () => {
    process.env.EXTENSION_GOOGLE_CLIENT_ID =
      "extension-client-id.apps.googleusercontent.com";

    expect(() => resolveExtensionBuildConfig("production")).toThrow(
      "EXTENSION_PRODUCTION_API_BASE_URL or EXTENSION_API_BASE_URL is not set.",
    );
  });
});
