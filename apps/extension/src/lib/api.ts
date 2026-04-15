import { API_BASE_URL } from "../config/env";
import type { SummarizeResponse, SummarizeStreamEvent } from "../types/runtime";

type ApiErrorPayload = {
  detail?: string;
};

function parseSseFrame(frame: string): SummarizeStreamEvent | null {
  let eventType = "";
  const dataLines: string[] = [];

  // SSE frames are line-based. Normalize CRLF so splitting works whether the
  // server/proxy sends "\r\n" or "\n" line endings.
  for (const line of frame.replace(/\r\n/g, "\n").split("\n")) {
    if (!line || line.startsWith(":")) {
      continue;
    }

    if (line.startsWith("event:")) {
      eventType = line.slice("event:".length).trim();
      continue;
    }

    if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trimStart());
    }
  }

  if (!eventType || dataLines.length === 0) {
    return null;
  }

  // The SSE event name carries our logical event type; the data payload only
  // contains the fields for that event, mirroring OpenAI-style stream events.
  return {
    ...JSON.parse(dataLines.join("\n")),
    type: eventType,
  } as SummarizeStreamEvent;
}

function readSseEvents(buffer: string): {
  events: SummarizeStreamEvent[];
  remainder: string;
} {
  // Network chunks can split in the middle of an SSE frame, so keep the last
  // partial frame in the buffer until the next read completes it.
  const normalizedBuffer = buffer.replace(/\r\n/g, "\n");
  const frames = normalizedBuffer.split("\n\n");
  const remainder = frames.pop() || "";
  const events = frames
    .map((frame) => parseSseFrame(frame))
    .filter((event): event is SummarizeStreamEvent => event !== null);

  return { events, remainder };
}

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

  const handleEvent = (event: SummarizeStreamEvent) => {
    onEvent(event);
    if (event.type === "done") {
      sawDone = true;
    }
    if (event.type === "error") {
      throw new Error(event.message);
    }
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const { events, remainder } = readSseEvents(buffer);
      buffer = remainder;

      for (const event of events) {
        handleEvent(event);
      }
    }

    buffer += decoder.decode();
    if (buffer.trim()) {
      const event = parseSseFrame(buffer);
      if (event) {
        handleEvent(event);
      }
    }

    if (!sawDone) {
      throw new Error("Summary stream ended before completion");
    }
    streamCompleted = true;
  } finally {
    if (!streamCompleted) {
      // Abort/error paths should release the stream promptly instead of leaving
      // the browser to drain a response the UI no longer needs.
      await reader.cancel().catch(() => undefined);
    }
    reader.releaseLock();
  }
}
