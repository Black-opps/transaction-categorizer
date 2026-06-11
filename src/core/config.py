# src/core/config.py
"""
Configuration management for transaction categorizer - MVP Hardened
"""

from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings - MVP focused."""

    # API Settings
    API_VERSION: str = "v1"
    API_PORT: int = 8009
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database (PostgreSQL for consistency with parser)
    DATABASE_URL: str = Field(
        "postgresql://postgres:Playee103@localhost:5432/parser_db", env="DATABASE_URL"
    )

    # RabbitMQ (already using, keep it)
    RABBITMQ_URL: str = Field("amqp://localhost:5672/", env="RABBITMQ_URL")

    # Service URLs
    CASHFLOW_SERVICE_URL: str = Field(
        "http://localhost:8005", env="CASHFLOW_SERVICE_URL"
    )
    TRANSACTION_SERVICE_URL: str = Field(
        "http://localhost:8006/api/v1/transactions", env="TRANSACTION_SERVICE_URL"
    )

    # Categorizer Settings
    DEFAULT_CATEGORY: str = "Other"
    CONFIDENCE_THRESHOLD: float = 0.7
    ENABLE_ML: bool = False

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8003",
        "http://localhost:8006",
    ]

    # Logging
    LOG_LEVEL: str = "INFO"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json

                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
