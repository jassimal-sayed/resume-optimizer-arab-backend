from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from shared import AuthenticatedUser, TokenVerificationError, envelope_error, get_settings, verify_jwt


settings = get_settings()

app = FastAPI(title="SmartResume Match API Gateway", version="0.1.0")

if settings.frontend_origin:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health", tags=["system"])
async def healthcheck() -> dict:
    return {"status": "ok", "env": settings.env}


async def get_current_user(authorization: str = Header(default="")) -> AuthenticatedUser:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=envelope_error("Missing bearer token"))
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return verify_jwt(token)
    except TokenVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=envelope_error(str(exc)))


@app.get("/me", tags=["system"])
async def whoami(user: AuthenticatedUser = Depends(get_current_user)) -> dict:
    return {"data": {"user": user.model_dump()}, "error": None}


# TODO: include routers (resumes, jobs, optimize, callbacks) once implemented.
