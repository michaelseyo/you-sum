import { API_BASE_URL } from "../config/env";
import type { AuthState, GoogleAuthExchangeResponse } from "../types/runtime";

export const AUTH_STORAGE_KEY = "authState";
const AUTH_EXPIRY_BUFFER_MS = 30_000;

export function getGoogleClientId(): string | undefined {
  return chrome.runtime.getManifest().oauth2?.client_id;
}

export function buildGoogleAuthUrl() {
  const clientId = getGoogleClientId();
  if (!clientId) {
    throw new Error(
      "Set the Google OAuth client ID in manifest.json before signing in.",
    );
  }

  const redirectUri = chrome.identity.getRedirectURL("google");
  const nonce = crypto.randomUUID();
  const state = crypto.randomUUID();
  const params = new URLSearchParams({
    client_id: clientId,
    nonce,
    prompt: "select_account",
    redirect_uri: redirectUri,
    response_type: "id_token",
    scope: "openid email profile",
    state,
  });

  return {
    nonce,
    state,
    url: `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`,
  };
}

export function parseIdTokenFromCallback(
  callbackUrl: string,
  expectedState: string,
) {
  const url = new URL(callbackUrl);
  const fragmentParams = new URLSearchParams(url.hash.slice(1));
  const state = fragmentParams.get("state");

  if (state !== expectedState) {
    throw new Error("Google sign-in state verification failed.");
  }

  const idToken = fragmentParams.get("id_token");

  if (!idToken) {
    throw new Error("Google did not return an ID token.");
  }

  return idToken;
}

export async function exchangeGoogleToken(
  idToken: string,
): Promise<GoogleAuthExchangeResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/google`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ id_token: idToken }),
  });

  const payload = (await response.json().catch(() => ({}))) as
    | GoogleAuthExchangeResponse
    | { detail?: string };

  if (!response.ok) {
    const errorMessage =
      "detail" in payload ? payload.detail : "Google sign-in failed.";
    throw new Error(errorMessage || "Google sign-in failed.");
  }

  return payload as GoogleAuthExchangeResponse;
}

export async function saveAuthState(authState: AuthState) {
  await chrome.storage.local.set({ [AUTH_STORAGE_KEY]: authState });
}

export async function clearAuthState() {
  await chrome.storage.local.remove(AUTH_STORAGE_KEY);
}

export async function getAuthState(): Promise<AuthState | null> {
  const stored = await chrome.storage.local.get(AUTH_STORAGE_KEY);
  const authState = stored[AUTH_STORAGE_KEY] as AuthState | undefined;
  if (!authState) {
    return null;
  }

  if (
    typeof authState.expiresAt !== "number" ||
    authState.expiresAt <= Date.now() + AUTH_EXPIRY_BUFFER_MS
  ) {
    await clearAuthState();
    return null;
  }

  return authState;
}

export async function signIn() {
  const { state, url } = buildGoogleAuthUrl();
  const callbackUrl = await chrome.identity.launchWebAuthFlow({
    interactive: true,
    url,
  });

  if (!callbackUrl) {
    throw new Error("Google sign-in did not return a callback URL.");
  }

  const idToken = parseIdTokenFromCallback(callbackUrl, state);
  const authPayload = await exchangeGoogleToken(idToken);
  const authState = {
    accessToken: authPayload.access_token,
    // The API returns Unix seconds; Date.now() comparisons use milliseconds.
    expiresAt: authPayload.expires_at * 1000,
    user: authPayload.user,
  };

  await saveAuthState(authState);

  return authState;
}
