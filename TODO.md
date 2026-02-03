# Backend TODO – SmartResume Match (Monorepo, FastAPI, Supabase Auth/DB)

Context snapshot (from frontend/API specs):

- Frontend expects REST under `API_BASE_URL` with `/jobs`, `/jobs/:id`, `/jobs/:id/refine` plus resume upload/text flows; bearer token is Supabase access token.
- Language metadata required: `resume_lang`, `jd_lang`, `desired_output_lang`; results return detected langs + preview markdown.
- Demo mode uses mocks now; real backend should match `API_DESIGN.md` envelopes `{ data, error }`.

Architecture & pattern:

- Design pattern: FastAPI routers → service layer (use cases) → repository/clients (Supabase REST, Pinecone, OpenAI). Shared Pydantic domain models live in `packages/shared`.
- Monorepo layout (services decoupled; communicate via Supabase DB + webhooks/queues, not direct imports). Each service lives in its own directory with its own Dockerfile and compose service block:
  - `apps/api-gateway_service/`: public HTTP API, auth, CORS, request validation, orchestration, webhooks.
  - `apps/worker-orchestrator_service/`: async worker that consumes queued tasks (job optimize, re-run/refine, embedding) using Supabase tables/queues, calls OpenAI + Pinecone, writes results back.
  - `apps/parser-proxy_service/` (optional): internal-only endpoint for heavy resume/job parsing if we move parsing off n8n.
  - `packages/shared/`: Pydantic schemas, config loader, Supabase client wrapper, JWT verifier, logging utilities.

Proposed Supabase schema (database models):

- `resumes` (uuid pk, user_id fk auth.users, title text, file_url text, active_version_id uuid null, source enum['upload','text'], created_at timestamptz default now(), updated_at timestamptz).
- `resume_versions` (uuid pk, resume_id fk -> resumes on delete cascade, version_no int default 1, raw_text text, content_md text, parsed_json jsonb, embedding_status enum['pending','indexed','failed'] default 'pending', created_at timestamptz default now()).
- `jobs` (uuid pk, user_id fk auth.users, title text, company text null, job_description text, parsed_json jsonb, custom_instructions text null, resume_lang text check in ('en','ar'), jd_lang text check in ('en','ar'), desired_output_lang text check in ('en','ar'), status enum['queued','processing','complete','failed'] default 'queued', created_at timestamptz default now(), updated_at timestamptz default now()).
- `optimizations` (uuid pk, user_id fk auth.users, resume_id fk resumes, resume_version_id fk resume_versions, job_id fk jobs, score int, report_json jsonb, preview_md text, change_log jsonb, created_at timestamptz default now(), updated_at timestamptz default now()).
- `task_queue` (uuid pk, task_type text enum['optimize','embed_resume','embed_job'], payload jsonb, status enum['queued','processing','complete','failed'] default 'queued', attempts int default 0, last_error text null, created_at timestamptz default now(), updated_at timestamptz default now()) for worker decoupling.
- `workflow_tokens` (text pk) or config table to store shared secrets for callback verification (or use env).

Roadmap (sequenced, agent-friendly; mark [ ] → [~] → [x]):

### Phase A – Foundations

- **ID:** B0 — Status: [x] — Monorepo scaffold
  - [x] Create folders `apps/api-gateway_service`, `apps/worker-orchestrator_service`, `packages/shared` (and `apps/parser-proxy_service` if used).
  - [x] Add per-app `pyproject.toml` or `requirements.txt`, `Dockerfile`, `.env.example`, `README.md` (consistent naming/structure across services).
  - [x] Add root `.dockerignore`, `.gitignore`, `docker-compose.yml` (local: api, worker, supabase-emulator/postgres, pinecone-mock), ensuring each service has its own compose service using its Dockerfile context.
  - [x] Add tooling configs (ruff, black, mypy) and pre-commit; ensure consistent lint/type settings across services.
  - [x] Implement shared config loader in `packages/shared` (python-dotenv, env validation).

### Phase B – Data & Auth

- **ID:** B1 — Status: [~] — Supabase schema & migrations (Alembic-managed)
  - [x] Configure Alembic in `apps/api-gateway_service` to target Supabase Postgres; no manual SQL files outside Alembic.
  - [x] Generate initial migration for all tables/enums with indexes on `user_id`, `status`, `created_at`.
  - [x] Add RLS: rows scoped to `auth.uid()`; callbacks/workflow tokens remain service-role only.
  - [x] Add seed or env doc for `workflow_tokens`; document Storage bucket names for resumes.
  - [x] Add local supabase CLI/emulator instructions to README; include Alembic commands for upgrade/downgrade.
- **ID:** B2 — Status: [x] — Auth/JWT verification module
  - [x] Implement `get_current_user` in `packages/shared/auth.py` using Supabase JWKS or JWT secret (cache JWKS).
  - [x] Add FastAPI dependency wrapper and error responses (401 with envelope `{ error }`).
  - [x] Include role/iss/aud validation; unit tests with sample tokens.

### Phase C – API Gateway (FastAPI)

- **ID:** B3 — Status: [x] — Resume ingestion routes
  - [x] Scaffold FastAPI app with CORS for `FRONTEND_ORIGIN`, healthcheck.
  - [x] Routes: `POST /resumes/upload` (multipart file + title → Supabase Storage signed URL + row + task_queue embed_resume), `POST /resumes/from-text` (title + raw_text → resume + version + enqueue embed), `POST /callbacks/n8n/resume` (X-Workflow-Token guard → update resume_version parsed_json/raw_text + enqueue embed).
  - [x] Responses follow `{ data, error }`; ownership check via `user_id`.
  - [x] TODO markers for storage bucket names and table names if not final.
- **ID:** B4 — Status: [x] — Job ingest + lifecycle
  - [x] Routes: `POST /jobs`, `GET /jobs`, `GET /jobs/{id}`, `POST /jobs/{id}/refine`, `POST /callbacks/n8n/job`.
  - [x] Persist language metadata (`resume_lang`, `jd_lang`, `desired_output_lang`); derive title fallback per `API_DESIGN.md`.
  - [x] On create/refine, enqueue optimize task; on callback, enqueue embed_job; always enforce user ownership.
  - [x] Envelope responses and error handling; pagination for list.
- **ID:** B5 — Status: [~] — Optimization result surface
  - [x] Ensure job detail includes latest `result` (joins `optimizations`).
  - [ ] Endpoint `POST /resumes/{resume_id}/optimize` (if kept) proxies to task enqueue; document any overlap with `/jobs`.
  - [ ] Wire OpenAPI docs with Pydantic schemas from `packages/shared`.

### Phase D – Worker / AI & Vector

- **ID:** B6 — Status: [ ] — Worker task processor
  - [ ] Worker entrypoint that polls `task_queue` with visibility timeout/backoff; supports `embed_resume`, `embed_job`, `optimize`.
  - [ ] Implement idempotency guard (dedupe key per resume_version/job).
  - [ ] Update task status/attempts/last_error; structured logging.
  - [ ] Persist optimization outputs to `optimizations`, update `jobs.status`.
- **ID:** B7 — Status: [ ] — Pinecone/vector utilities
  - [ ] Shared chunker (~3500 chars, 400 overlap) and metadata shape.
  - [ ] Embedding client (OpenAI) and Pinecone upsert/query with namespace=user_id.
  - [ ] `search_resume_vs_job` helper returning matches + avg score.
  - [ ] Retries/backoff, circuit-breaker defaults.
- **ID:** B8 — Status: [ ] — LLM prompts (analysis + generation)
  - [ ] Implement `analyze_resume_vs_job` prompt with JSON-only guard, ATS-safe rules.
  - [ ] Implement `generate_optimized_resume` with truthfulness constraints, markdown output + change_log.
  - [ ] Add unit tests with stubbed OpenAI responses.

### Phase E – Security, Observability, Ops

- **ID:** B9 — Status: [ ] — Security hardening
  - [ ] Enforce auth on all user routes; validate `user_id` ownership at repo layer.
  - [ ] Limit payload sizes, sanitize markdown, generate signed URLs for Storage, verify `X-Workflow-Token` on callbacks.
  - [ ] Add rate-limit middleware placeholder and basic audit logs.
- **ID:** B10 — Status: [ ] — Testing & CI
  - [ ] Unit tests for services/repositories; contract tests for API envelopes; integration harness vs Supabase test project + mocked Pinecone/OpenAI.
  - [ ] GitHub Actions (or similar) for lint/test/type-check per app; build Docker images.
  - [ ] Update `docker-compose.yml` for local dev (api + worker) and docs on how to run.

Notes for n8n alignment:

- WF-Parse-Resume: backend supplies signed Storage URL to n8n; callback hits `/callbacks/n8n/resume` with `X-Workflow-Token`.
- WF-Job-URL-Ingest: n8n scrapes/cleans JD text; callback hits `/callbacks/n8n/job`; worker enqueues embed + optimization once `job_description` exists.
