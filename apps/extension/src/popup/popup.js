const API_BASE_URL = "http://localhost:8000";
const authStatusEl = document.getElementById("auth-status");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const signInButton = document.getElementById("sign-in-button");
const signOutButton = document.getElementById("sign-out-button");
const summarizeButton = document.getElementById("summarize-button");
let authState = null;

function sendRuntimeMessage(type) {
  return chrome.runtime.sendMessage({ type });
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function getVideoContext(tabId) {
  return chrome.tabs.sendMessage(tabId, { type: "GET_VIDEO_CONTEXT" });
}

async function summarizeVideo(videoId) {
  const response = await fetch(`${API_BASE_URL}/summarize`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${authState.accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ video_id: videoId }),
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "API request failed");
  }

  return payload;
}

function renderAuthState() {
  const signedIn = Boolean(authState?.accessToken);
  signInButton.hidden = signedIn;
  signOutButton.hidden = !signedIn;
  summarizeButton.disabled = !signedIn;
  authStatusEl.textContent = signedIn
    ? `Signed in as ${authState.user.email}`
    : "Sign in with Google to use your backend.";
}

async function refreshAuthState() {
  const response = await sendRuntimeMessage("AUTH_GET_STATE");
  if (!response?.ok) {
    throw new Error(response?.error || "Unable to load auth state");
  }

  authState = response.authState;
  renderAuthState();
}

async function signIn() {
  authStatusEl.textContent = "Signing in with Google...";
  const response = await sendRuntimeMessage("AUTH_SIGN_IN");
  if (!response?.ok) {
    throw new Error(response?.error || "Sign-in failed");
  }

  authState = response.authState;
  renderAuthState();
}

async function signOut() {
  const response = await sendRuntimeMessage("AUTH_SIGN_OUT");
  if (!response?.ok) {
    throw new Error(response?.error || "Sign-out failed");
  }

  authState = null;
  renderAuthState();
  resultEl.textContent = "No summary yet.";
  statusEl.textContent = "Ready to summarize the current video.";
}

summarizeButton.addEventListener("click", async () => {
  if (!authState?.accessToken) {
    statusEl.textContent = "Sign in before summarizing.";
    return;
  }

  statusEl.textContent = "Reading current tab...";
  resultEl.textContent = "Loading...";

  try {
    const tab = await getActiveTab();

    if (!tab?.id) {
      throw new Error("No active tab found");
    }

    const context = await getVideoContext(tab.id);

    if (!context?.videoId) {
      throw new Error("Open a YouTube video first");
    }

    statusEl.textContent = `Summarizing ${context.videoId}...`;
    const data = await summarizeVideo(context.videoId);

    resultEl.textContent = data.summary;
    statusEl.textContent = "Summary loaded";
  } catch (error) {
    statusEl.textContent = "Unable to summarize video";
    resultEl.textContent = error.message;
  }
});

signInButton.addEventListener("click", async () => {
  try {
    await signIn();
  } catch (error) {
    authStatusEl.textContent = error.message;
  }
});

signOutButton.addEventListener("click", async () => {
  try {
    await signOut();
  } catch (error) {
    authStatusEl.textContent = error.message;
  }
});

refreshAuthState().catch((error) => {
  authStatusEl.textContent = error.message;
  renderAuthState();
});
