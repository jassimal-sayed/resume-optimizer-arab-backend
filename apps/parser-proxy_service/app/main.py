from fastapi import FastAPI

from shared import get_settings

settings = get_settings()

app = FastAPI(title="Parser Proxy Service", version="0.1.0")


@app.get("/health", tags=["system"])
async def healthcheck() -> dict:
    return {"status": "ok", "env": settings.env}


# TODO: add parsing endpoints if/when we migrate parsing off n8n.
