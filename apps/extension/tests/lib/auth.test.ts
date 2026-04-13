import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  AUTH_STORAGE_KEY,
  getAuthState,
  signIn,
} from "../../src/lib/auth.ts";

const storageState: Record<string, unknown> = {};

function installChromeMock() {
  vi.stubGlobal("chrome", {
    identity: {
      getRedirectURL: vi.fn(() => "https://extension.example/google"),
      launchWebAuthFlow: vi.fn(async () => {
        return "https://extension.example/google#state=state-value&id_token=google-token";
      }),
    },
    runtime: {
      getManifest: vi.fn(() => ({
        oauth2: {
          client_id: "client-id.apps.googleusercontent.com",
        },
      })),
    },
    storage: {
      local: {
        get: vi.fn(async (key: string) => ({
          [key]: storageState[key],
        })),
        remove: vi.fn(async (key: string) => {
          delete storageState[key];
        }),
        set: vi.fn(async (items: Record<string, unknown>) => {
          Object.assign(storageState, items);
        }),
      },
    },
  });
}

describe("auth storage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    for (const key of Object.keys(storageState)) {
      delete storageState[key];
    }
    installChromeMock();
  });

  it("stores the backend token expiry when signing in", async () => {
    vi.spyOn(crypto, "randomUUID")
      .mockReturnValueOnce("nonce-value")
      .mockReturnValueOnce("state-value");
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        return new Response(
          JSON.stringify({
            access_token: "app-token",
            expires_at: 1776071234,
            token_type: "bearer",
            user: {
              email: "user@example.com",
            },
          }),
          {
            headers: {
              "Content-Type": "application/json",
            },
            status: 200,
          },
        );
      }),
    );

    const authState = await signIn();

    expect(authState.expiresAt).toBe(1776071234000);
    expect(storageState[AUTH_STORAGE_KEY]).toEqual(authState);
  });

  it("removes expired stored auth state", async () => {
    storageState[AUTH_STORAGE_KEY] = {
      accessToken: "expired-token",
      expiresAt: Date.now() - 1,
      user: {
        email: "user@example.com",
      },
    };

    await expect(getAuthState()).resolves.toBeNull();

    expect(chrome.storage.local.remove).toHaveBeenCalledWith(AUTH_STORAGE_KEY);
    expect(storageState[AUTH_STORAGE_KEY]).toBeUndefined();
  });

  it("removes legacy auth state without an expiry", async () => {
    storageState[AUTH_STORAGE_KEY] = {
      accessToken: "legacy-token",
      user: {
        email: "user@example.com",
      },
    };

    await expect(getAuthState()).resolves.toBeNull();

    expect(chrome.storage.local.remove).toHaveBeenCalledWith(AUTH_STORAGE_KEY);
    expect(storageState[AUTH_STORAGE_KEY]).toBeUndefined();
  });
});
