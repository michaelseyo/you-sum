import { describe, expect, it } from "vitest";
import {
  PRODUCTION_API_FALLBACK_URL,
  resolveExtensionBuildConfig,
} from "../../manifest.config";

describe("resolveExtensionBuildConfig", () => {
  it("returns development defaults", () => {
    const config = resolveExtensionBuildConfig("development");

    expect(config.env).toBe("development");
    expect(config.apiBaseUrl).toBe("http://localhost:8000");
    expect(config.manifest.name).toBe("Yousum Dev");
    expect(config.manifest.host_permissions).toContain("http://localhost:8000/*");
    expect(config.manifest.action.default_popup).toBe("index.html");
  });

  it("returns production defaults", () => {
    const config = resolveExtensionBuildConfig("production");

    expect(config.env).toBe("production");
    expect(config.apiBaseUrl).toBe(PRODUCTION_API_FALLBACK_URL);
    expect(config.manifest.name).toBe("Yousum");
    expect(config.manifest.host_permissions).toContain(
      `${PRODUCTION_API_FALLBACK_URL}/*`,
    );
    expect(config.manifest.background.service_worker).toBe("src/background.js");
  });
});
