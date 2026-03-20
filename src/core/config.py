"""
Configuration management for transaction categorizer microservice.
"""

import os
import logging
from enum import Enum
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, HttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


logger = logging.getLogger("config")


# ────────────────────────────────────────────────
# Environment Enum (SAFER)
# ────────────────────────────────────────────────
class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class Settings(BaseSettings):
    """Application settings."""

    # Core
    APP_NAME: str = "transaction-categorizer"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False

    API_VERSION: str = "v1"
    API_PORT: int = Field(8001, ge=1024, le=65535)
    API_BASE_URL: HttpUrl = "http://localhost:8001"

    # Dependencies
    REDIS_URL: Optional[str] = None
    KAFKA_BOOTSTRAP_SERVERS: Optional[str] = None

    # Categorizer
    DEFAULT_CATEGORY: str = "Other"
    CONFIDENCE_THRESHOLD: float = Field(0.7, ge=0.0, le=1.0)

    # Security
    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production-123456",
        min_length=32
)
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8003",
    ]

    # Logging
    LOG_LEVEL: str = "INFO"

    # Dynamic env file
    model_config = SettingsConfigDict(
        env_file=f".env.{os.getenv('ENVIRONMENT', 'development')}",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=False,
    )

    # ────────────────────────────────────────────────
    # Validators
    # ────────────────────────────────────────────────


    

    @field_validator("API_BASE_URL")
    @classmethod
    def normalize_base_url(cls, v: HttpUrl) -> HttpUrl:
        return HttpUrl(str(v).rstrip("/"))



    @model_validator(mode="after")
    def validate_environment_rules(self):
        # ❌ Prevent dangerous config
        if self.ENVIRONMENT == Environment.PRODUCTION:
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production")

            if not self.REDIS_URL:
                logger.warning("REDIS_URL not set in production")

        return self


# ────────────────────────────────────────────────
# Singleton (IMPORTANT)
# ────────────────────────────────────────────────
@lru_cache
def get_settings():
    try:
        settings = Settings()
        logger.info(
            "Settings loaded",
            extra={
                "env": settings.ENVIRONMENT,
                "debug": settings.DEBUG,
            },
        )
        return settings
    except Exception:
        logger.exception("Failed to load settings")
        raise


settings = get_settings()