# parser-proxy_service (optional)

Internal-only FastAPI service to handle heavy resume/job parsing if we move parsing off n8n.

## Run locally

```bash
pip install -e ../../packages/shared
pip install -e .
uvicorn app.main:app --reload --port ${PARSER_PORT:-8010}
```

Use `.env` based on `.env.example`; restrict network exposure in production.
