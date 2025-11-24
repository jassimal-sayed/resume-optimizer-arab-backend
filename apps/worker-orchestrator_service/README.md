# worker-orchestrator_service

Background worker that consumes queued tasks (optimize/refine, embed resume/job), calls OpenAI + Pinecone, and writes back to Supabase.

## Run locally

```bash
pip install -e ../../packages/shared
pip install -e .
python -m app.main
```

Set `.env` from `.env.example`; ensure Supabase DB and Pinecone/OpenAI keys are available.
