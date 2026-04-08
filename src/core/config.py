"""
Configuration management for transaction categorizer.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    API_VERSION: str = "v1"
    API_PORT: int = 8001
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str = Field("sqlite:///./categorizer.db", env="DATABASE_URL")
    
    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = Field("localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    KAFKA_RAW_TOPIC: str = Field("raw-transactions", env="KAFKA_RAW_TOPIC")
    KAFKA_CATEGORIZED_TOPIC: str = Field("categorized-transactions", env="KAFKA_CATEGORIZED_TOPIC")
    KAFKA_CONSUMER_GROUP: str = "transaction-categorizer"
    
    # Categorizer Settings
    DEFAULT_CATEGORY: str = "Other"
    CONFIDENCE_THRESHOLD: float = 0.7
    ENABLE_ML: bool = False
    
    # CORS - Will be parsed from string
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8003"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from environment variable."""
        if isinstance(v, str):
            # If it's a JSON array string, parse it
            if v.startswith('[') and v.endswith(']'):
                import json
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Otherwise split by comma
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()