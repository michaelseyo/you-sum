# Summary Streaming Design

## Goal

Make summaries feel fast by rendering OpenAI output incrementally in the Chrome extension while preserving the existing `/summarize` response contract and summary cache behavior.

## Current Flow

The extension calls `POST /summarize` from `apps/extension/src/lib/api.ts`, waits for the full JSON response, then replaces the popup result text. The backend route in `apps/api/main.py` delegates to `SummarizeOrchestrator`, which fetches or reuses the transcript, checks the summary cache, calls OpenAI on a cache miss, saves the completed summary, and returns the full text.

## Proposed Flow

Add a new authenticated endpoint, `POST /summarize/stream`, beside the existing endpoint. It returns newline-delimited JSON events so the extension can use `fetch()` and `ReadableStream` without EventSource limitations around POST bodies and Authorization headers.

Events:

```json
{"type":"status","message":"Checking cache..."}
{"type":"status","message":"Writing summary..."}
{"type":"delta","text":"The"}
{"type":"delta","text":" video"}
{"type":"done","cached":false,"prompt_version":"v1"}
```

For cached summaries, the backend emits the cached text through the same `delta` path and then a `done` event. This keeps the extension rendering logic simple.

## Backend Design

`SummaryService` gains a streaming method that wraps the OpenAI Responses streaming API and yields plain text deltas. The current `summarize_transcript()` method remains unchanged for `/summarize`.

`SummarizeOrchestrator` gains a streaming method that owns cache coordination:

1. Load or fetch the transcript.
2. Check the existing summary cache.
3. Yield cached summary text if present.
4. Otherwise stream OpenAI deltas, accumulate the full text, and save it with the existing `SummariesRepository`.

The route remains thin. It handles auth and converts orchestrator events into a `StreamingResponse`.

## Extension Design

Add a streaming API helper next to the existing `summarizeVideo()` helper. The popup uses the streaming helper for the summarize button, clears the result, and appends text as `delta` events arrive.

The current non-streaming helper stays available as a fallback and to avoid breaking callers.

## Error Handling

If setup fails before streaming starts, return the same style of HTTP errors as `/summarize`. If an error happens while streaming, emit an error event:

```json
{"type":"error","message":"Summary generation failed unexpectedly."}
```

The extension should keep any partial summary visible and set a failure status.

## Testing

Backend tests cover cached streaming, uncached streaming plus cache save, stream route auth, and stream route event formatting. Extension tests cover incremental rendering by mocking the streaming helper or stream reader.
