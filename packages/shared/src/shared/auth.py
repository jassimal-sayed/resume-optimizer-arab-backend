import json
from functools import lru_cache
from typing import Any, Dict, Optional

import httpx
from jose import JWTError, jwt
from pydantic import BaseModel

from .config import get_settings


class AuthenticatedUser(BaseModel):
    id: str
    email: Optional[str] = None


class TokenVerificationError(Exception):
    pass


@lru_cache
def _get_jwks() -> Optional[Dict[str, Any]]:
    settings = get_settings()
    if not settings.supabase_jwks_url:
        return None
    with httpx.Client() as client:
        resp = client.get(settings.supabase_jwks_url, timeout=5.0)
        resp.raise_for_status()
        return resp.json()


def verify_jwt(token: str) -> AuthenticatedUser:
    """
    Verify Supabase access token using JWKS if available, otherwise HS256 secret.
    """
    settings = get_settings()
    decode_kwargs = {
        "options": {"verify_aud": bool(settings.expected_audience), "verify_iss": bool(settings.expected_issuer)},
    }
    if settings.expected_audience:
        decode_kwargs["audience"] = settings.expected_audience
    try:
        if settings.supabase_jwks_url:
            jwks = _get_jwks()
            if not jwks:
                raise TokenVerificationError("JWKS not available")
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            key = None
            for jwk in jwks.get("keys", []):
                if jwk.get("kid") == kid:
                    key = jwk
                    break
            if not key:
                raise TokenVerificationError("No matching JWK found")
            algs = key.get("alg", ["RS256"])
            claims = jwt.decode(token, key, algorithms=algs, **decode_kwargs)
        elif settings.supabase_jwt_secret:
            claims = jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], **decode_kwargs)
        else:
            raise TokenVerificationError("No JWKS URL or JWT secret configured")
    except (JWTError, httpx.HTTPError, TokenVerificationError) as exc:
        raise TokenVerificationError(str(exc)) from exc

    user_id = claims.get("sub") or claims.get("user_id")
    email = claims.get("email")
    issuer = claims.get("iss")
    if settings.expected_issuer and issuer != settings.expected_issuer:
        raise TokenVerificationError("Invalid issuer")
    if not user_id:
        raise TokenVerificationError("Missing user identifier in token")
    return AuthenticatedUser(id=str(user_id), email=email)


def envelope_error(message: str) -> dict:
    return {"data": None, "error": {"message": message}}
