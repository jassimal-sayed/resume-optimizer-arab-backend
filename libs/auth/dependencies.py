from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from libs.common import envelope_error, get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    def __init__(self, user_id: str, email: Optional[str] = None):
        self.id = user_id
        self.email = email


def verify_jwt(token: str) -> dict:
    """
    Verify Supabase JWT token.
    Uses the JWT secret from settings to verify signature.
    """
    # Development mock tokens for testing (use valid UUID format)
    if token.startswith("mock_") or token.startswith("mock-"):
        return {
            "sub": "00000000-0000-0000-0000-000000000001",
            "email": "mock@example.com",
        }

    try:
        # Supabase JWTs are signed with the JWT secret using HS256
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=envelope_error("Token has expired"),
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=envelope_error(f"Invalid token: {str(e)}"),
        )


def get_current_user_id(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=envelope_error("Missing authentication credentials"),
        )

    try:
        payload = verify_jwt(auth.credentials)
        return payload["sub"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=envelope_error("Invalid authentication credentials"),
        )


def get_current_user(user_id: str = Depends(get_current_user_id)) -> AuthenticatedUser:
    return AuthenticatedUser(user_id=user_id)
