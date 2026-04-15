import { useEffect, useRef, useState } from "react";
import { summarizeVideoStream } from "../lib/api";
import {
  getActiveTab,
  getVideoContext,
  sendRuntimeMessage,
} from "../lib/chrome";
import type { AuthState } from "../types/runtime";

export function App() {
  const [authState, setAuthState] = useState<AuthState | null>(null);
  const [authStatus, setAuthStatus] = useState(
    "Sign in with Google to use your backend.",
  );
  const [status, setStatus] = useState("Ready to summarize the current video.");
  const [result, setResult] = useState("No summary yet.");
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [isSigningOut, setIsSigningOut] = useState(false);
  const summarizeAttemptRef = useRef(0);
  const streamAbortRef = useRef<AbortController | null>(null);

  const signedIn = Boolean(authState?.accessToken);

  useEffect(() => {
    async function refreshAuthState() {
      const response = await sendRuntimeMessage({ type: "AUTH_GET_STATE" });
      if (!response.ok) {
        throw new Error(response.error || "Unable to load auth state");
      }

      setAuthState(response.authState);
      setAuthStatus(
        response.authState?.accessToken
          ? `Signed in as ${response.authState.user.email}`
          : "Sign in with Google to use your backend.",
      );
    }

    refreshAuthState().catch((error: unknown) => {
      const message =
        error instanceof Error ? error.message : "Unable to load auth state";
      setAuthStatus(message);
      setAuthState(null);
    });

    return () => {
      streamAbortRef.current?.abort();
    };
  }, []);

  async function handleSignIn() {
    try {
      setAuthStatus("Signing in with Google...");
      const response = await sendRuntimeMessage({ type: "AUTH_SIGN_IN" });
      if (!response.ok) {
        throw new Error(response.error || "Sign-in failed");
      }
      if (!response.authState) {
        throw new Error("Sign-in did not return an auth state");
      }

      setAuthState(response.authState);
      setAuthStatus(`Signed in as ${response.authState.user.email}`);
    } catch (error: unknown) {
      setAuthStatus(error instanceof Error ? error.message : "Sign-in failed");
    }
  }

  async function handleSignOut() {
    try {
      summarizeAttemptRef.current += 1;
      streamAbortRef.current?.abort();
      setIsSigningOut(true);
      setIsSummarizing(false);
      const response = await sendRuntimeMessage({ type: "AUTH_SIGN_OUT" });
      if (!response.ok) {
        throw new Error(response.error || "Sign-out failed");
      }

      setAuthState(null);
      setAuthStatus("Sign in with Google to use your backend.");
      setStatus("Ready to summarize the current video.");
      setResult("No summary yet.");
    } catch (error: unknown) {
      setAuthStatus(error instanceof Error ? error.message : "Sign-out failed");
    } finally {
      setIsSigningOut(false);
    }
  }

  async function handleSummarize() {
    if (!authState?.accessToken) {
      setStatus("Sign in before summarizing.");
      return;
    }
    if (isSigningOut) {
      return;
    }
    if (isSummarizing) {
      return;
    }

    const attemptId = summarizeAttemptRef.current + 1;
    summarizeAttemptRef.current = attemptId;
    streamAbortRef.current?.abort();
    const abortController = new AbortController();
    streamAbortRef.current = abortController;
    setIsSummarizing(true);
    setStatus("Reading current tab...");
    setResult("Loading...");
    let receivedText = false;

    try {
      const tab = await getActiveTab();

      if (!tab?.id) {
        throw new Error("No active tab found");
      }

      const context = await getVideoContext(tab.id);

      if (!context.videoId) {
        throw new Error("Open a YouTube video first");
      }

      setStatus(`Summarizing ${context.videoId}...`);
      setResult("");
      await summarizeVideoStream(
        context.videoId,
        authState.accessToken,
        (event) => {
          if (summarizeAttemptRef.current !== attemptId) {
            return;
          }

          if (event.type === "status") {
            setStatus(event.message);
            return;
          }

          if (event.type === "delta") {
            receivedText = true;
            setResult((current) => current + event.text);
            return;
          }

          if (event.type === "done") {
            setStatus(event.cached ? "Cached summary loaded" : "Summary loaded");
            return;
          }

          if (event.type === "error") {
            setStatus("Unable to summarize video");
          }
        },
        abortController.signal,
      );
    } catch (error: unknown) {
      if (summarizeAttemptRef.current !== attemptId) {
        return;
      }
      setStatus("Unable to summarize video");
      if (!receivedText) {
        setResult(
          error instanceof Error ? error.message : "Unable to summarize video",
        );
      }
    } finally {
      if (summarizeAttemptRef.current === attemptId) {
        setIsSummarizing(false);
      }
      if (streamAbortRef.current === abortController) {
        streamAbortRef.current = null;
      }
    }
  }

  return (
    <main className="popup">
      <h1>Yousum</h1>
      <p className="status">{authStatus}</p>
      <p className="status">{status}</p>
      <div className="auth-actions">
        {!signedIn ? (
          <button onClick={handleSignIn} type="button">
            Sign in with Google
          </button>
        ) : null}
        {signedIn ? (
          <button
            className="secondary"
            disabled={isSigningOut}
            onClick={handleSignOut}
            type="button"
          >
            Sign out
          </button>
        ) : null}
      </div>
      <button
        disabled={!signedIn || isSummarizing || isSigningOut}
        onClick={handleSummarize}
        type="button"
      >
        Summarize this video
      </button>
      <pre>{result}</pre>
    </main>
  );
}
