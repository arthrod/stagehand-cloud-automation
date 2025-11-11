"""
Frontend configuration.

This module provides frontend-specific settings that are decoupled from backend configuration.
Frontend communicates with backend via API endpoints, so it only needs the API URL.
"""

from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the directory containing this config file
BASE_DIR = Path(__file__).resolve().parent


class FrontendSettings(BaseSettings):
    """Frontend-specific settings."""

    # Frontend App Settings
    APP_NAME: str = Field(default="Stagehand Frontend", description="Frontend application name")
    VERSION: str = Field(default="1.0.0", description="Frontend version")

    # Backend API Configuration
    BACKEND_API_URL: str = Field(
        default="http://localhost:8000",
        description="Backend API base URL"
    )
    BACKEND_API_TIMEOUT: int = Field(
        default=300,
        description="Backend API timeout in seconds"
    )

    # Streamlit Configuration (if using Streamlit)
    STREAMLIT_SERVER_PORT: int = Field(default=8501, description="Streamlit server port")
    STREAMLIT_SERVER_ADDRESS: str = Field(default="0.0.0.0", description="Streamlit server address")

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='allow',
        env_prefix='FRONTEND_'  # Frontend-specific env vars start with FRONTEND_
    )


@lru_cache()
def get_frontend_settings() -> FrontendSettings:
    """Get cached frontend settings instance."""
    return FrontendSettings()


# Global settings instance
frontend_settings = get_frontend_settings()

