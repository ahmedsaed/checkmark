"""
Application configuration using pydantic-settings.

Loads environment variables from .env file and provides type-safe access
to all configuration values.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "checkmark"

    # AI Model Integration
    openrouter_api_key: str = ""
    litellm_api_key: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Admin Authentication
    admin_username: str = "admin"
    admin_password: str = "changeme"

    # CORS
    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


# Singleton settings instance
settings = Settings()
