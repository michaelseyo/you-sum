import { API_BASE_URL } from "../config/env";
import type { SummarizeResponse } from "../types/runtime";

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
