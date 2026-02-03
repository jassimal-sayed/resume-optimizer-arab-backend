"""
Gateway Service: Pure API Gateway

Handles:
- User authentication (JWT verification)
- Rate limiting (TODO)
- Request routing to Orchestrator
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import jobs, uploads


def create_app() -> FastAPI:
    app = FastAPI(title="Resume Optimizer API Gateway")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure per environment
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "gateway"}

    app.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
    app.include_router(uploads.router, prefix="/resumes", tags=["Resumes"])

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
