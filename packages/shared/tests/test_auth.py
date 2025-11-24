import datetime

import pytest
from jose import jwt

from shared import TokenVerificationError, verify_jwt
from shared.config import get_settings


def test_verify_jwt_hs256_with_issuer_and_audience(monkeypatch):
    settings = get_settings()
    secret = "test-secret"
    issuer = "http://localhost/auth/v1"
    audience = "authenticated"

    monkeypatch.setattr(settings, "supabase_jwt_secret", secret)
    monkeypatch.setattr(settings, "supabase_jwks_url", None)
    monkeypatch.setattr(settings, "expected_issuer", issuer)
    monkeypatch.setattr(settings, "expected_audience", audience)

    token = jwt.encode(
        {
            "sub": "user-123",
            "email": "user@example.com",
            "iss": issuer,
            "aud": audience,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
        },
        secret,
        algorithm="HS256",
    )

    user = verify_jwt(token)
    assert user.id == "user-123"
    assert user.email == "user@example.com"


def test_verify_jwt_invalid_issuer(monkeypatch):
    settings = get_settings()
    secret = "test-secret"
    issuer = "http://localhost/auth/v1"

    monkeypatch.setattr(settings, "supabase_jwt_secret", secret)
    monkeypatch.setattr(settings, "supabase_jwks_url", None)
    monkeypatch.setattr(settings, "expected_issuer", "wrong-issuer")
    monkeypatch.setattr(settings, "expected_audience", None)

    token = jwt.encode(
        {
            "sub": "user-123",
            "iss": issuer,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
        },
        secret,
        algorithm="HS256",
    )

    with pytest.raises(TokenVerificationError):
        verify_jwt(token)
