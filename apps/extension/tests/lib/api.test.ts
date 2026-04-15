import { beforeEach, describe, expect, it, vi } from "vitest";
import { summarizeVideoStream } from "../../src/lib/api.ts";
import type { SummarizeStreamEvent } from "../../src/types/runtime.ts";

function streamResponse(chunks: string[], init?: ResponseInit): Response {
  const encoder = new TextEncoder();

  return new Response(
    new ReadableStream({
      start(controller) {
        for (const chunk of chunks) {
          controller.enqueue(encoder.encode(chunk));
        }
        controller.close();
      },
    }),
    init,
  );
}

describe("summarizeVideoStream", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("parses SSE events across chunk boundaries", async () => {
    const events: SummarizeStreamEvent[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        streamResponse(
          [
            'event: status\ndata: {"message":"Writing"}\n\n',
            'event: delta\ndata: {"text":"Hel"}\n\nevent: del',
            'ta\ndata: {"text":"lo"}\n\n',
            'event: done\ndata: {"cached":false,"prompt_version":"v1"}\n\n',
          ],
          {
            headers: {
              "Content-Type": "text/event-stream",
            },
            status: 200,
          },
        ),
      ),
    );

    await summarizeVideoStream("video-id", "token", (event) => {
      events.push(event);
    });

    expect(events).toEqual([
      { message: "Writing", type: "status" },
      { text: "Hel", type: "delta" },
      { text: "lo", type: "delta" },
      { cached: false, prompt_version: "v1", type: "done" },
    ]);
  });

  it("throws when the SSE stream sends an error event", async () => {
    const events: SummarizeStreamEvent[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        streamResponse(['event: error\ndata: {"message":"Boom"}\n\n'], {
          headers: {
            "Content-Type": "text/event-stream",
          },
          status: 200,
        }),
      ),
    );

    await expect(
      summarizeVideoStream("video-id", "token", (event) => {
        events.push(event);
      }),
    ).rejects.toThrow("Boom");

    expect(events).toEqual([{ message: "Boom", type: "error" }]);
  });

  it("throws when the SSE stream ends before done", async () => {
    const events: SummarizeStreamEvent[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        streamResponse(['event: delta\ndata: {"text":"partial"}\n\n'], {
          headers: {
            "Content-Type": "text/event-stream",
          },
          status: 200,
        }),
      ),
    );

    await expect(
      summarizeVideoStream("video-id", "token", (event) => {
        events.push(event);
      }),
    ).rejects.toThrow("Summary stream ended before completion");

    expect(events).toEqual([{ text: "partial", type: "delta" }]);
  });
});
