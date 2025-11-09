"""Tests for configuration module."""

import os
import pytest
from config import Settings, get_settings


def test_settings_defaults():
    """Test default settings values."""
    settings = Settings()

    assert settings.APP_NAME == "AI Web Scraper API"
    assert settings.VERSION == "1.0.0"
    assert settings.ENVIRONMENT == "development"
    assert settings.DEBUG is False
    assert settings.VERBOSE == 1
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8000


def test_settings_browser_defaults():
    """Test browser configuration defaults."""
    settings = Settings()

    assert settings.STAGEHAND_ENV == "BROWSERBASE"
    assert settings.BROWSER_TYPE == "chrome"
    assert settings.USE_EXISTING_SESSION is False
    assert settings.HEADLESS is True
    assert settings.DOM_SETTLE_TIMEOUT_MS == 30000
    assert settings.SELF_HEAL is True


def test_settings_from_env(test_env_vars):
    """Test settings loaded from environment variables."""
    settings = Settings()

    assert settings.STAGEHAND_ENV == "LOCAL"
    assert settings.BROWSER_TYPE == "chrome"
    assert settings.VERBOSE == 1
    assert settings.MODEL_API_KEY == "test-api-key"


def test_get_settings_singleton():
    """Test that get_settings returns a singleton instance."""
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2


def test_cors_origins():
    """Test CORS origins configuration."""
    settings = Settings()

    assert isinstance(settings.CORS_ORIGINS, list)
    assert len(settings.CORS_ORIGINS) > 0


def test_browser_type_validation():
    """Test that browser type can be set to supported values."""
    for browser in ["chrome", "arc", "zen", "firefox", "vivaldi"]:
        settings = Settings(BROWSER_TYPE=browser)
        assert settings.BROWSER_TYPE == browser


def test_optional_fields():
    """Test optional configuration fields."""
    settings = Settings()

    # These can be None
    assert settings.BROWSERBASE_API_KEY is None or isinstance(settings.BROWSERBASE_API_KEY, str)
    assert settings.BROWSER_EXECUTABLE_PATH is None or isinstance(settings.BROWSER_EXECUTABLE_PATH, str)
    assert settings.BROWSER_CDP_URL is None or isinstance(settings.BROWSER_CDP_URL, str)
