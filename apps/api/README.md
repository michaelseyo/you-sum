# API Deployment Notes

## Required Environment Variables

```bash
OPENAI_API_KEY=your-openai-api-key
DATABASE_URL=postgresql+psycopg://user:password@host:5432/yousum
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
APP_JWT_SECRET=change-me-to-a-long-random-string
APP_JWT_EXPIRES_MINUTES=60
ALLOWED_EMAILS=you@example.com,teammate@example.com
```

Optional:

```bash
OPENAI_MODEL=gpt-5-mini
ENABLE_DEV_LOGIN=false
ALLOWED_ORIGINS=http://localhost:3000,chrome-extension://<your-extension-id>
ALLOWED_ORIGIN_REGEX=chrome-extension://<your-extension-id>
```

`ENABLE_DEV_LOGIN` should only be enabled for local development.
`ALLOWED_EMAILS` accepts a comma-separated list when you want to allow multiple accounts.

## Docker Compose Run

Docker Compose is the standard local development workflow.

Copy the repo root `.env.example` to `.env`, then fill in the OpenAI and Google auth values.

```bash
cp .env.example .env
```

Then start the API and Postgres together:

```bash
pnpm dev:api
```

Compose uses:

- API on `http://localhost:8000`
- Postgres on `localhost:5432`
- `DATABASE_URL=postgresql+psycopg://postgres:postgres@postgres:5432/yousum`

For local extension development, Compose defaults `ALLOWED_ORIGIN_REGEX` to `chrome-extension://.*`.

If your host already uses those ports, override them when starting Compose:

```bash
API_PORT=8001 POSTGRES_PORT=5433 pnpm dev:api
```

Stop the stack with:

```bash
pnpm down:api
```

## Direct Run Fallback

If you need to run the API without Docker, use:

```bash
DATABASE_URL=sqlite+pysqlite:///./apps/api/yousum.db pnpm dev-api-direct
```

`apps/api/.env.example` remains the API runtime env reference for direct runs and production setups.

## Transcript Provider Limitation

The current transcript fetch path uses `youtube-transcript-api` from the backend. This works for local development more reliably than cloud deployment. On cloud hosts, YouTube may block transcript requests from datacenter IP ranges, which can cause `/summarize` to fail even when the rest of the API is healthy.

Treat the current transcript retrieval setup as local-development friendly rather than production-reliable.

## Production Run

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Hosting Shape

- One FastAPI container image
- One separate Postgres service

For local parity or lightweight self-hosting, use `docker-compose.yml` with the bundled Postgres service and persistent volume.

For production-like deployment, build from `apps/api/Dockerfile` and connect the container to a managed Postgres database.

This app creates tables on startup, so no separate migration step is required yet.
