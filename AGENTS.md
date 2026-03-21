# AGENTS.md

## Project Overview

YouSum is a monorepo with:

- `apps/api`: FastAPI backend that fetches YouTube transcripts, caches data, and generates summaries with OpenAI
- `apps/extension`: Chrome extension client (Manifest V3)

Prefer small, targeted changes. Preserve the current architecture unless the task explicitly asks for a larger refactor.

## Repo Priorities

When making changes:

1. Keep API routes thin and business logic in services/orchestrators/repositories.
2. Avoid breaking the extension-to-API contract.
3. Prefer incremental changes over broad rewrites.
4. Update tests when behavior changes.

## Directory Guide

- `apps/api/main.py`: FastAPI app entrypoint and route wiring
- `apps/api/app/services`: business logic
- `apps/api/app/repositories`: database access
- `apps/api/app/schemas`: request/response models
- `apps/api/app/clients`: external integrations and DB setup
- `apps/api/tests`: backend test suite
- `apps/extension/src`: extension scripts and popup UI

## Local Development

Primary API workflow:

```bash
pnpm dev:api
```

This starts Docker Compose for:

- API at `http://localhost:8000`
- Postgres at `localhost:5432`

Direct API fallback:

```bash
DATABASE_URL=sqlite+pysqlite:///./apps/api/yousum.db pnpm dev-api-direct
```

## Validation Commands

Run the smallest relevant checks first.

Backend:

```bash
pnpm test:api
pnpm check:api
pnpm fix:api
```

## Coding Conventions

### Python / API

- Keep route handlers minimal.
- Put summary-related orchestration in services, not route functions.
- Put persistence logic in repositories.
- Reuse existing schema types for request/response shapes.
- Follow existing FastAPI dependency patterns in `main.py`.

### Extension

- Keep changes lightweight and consistent with the existing plain JS structure.
- Do not introduce a new frontend framework unless explicitly requested.

## Environment Notes

The API expects environment variables such as:

- `OPENAI_API_KEY`
- `DATABASE_URL`

Optional:

- `OPENAI_MODEL`
- `ALLOWED_ORIGINS`
- `ALLOWED_ORIGIN_REGEX`

For local extension development, CORS may rely on `chrome-extension://...` origins.

## Change Rules

- Do not rename major modules or move files unless necessary.
- Do not introduce migrations/framework changes unless explicitly requested.
- Prefer preserving current DB initialization behavior.
- If changing API behavior, check whether the extension depends on that response shape.
- If adding a new OpenAI call path, keep error handling consistent with existing patterns.

## Testing Expectations

- Add or update tests in `apps/api/tests` for backend behavior changes.
- For small refactors, run at least the directly affected tests.
- For route/service changes, prefer covering both success and failure paths.

## Safe Workflow For Agents

Before editing:

1. Read the relevant files end-to-end.
2. Identify whether the change belongs in routes, services, repositories, or the extension.
3. Make the narrowest change that solves the request.

Before finishing:

1. Run relevant tests/checks if possible.
2. Mention any assumptions.
3. Call out anything not verified.

## When Unsure

If a request could affect both the backend and extension, inspect both sides before changing contracts.
If a task suggests a larger architectural shift, pause and propose the tradeoffs before proceeding.
