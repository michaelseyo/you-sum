import type {
  AuthGetStateMessage,
  AuthRuntimeMessage,
  AuthSignInMessage,
  AuthSignOutMessage,
  AuthStateRuntimeResponse,
  GetVideoContextMessage,
  RuntimeMutationResponse,
  VideoContext,
} from "../types/runtime";

export function sendRuntimeMessage(
  message: AuthGetStateMessage | AuthSignInMessage,
): Promise<AuthStateRuntimeResponse>;
export function sendRuntimeMessage(
  message: AuthSignOutMessage,
): Promise<RuntimeMutationResponse>;
export function sendRuntimeMessage(
  message: AuthRuntimeMessage,
): Promise<AuthStateRuntimeResponse | RuntimeMutationResponse> {
  return chrome.runtime.sendMessage(message);
}

export async function getActiveTab(): Promise<chrome.tabs.Tab | undefined> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

export function getVideoContext(tabId: number): Promise<VideoContext> {
  const message: GetVideoContextMessage = { type: "GET_VIDEO_CONTEXT" };
  return chrome.tabs.sendMessage(tabId, message);
}
