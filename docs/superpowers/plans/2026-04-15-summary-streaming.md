# Summary Streaming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add token-by-token summary rendering for OpenAI cache misses while preserving the existing `/summarize` API contract.

**Architecture:** Add a backward-compatible `POST /summarize/stream` endpoint that emits newline-delimited JSON events. The backend reuses the existing transcript and summary cache flow, streams OpenAI deltas on cache misses, accumulates the final text, and saves it to the existing summaries table.

**Tech Stack:** FastAPI `StreamingResponse`, OpenAI Python async Responses streaming, SQLAlchemy repositories, React popup, Chrome extension `fetch()` readable streams, Python `unittest`, Vitest.

---

## File Structure

- Modify `apps/api/app/services/summary.py`: add a streaming OpenAI delta generator beside the existing full-response method.
- Modify `apps/api/app/services/summarize_orchestrator.py`: add stream event types and a streaming orchestration method that preserves cache behavior.
- Modify `apps/api/main.py`: add `POST /summarize/stream`, keep route thin, serialize newline-delimited JSON events.
- Modify `apps/api/tests/test_summarize_orchestrator.py`: test cached and uncached streaming orchestration.
- Modify `apps/api/tests/test_auth_routes.py`: test streaming auth and route output format.
- Modify `apps/extension/src/types/runtime.ts`: add stream event TypeScript types.
- Modify `apps/extension/src/lib/api.ts`: add `summarizeVideoStream()`.
- Modify `apps/extension/src/popup/App.tsx`: use streaming helper and progressively append deltas.
- Add or modify extension tests if the current test setup supports popup tests.

## Task 1: Backend Streaming Service

**Files:**
- Modify: `apps/api/app/services/summary.py`
- Test indirectly in: `apps/api/tests/test_summarize_orchestrator.py`

- [ ] **Step 1: Add fake streaming support to the orchestrator test fake**

In `apps/api/tests/test_summarize_orchestrator.py`, extend `FakeSummaryService`:

```python
    async def stream_summary_transcript(self, transcript_text: str):
        self.calls += 1
        for chunk in ("summary:", transcript_text):
            yield chunk
```

- [ ] **Step 2: Run current orchestrator tests**

Run: `uv run --directory apps/api python -m unittest tests.test_summarize_orchestrator -v`

Expected: PASS. This confirms the fake change did not break existing tests.

- [ ] **Step 3: Add the real streaming method**

In `apps/api/app/services/summary.py`, add:

```python
    async def stream_summary_transcript(self, transcript_text: str):
        prompt = build_summary_prompt(transcript_text)
        async with self.client.responses.stream(
            model=self.model,
            instructions=SUMMARY_INSTRUCTIONS,
            input=prompt,
        ) as stream:
            async for event in stream:
                if event.type == "response.output_text.delta":
                    yield event.delta
```

Keep `summarize_transcript()` unchanged.

- [ ] **Step 4: Run API formatting check**

Run: `uv run --directory apps/api ruff check app/services/summary.py`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/app/services/summary.py apps/api/tests/test_summarize_orchestrator.py
git commit -m "feat: add OpenAI summary streaming service"
```

## Task 2: Backend Streaming Orchestrator

**Files:**
- Modify: `apps/api/app/services/summarize_orchestrator.py`
- Modify: `apps/api/tests/test_summarize_orchestrator.py`

- [ ] **Step 1: Write cached summary streaming test**

Add a test to `SummarizeOrchestratorTestCase`:

```python
    async def test_stream_reuses_cached_summary(self) -> None:
        summary_service = FakeSummaryService()
        transcripts_repository = InMemoryTranscriptsRepository()
        summaries_repository = InMemorySummariesRepository()
        transcript_text = "hello world"
        transcript = transcripts_repository.save_transcript(
            object(),
            video_id="video-1",
            transcript_text=transcript_text,
            transcript_fingerprint=build_transcript_fingerprint(transcript_text),
        )
        summaries_repository.save_summary(
            object(),
            transcript_id=transcript.id,
            summary_text="cached summary",
            model="gpt-5-mini",
            prompt_version=SUMMARY_PROMPT_VERSION,
        )
        orchestrator = SummarizeOrchestrator(
            summary_service=summary_service,
            transcripts_repository=transcripts_repository,
            summaries_repository=summaries_repository,
        )

        events = [
            event
            async for event in orchestrator.stream_summarize_video(object(), "video-1")
        ]

        self.assertEqual(
            events,
            [
                {"type": "status", "message": "Checking cache..."},
                {"type": "delta", "text": "cached summary"},
                {
                    "type": "done",
                    "cached": True,
                    "prompt_version": SUMMARY_PROMPT_VERSION,
                },
            ],
        )
        self.assertEqual(summary_service.calls, 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --directory apps/api python -m unittest tests.test_summarize_orchestrator.SummarizeOrchestratorTestCase.test_stream_reuses_cached_summary -v`

Expected: FAIL with `AttributeError: 'SummarizeOrchestrator' object has no attribute 'stream_summarize_video'`.

- [ ] **Step 3: Write uncached summary streaming test**

Add:

```python
    async def test_stream_generates_and_caches_summary(self) -> None:
        summary_service = FakeSummaryService()
        transcripts_repository = InMemoryTranscriptsRepository()
        summaries_repository = InMemorySummariesRepository()
        orchestrator = SummarizeOrchestrator(
            summary_service=summary_service,
            transcripts_repository=transcripts_repository,
            summaries_repository=summaries_repository,
        )

        from unittest.mock import patch

        with patch(
            "app.services.summarize_orchestrator.fetch_transcript_text",
            return_value="hello world",
        ):
            events = [
                event
                async for event in orchestrator.stream_summarize_video(
                    object(), "video-1"
                )
            ]

        self.assertEqual(
            events,
            [
                {"type": "status", "message": "Fetching transcript..."},
                {"type": "status", "message": "Checking cache..."},
                {"type": "status", "message": "Writing summary..."},
                {"type": "delta", "text": "summary:"},
                {"type": "delta", "text": "hello world"},
                {
                    "type": "done",
                    "cached": False,
                    "prompt_version": SUMMARY_PROMPT_VERSION,
                },
            ],
        )
        cached = summaries_repository.get_by_cache_key(
            object(),
            transcript_id=1,
            model="gpt-5-mini",
            prompt_version=SUMMARY_PROMPT_VERSION,
        )
        self.assertEqual(cached.summary_text, "summary:hello world")
```

- [ ] **Step 4: Implement stream orchestration**

In `apps/api/app/services/summarize_orchestrator.py`, add a module type alias:

```python
StreamEvent = dict[str, str | bool]
```

Add `stream_summarize_video()` that follows the existing `summarize_video()` cache flow, yields status events, yields cached text as `delta`, streams uncached deltas from `self.summary_service.stream_summary_transcript()`, joins deltas into `summary_text`, saves through `self.summaries_repository.save_summary()`, and finally yields `done`.

- [ ] **Step 5: Run orchestrator tests**

Run: `uv run --directory apps/api python -m unittest tests.test_summarize_orchestrator -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/api/app/services/summarize_orchestrator.py apps/api/tests/test_summarize_orchestrator.py
git commit -m "feat: stream summary orchestration"
```

## Task 3: Streaming API Route

**Files:**
- Modify: `apps/api/main.py`
- Modify: `apps/api/tests/test_auth_routes.py`

- [ ] **Step 1: Write missing auth test**

Add to `AuthRoutesTestCase`:

```python
    def test_summarize_stream_rejects_missing_token(self) -> None:
        temp_dir, main_module = load_main_module()
        self.addCleanup(temp_dir.cleanup)

        with TestClient(main_module.app) as client:
            response = client.post("/summarize/stream", json={"video_id": "video-1"})

        self.assertEqual(response.status_code, 401)
```

- [ ] **Step 2: Write successful stream route test**

Add:

```python
    def test_summarize_stream_succeeds_with_valid_dev_token(self) -> None:
        temp_dir, main_module = load_main_module(enable_dev_login=True)
        self.addCleanup(temp_dir.cleanup)

        async def fake_stream(_db, _video_id):
            yield {"type": "delta", "text": "hello"}
            yield {"type": "done", "cached": False, "prompt_version": "v1"}

        with TestClient(main_module.app) as client:
            login_response = client.post("/auth/dev-login", json={})
            access_token = login_response.json()["access_token"]

            with patch.object(
                main_module.summarize_orchestrator,
                "stream_summarize_video",
                fake_stream,
            ):
                response = client.post(
                    "/summarize/stream",
                    json={"video_id": "video-1"},
                    headers={"Authorization": f"Bearer {access_token}"},
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/x-ndjson")
        self.assertEqual(
            response.text,
            '{"type":"delta","text":"hello"}\n'
            '{"type":"done","cached":false,"prompt_version":"v1"}\n',
        )
```

- [ ] **Step 3: Run tests to verify route is missing**

Run: `uv run --directory apps/api python -m unittest tests.test_auth_routes.AuthRoutesTestCase.test_summarize_stream_rejects_missing_token tests.test_auth_routes.AuthRoutesTestCase.test_summarize_stream_succeeds_with_valid_dev_token -v`

Expected: first test may return 404 and second fails until the route exists.

- [ ] **Step 4: Implement route**

In `apps/api/main.py`, import:

```python
import json
from collections.abc import AsyncIterator
from fastapi.responses import StreamingResponse
```

Add a helper near the route:

```python
async def encode_stream_events(events) -> AsyncIterator[str]:
    try:
        async for event in events:
            yield json.dumps(event, separators=(",", ":")) + "\n"
    except RateLimitError:
        logger.warning("OpenAI rate limit or quota issue during stream")
        yield json.dumps(
            {
                "type": "error",
                "message": "Summary generation is temporarily unavailable due to an OpenAI quota or rate limit issue.",
            },
            separators=(",", ":"),
        ) + "\n"
    except APIStatusError:
        logger.exception("OpenAI API status error during stream")
        yield json.dumps(
            {
                "type": "error",
                "message": "Summary generation failed because the upstream AI service returned an error.",
            },
            separators=(",", ":"),
        ) + "\n"
    except Exception:
        logger.exception("Unexpected summary stream failure")
        yield json.dumps(
            {"type": "error", "message": "Summary generation failed unexpectedly."},
            separators=(",", ":"),
        ) + "\n"
```

Add:

```python
@app.post("/summarize/stream")
async def summarize_stream(
    payload: SummarizeRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    logger.info(
        "Summarize stream requested for video_id=%s by email=%s user_id=%s",
        payload.video_id,
        current_user.email,
        current_user.id,
    )
    events = summarize_orchestrator.stream_summarize_video(db, payload.video_id)
    return StreamingResponse(
        encode_stream_events(events),
        media_type="application/x-ndjson",
    )
```

- [ ] **Step 5: Run route tests**

Run: `uv run --directory apps/api python -m unittest tests.test_auth_routes -v`

Expected: PASS.

- [ ] **Step 6: Run backend checks**

Run: `pnpm test:api`

Expected: PASS.

Run: `pnpm check:api`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/api/main.py apps/api/tests/test_auth_routes.py
git commit -m "feat: add summary streaming route"
```

## Task 4: Extension Streaming API Helper

**Files:**
- Modify: `apps/extension/src/types/runtime.ts`
- Modify: `apps/extension/src/lib/api.ts`

- [ ] **Step 1: Add stream event types**

In `apps/extension/src/types/runtime.ts`, add:

```ts
export type SummarizeStreamEvent =
  | {
      message: string;
      type: "status";
    }
  | {
      text: string;
      type: "delta";
    }
  | {
      cached: boolean;
      prompt_version: string;
      type: "done";
    }
  | {
      message: string;
      type: "error";
    };
```

- [ ] **Step 2: Add streaming helper**

In `apps/extension/src/lib/api.ts`, import `SummarizeStreamEvent` and add:

```ts
export async function summarizeVideoStream(
  videoId: string,
  accessToken: string,
  onEvent: (event: SummarizeStreamEvent) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/summarize/stream`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ video_id: videoId }),
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
      if (event.type === "error") {
        throw new Error(event.message);
      }
    }
  }

  buffer += decoder.decode();
  if (buffer.trim()) {
    const event = JSON.parse(buffer) as SummarizeStreamEvent;
    onEvent(event);
    if (event.type === "error") {
      throw new Error(event.message);
    }
  }
}
```

- [ ] **Step 3: Run extension build**

Run: `pnpm build:extension`

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add apps/extension/src/types/runtime.ts apps/extension/src/lib/api.ts
git commit -m "feat: add extension summary stream client"
```

## Task 5: Popup Progressive Rendering

**Files:**
- Modify: `apps/extension/src/popup/App.tsx`

- [ ] **Step 1: Switch popup import**

Replace:

```ts
import { summarizeVideo } from "../lib/api";
```

With:

```ts
import { summarizeVideoStream } from "../lib/api";
```

- [ ] **Step 2: Use stream helper in `handleSummarize()`**

Replace the full-response call:

```ts
setStatus(`Summarizing ${context.videoId}...`);
const data = await summarizeVideo(context.videoId, authState.accessToken);
setResult(data.summary);
setStatus("Summary loaded");
```

With:

```ts
setStatus(`Summarizing ${context.videoId}...`);
setResult("");
await summarizeVideoStream(context.videoId, authState.accessToken, (event) => {
  if (event.type === "status") {
    setStatus(event.message);
    return;
  }

  if (event.type === "delta") {
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
});
```

- [ ] **Step 3: Preserve partial text on stream errors**

In the existing `catch`, only replace `result` if it is still empty. Use a local `receivedText` boolean to avoid losing partial output:

```ts
let receivedText = false;
...
if (event.type === "delta") {
  receivedText = true;
  setResult((current) => current + event.text);
  return;
}
...
} catch (error: unknown) {
  setStatus("Unable to summarize video");
  if (!receivedText) {
    setResult(
      error instanceof Error ? error.message : "Unable to summarize video",
    );
  }
}
```

- [ ] **Step 4: Run extension build**

Run: `pnpm build:extension`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/extension/src/popup/App.tsx
git commit -m "feat: render streamed summaries in popup"
```

## Task 6: End-to-End Verification

**Files:**
- No planned source edits.

- [ ] **Step 1: Run backend tests**

Run: `pnpm test:api`

Expected: PASS.

- [ ] **Step 2: Run backend check**

Run: `pnpm check:api`

Expected: PASS.

- [ ] **Step 3: Run extension build**

Run: `pnpm build:extension`

Expected: PASS.

- [ ] **Step 4: Manual smoke test**

Run: `DATABASE_URL=sqlite+pysqlite:///./apps/api/yousum.db pnpm dev-api-direct`

In another terminal, run: `pnpm build-dev:extension`, load the extension in Chrome, sign in, open a YouTube video, and click “Summarize this video”.

Expected: summary text appears incrementally, final status becomes “Summary loaded”, repeating the same video loads from cache.

- [ ] **Step 5: Final commit if any verification fixes were needed**

```bash
git status --short
git add <changed-files>
git commit -m "fix: polish summary streaming"
```
