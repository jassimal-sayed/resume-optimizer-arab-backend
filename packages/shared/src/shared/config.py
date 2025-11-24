from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed environment loader shared across services."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = "local"

    # API / CORS
    frontend_origin: Optional[str] = None

    # Supabase
    supabase_url: str
    supabase_service_role_key: str
    supabase_jwks_url: Optional[str] = None
    supabase_jwt_secret: Optional[str] = None
    database_url: Optional[str] = None  # direct Postgres URL for Alembic/migrations
    expected_issuer: Optional[str] = None
    expected_audience: Optional[str] = None  # optional audience check for access tokens

    # Storage
    supabase_storage_bucket_resumes: str = "resumes"

    # OpenAI / Pinecone
    openai_api_key: str
    pinecone_api_key: str
    pinecone_index_name: str
    pinecone_environment: Optional[str] = None

    # Workflow callbacks
    workflow_token: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
