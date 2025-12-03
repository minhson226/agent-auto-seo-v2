"""Notification Service configuration settings."""

from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Notification Service"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8082

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://autoseo:autoseo_secret@localhost:5432/autoseo"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    # Email Settings
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@autoseo.com"
    SMTP_FROM_NAME: str = "Auto-SEO Platform"
    SMTP_TLS: bool = True

    # SendGrid (alternative to SMTP)
    SENDGRID_API_KEY: Optional[str] = None

    # Slack Settings
    SLACK_WEBHOOK_URL: Optional[str] = None

    # Retry Settings
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 60

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

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
