from functools import lru_cache
from typing import Literal, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Application
    ENVIRONMENT: Literal["development", "production"] = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 2  # Reduced to prevent MaxClientsInSessionMode error
    DB_MAX_OVERFLOW: int = 5  # Reduced to prevent MaxClientsInSessionMode error
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # Database
    database_url: Optional[str] = None
    SUPABASE_URL: str = "http://localhost"
    SUPABASE_SERVICE_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    # Gateway
    GATEWAY_URL: str = "http://localhost:8000"

    # Microservices URLs
    ORCHESTRATOR_SERVICE_URL: str = "http://orchestrator-service:8001"
    PARSER_SERVICE_URL: str = "http://parser-service:8002"

    # Auth
    SUPABASE_JWT_SECRET: str

    # AI
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_PROVIDER: str = "openai"

    # Storage
    SUPABASE_STORAGE_BUCKET_RESUMES: str = "resumes"

    # Workflow
    WORKFLOW_TOKEN: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str]) -> str:
        if isinstance(v, str):
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v


@lru_cache
def get_settings() -> Settings:
    """
    Return the global settings instance, cached.
    """
    return Settings()
