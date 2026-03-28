const API_BASE_URL = "http://localhost:8000";
const AUTH_STORAGE_KEY = "authState";

chrome.runtime.onInstalled.addListener(() => {
  console.log("You Sum extension installed");
});

function getGoogleClientId() {
  return chrome.runtime.getManifest().oauth2?.client_id;
}

function buildGoogleAuthUrl() {
  const clientId = getGoogleClientId();
  if (!clientId) {
    throw new Error(
      "Set the Google OAuth client ID in manifest.json before signing in.",
    );
  }

  // Chrome generates an extension-owned callback URL that Google redirects back to
  const redirectUri = chrome.identity.getRedirectURL("google");
  // nonce and state are standard OIDC values used to guard against replay and callback mixups
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

function parseIdTokenFromCallback(callbackUrl, expectedState) {
  const url = new URL(callbackUrl);
  // Google returns the ID token in the redirect URL fragment for this flow
  // slice(1) removes the leading # so URLSearchParams can parse the fragment values
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

async function exchangeGoogleToken(idToken) {
  // Exchange the Google ID token for the app's own backend JWT
  const response = await fetch(`${API_BASE_URL}/auth/google`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ id_token: idToken }),
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "Google sign-in failed.");
  }

  return payload;
}

async function saveAuthState(authState) {
  await chrome.storage.local.set({ [AUTH_STORAGE_KEY]: authState });
}

async function clearAuthState() {
  await chrome.storage.local.remove(AUTH_STORAGE_KEY);
}

async function getAuthState() {
  const stored = await chrome.storage.local.get(AUTH_STORAGE_KEY);
  return stored[AUTH_STORAGE_KEY] || null;
}

async function signIn() {
  const { state, url } = buildGoogleAuthUrl();
  // launchWebAuthFlow opens the Google sign-in page and resolves with the final callback URL
  const callbackUrl = await chrome.identity.launchWebAuthFlow({
    interactive: true,
    url,
  });
  const idToken = parseIdTokenFromCallback(callbackUrl, state);
  const authPayload = await exchangeGoogleToken(idToken);
  const authState = {
    accessToken: authPayload.access_token,
    user: authPayload.user,
  };
  await saveAuthState(authState);
  return authState;
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  // The popup asks the background worker to manage auth so token state survives popup reopen
  if (message?.type === "AUTH_GET_STATE") {
    getAuthState()
      .then((authState) => sendResponse({ ok: true, authState }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));
    return true;
  }

  if (message?.type === "AUTH_SIGN_IN") {
    signIn()
      .then((authState) => sendResponse({ ok: true, authState }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));
    return true;
  }

  if (message?.type === "AUTH_SIGN_OUT") {
    clearAuthState()
      .then(() => sendResponse({ ok: true }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));
    return true;
  }

  return false;
});
