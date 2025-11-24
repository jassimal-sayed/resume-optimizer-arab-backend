# api-gateway_service

Public FastAPI surface: auth, CORS, request validation, routers, webhooks.

## Run locally

```bash
pip install -e ../../packages/shared
pip install -e .
uvicorn app.main:app --reload --port ${API_PORT:-8000}
```

## Env

Copy `.env.example` to `.env` and fill Supabase, OpenAI, Pinecone, workflow token, and CORS origin.

## Migrations

Alembic will manage schema; models + migrations live here to target Supabase Postgres.

Commands (run inside `apps/api-gateway_service`):
```bash
alembic upgrade head
alembic downgrade -1
alembic revision --autogenerate -m "desc"  # if models change
```

## Supabase emulator / local DB
- Start Supabase locally (CLI) or point `DATABASE_URL` to your Postgres instance. Example for Supabase CLI: `supabase start` (creates local Postgres at `localhost:54322`).
- Set `SUPABASE_URL`/`SUPABASE_SERVICE_ROLE_KEY` for REST/auth, and `DATABASE_URL` for Alembic (e.g., `postgresql+psycopg://postgres:postgres@localhost:54322/postgres`).
- Ensure storage bucket `SUPABASE_STORAGE_BUCKET_RESUMES` exists (default: `resumes`).
- For workflow callbacks, configure `WORKFLOW_TOKEN` and insert into `workflow_tokens` table or pass via env for service-role checks.
