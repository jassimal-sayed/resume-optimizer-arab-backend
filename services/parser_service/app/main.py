"""
Parser Service: Stateless file parsing microservice.

Handles:
- PDF text extraction
- DOCX text extraction
- OCR fallback for scanned documents
- Returns extracted text to Gateway/Orchestrator
"""

from fastapi import FastAPI

from .routers import extract as extract_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Parser Service",
        version="0.1.0",
        description="Parser management service.",
    )

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok", "service": "parser"}

    # Include parser router
    app.include_router(extract_router.router, prefix="/internal")

    return app


app = create_app()
