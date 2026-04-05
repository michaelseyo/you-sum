import {
  clearAuthState,
  getAuthState,
  signIn,
} from "./lib/auth";
import type { RuntimeMessage } from "./types/runtime";

chrome.runtime.onInstalled.addListener(() => {
  console.log("You Sum extension installed");
});

chrome.runtime.onMessage.addListener(
  (message: RuntimeMessage, _sender, sendResponse) => {
    if (message.type === "AUTH_GET_STATE") {
      getAuthState()
        .then((authState) => sendResponse({ ok: true, authState }))
        .catch((error: unknown) =>
          sendResponse({
            error:
              error instanceof Error ? error.message : "Unable to load auth state",
            ok: false,
          }),
        );
      return true;
    }

    if (message.type === "AUTH_SIGN_IN") {
      signIn()
        .then((authState) => sendResponse({ ok: true, authState }))
        .catch((error: unknown) =>
          sendResponse({
            error: error instanceof Error ? error.message : "Sign-in failed",
            ok: false,
          }),
        );
      return true;
    }

    if (message.type === "AUTH_SIGN_OUT") {
      clearAuthState()
        .then(() => sendResponse({ ok: true }))
        .catch((error: unknown) =>
          sendResponse({
            error: error instanceof Error ? error.message : "Sign-out failed",
            ok: false,
          }),
        );
      return true;
    }

    return false;
  },
);
