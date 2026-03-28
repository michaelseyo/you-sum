# YouSum

FastAPI backend for summarizing YouTube videos, with a Chrome extension client in the same repo.

## Workspace

- `apps/api`: FastAPI service that fetches transcripts, caches them, and generates summaries with OpenAI.
- `apps/extension`: Manifest v3 Chrome extension client.

## API Local Development

Docker Compose is the standard local development workflow for the API.

1. Copy `.env.example` to `.env` at the repo root
2. Fill in the auth and API settings in that root `.env`
3. Start the local stack:

```bash
pnpm dev:api
```

This makes Docker Compose load the variables automatically from the root `.env`

The stack starts:

- API: `http://localhost:8000`
- Postgres: `localhost:5432`

The Compose setup uses a separate Postgres container and persists data in the `postgres_data` Docker volume. The API connects to Postgres through `DATABASE_URL=postgresql+psycopg://postgres:postgres@postgres:5432/yousum`.

For local extension development, Docker Compose defaults `ALLOWED_ORIGIN_REGEX` to `chrome-extension://.*` so an unpacked extension can call the API without extra setup.

If those host ports are already taken on your machine, override them when starting Compose:

```bash
API_PORT=8001 POSTGRES_PORT=5433 pnpm dev:api
```

You can stop the stack with:

```bash
pnpm down:api
```

## Direct API Run Fallback

If you need to run the API without Docker for a quick check, use:

```bash
DATABASE_URL=sqlite+pysqlite:///./apps/api/yousum.db pnpm dev-api-direct
```

That fallback is no longer the default local workflow.

`apps/api/.env.example` is still useful as the API runtime reference for direct runs and production configuration.

## Minimal API Deployment

Use one hosted FastAPI service plus one managed Postgres database.

Recommended first pass:

- API hosting: Render web service
- Database: Neon Postgres or Render Postgres

### Required environment variables

```bash
OPENAI_API_KEY=your-openai-api-key
DATABASE_URL=postgresql+psycopg://user:password@host:5432/yousum
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
APP_JWT_SECRET=change-me-to-a-long-random-string
APP_JWT_EXPIRES_MINUTES=60
ALLOWED_EMAILS=you@example.com,teammate@example.com
```

Optional runtime settings:

```bash
OPENAI_MODEL=gpt-5-mini
ENABLE_DEV_LOGIN=false
ALLOWED_ORIGINS=http://localhost:3000,chrome-extension://<your-extension-id>
ALLOWED_ORIGIN_REGEX=chrome-extension://<your-extension-id>
```

`ALLOWED_ORIGIN_REGEX` is opt-in for production. Set it explicitly when you want to allow a specific extension origin.
`ENABLE_DEV_LOGIN` should stay `false` outside local development.
`ALLOWED_EMAILS` accepts a comma-separated list when you want to allow multiple accounts.

### Deploy the API

1. Create a Postgres database.
2. Build the API image from `apps/api/Dockerfile`.
3. Push the image to your container registry.
4. Deploy that image on your container platform.
5. Set the environment variables above, pointing `DATABASE_URL` at the managed Postgres instance.
6. Run the container with:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

If your platform requires an explicit image build command, build locally with:

```bash
docker build -t yousum-api ./apps/api
```

The API container creates its tables on startup using the configured database. For production-like deployments, keep Postgres as a separate managed service rather than shipping it inside the same deployable unit.

## Verification

- `pnpm test:api`
- `pnpm check:api`
- `docker compose up --build`
