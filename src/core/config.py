# transaction-categorizer/src/core/config.py

import os
from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings"""

    PORT: int = int(os.getenv("PORT", 8009))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # RabbitMQ
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT", 5672))
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "guest")

    # Service URLs
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
    TENANT_SERVICE_URL: str = os.getenv("TENANT_SERVICE_URL", "http://localhost:8002")
    ANALYTICS_SERVICE_URL: str = os.getenv(
        "ANALYTICS_SERVICE_URL", "http://localhost:8003"
    )
    PARSER_SERVICE_URL: str = os.getenv("PARSER_SERVICE_URL", "http://localhost:8004")
    CASHFLOW_SERVICE_URL: str = os.getenv(
        "CASHFLOW_SERVICE_URL", "http://localhost:8005"
    )
    TRANSACTION_SERVICE_URL: str = os.getenv(
        "TRANSACTION_SERVICE_URL", "http://localhost:8006"
    )
    PAYMENT_SERVICE_URL: str = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8007")
    BILLING_SERVICE_URL: str = os.getenv("BILLING_SERVICE_URL", "http://localhost:8008")
    CATEGORIZER_SERVICE_URL: str = os.getenv(
        "CATEGORIZER_SERVICE_URL", "http://localhost:8009"
    )
    WEBHOOK_SERVICE_URL: str = os.getenv("WEBHOOK_SERVICE_URL", "http://localhost:8010")

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8003",
        "http://localhost:9000",
        "http://localhost:8009",
    ]

    # JWT
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "mpesa-super-secure-platform-secret-2024"
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    # Categorization
    MIN_CONFIDENCE_THRESHOLD: float = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", 0.6))
    MAX_RULES_PER_TENANT: int = int(os.getenv("MAX_RULES_PER_TENANT", 100))
    ENABLE_AUTO_CATEGORIZATION: bool = (
        os.getenv("ENABLE_AUTO_CATEGORIZATION", "True").lower() == "true"
    )

    # Cache
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", 300))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
