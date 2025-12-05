"""Application configuration settings."""

from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application
    APP_NAME: str = "Analytics Service"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8087

    # ClickHouse
    CLICKHOUSE_HOST: str = "localhost"
    CLICKHOUSE_PORT: int = 8123
    CLICKHOUSE_USER: str = "autoseo"
    CLICKHOUSE_PASSWORD: str = "clickhouse_secret"
    CLICKHOUSE_DATABASE: str = "autoseo_analytics"

    # JWT Settings (for auth validation)
    JWT_SECRET_KEY: str = "your-jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"

    # Google Analytics 4 Settings
    GA4_CREDENTIALS_PATH: Optional[str] = None
    GA4_DEFAULT_PROPERTY_ID: Optional[str] = None

    # Google Search Console Settings
    GSC_CREDENTIALS_PATH: Optional[str] = None

    # Analytics Sync Settings
    ANALYTICS_SYNC_ENABLED: bool = True
    ANALYTICS_SYNC_HOUR: int = 2  # Run at 2 AM

    # Alerting Settings
    ALERTING_ENABLED: bool = True
    ALERT_POSITION_WARNING: float = 15.0
    ALERT_POSITION_CRITICAL: float = 20.0
    ALERT_MIN_CLICKS_30D: int = 10

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
