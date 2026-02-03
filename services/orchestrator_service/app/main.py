"""FastAPI application for the Orchestrator Service."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .routers import jobs as jobs_router
from .worker import run_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run worker in background
    task = asyncio.create_task(run_worker())

    yield

    # Shutdown: Cancel worker
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    """Create and configure the Orchestrator Service FastAPI app."""
    app = FastAPI(
        title="Orchestrator Service",
        version="0.1.0",
        description="Orchestrator management service.",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok", "service": "orchestrator"}

    # Include orchestrator router
    app.include_router(jobs_router.router, prefix="/internal")

    return app


app = create_app()
