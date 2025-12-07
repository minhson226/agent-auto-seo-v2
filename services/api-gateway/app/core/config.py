"""API Gateway configuration settings."""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "API Gateway"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    # Redis for rate limiting
    REDIS_URL: str = "redis://:redis_secret@localhost:6379/0"

    # JWT Settings (for token validation only)
    JWT_SECRET_KEY: str = "your-jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"

    # Service URLs
    AUTH_SERVICE_URL: str = "http://localhost:8081"
    NOTIFICATION_SERVICE_URL: str = "http://localhost:8082"
    KEYWORD_INGESTION_URL: str = "http://localhost:8083"
    SEO_STRATEGY_URL: str = "http://localhost:8084"
    SEO_SCORER_URL: str = "http://localhost:8085"
    CONTENT_GENERATOR_URL: str = "http://localhost:8086"
    ANALYTICS_URL: str = "http://localhost:8087"

    # Rate Limiting
    RATE_LIMIT_PER_USER_MINUTE: int = 100
    RATE_LIMIT_PER_WORKSPACE_MINUTE: int = 1000

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Request timeout (seconds)
    REQUEST_TIMEOUT: int = 30

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
