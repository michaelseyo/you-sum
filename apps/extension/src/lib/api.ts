import { API_BASE_URL } from "../config/env";
import type { SummarizeResponse, SummarizeStreamEvent } from "../types/runtime";

type ApiErrorPayload = {
  detail?: string;
};

export async function summarizeVideo(
  videoId: string,
  accessToken: string,
): Promise<SummarizeResponse> {
  const response = await fetch(`${API_BASE_URL}/summarize`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ video_id: videoId }),
  });

  const payload = (await response.json().catch(() => ({}))) as ApiErrorPayload &
    SummarizeResponse;

  if (!response.ok) {
    throw new Error(payload.detail || "API request failed");
  }

  return payload;
}

export async function summarizeVideoStream(
  videoId: string,
  accessToken: string,
  onEvent: (event: SummarizeStreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/summarize/stream`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ video_id: videoId }),
    signal,
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as ApiErrorPayload;
    throw new Error(payload.detail || "API request failed");
  }

  if (!response.body) {
    throw new Error("Streaming is not supported in this browser");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let streamCompleted = false;
  let sawDone = false;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.trim()) {
          continue;
        }

        const event = JSON.parse(line) as SummarizeStreamEvent;
        onEvent(event);
        if (event.type === "done") {
          sawDone = true;
        }
        if (event.type === "error") {
          throw new Error(event.message);
        }
      }
    }

    buffer += decoder.decode();
    if (buffer.trim()) {
      const event = JSON.parse(buffer) as SummarizeStreamEvent;
      onEvent(event);
      if (event.type === "done") {
        sawDone = true;
      }
      if (event.type === "error") {
        throw new Error(event.message);
      }
    }

    if (!sawDone) {
      throw new Error("Summary stream ended before completion");
    }
    streamCompleted = true;
  } finally {
    if (!streamCompleted) {
      await reader.cancel().catch(() => undefined);
    }
    reader.releaseLock();
  }
}
