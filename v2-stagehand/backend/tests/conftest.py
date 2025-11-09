"""Test configuration and fixtures."""

import os
import sys
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add parent directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Mock stagehand imports before they're needed
sys.modules['stagehand'] = MagicMock()


@pytest.fixture(scope="session")
def test_env_vars():
    """Set up test environment variables."""
    test_vars = {
        "STAGEHAND_ENV": "LOCAL",
        "BROWSER_TYPE": "chrome",
        "USE_EXISTING_SESSION": "false",
        "BROWSER_CDP_URL": "http://localhost:9222",
        "VERBOSE": "1",
        "DOM_SETTLE_TIMEOUT_MS": "30000",
        "SELF_HEAL": "true",
        "HEADLESS": "true",
        "MODEL_API_KEY": "test-api-key",
        "MODEL_NAME": "test-model",
        "HOST": "0.0.0.0",
        "PORT": "8000",
        "LOG_LEVEL": "INFO",
    }

    # Store original values
    original_vars = {}
    for key, value in test_vars.items():
        original_vars[key] = os.environ.get(key)
        os.environ[key] = value

    yield test_vars

    # Restore original values
    for key, original_value in original_vars.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture
def mock_stagehand_instance():
    """Create a mock Stagehand instance."""
    mock_stagehand = MagicMock()
    mock_page = MagicMock()

    # Setup page mock
    mock_page.goto = AsyncMock()
    mock_page.observe = AsyncMock(return_value=[{"element": "button"}])
    mock_page.act = AsyncMock()
    mock_page.extract = AsyncMock(return_value={"data": "test"})
    mock_page.screenshot = AsyncMock(return_value=b"fake_screenshot_data")
    mock_page.mouse = MagicMock()
    mock_page.mouse.click = AsyncMock()
    mock_page.keyboard = MagicMock()
    mock_page.keyboard.type = AsyncMock()
    mock_page.keyboard.press = AsyncMock()

    mock_stagehand.page = mock_page
    mock_stagehand.close = AsyncMock()
    mock_stagehand.init = AsyncMock()

    return mock_stagehand


@pytest.fixture
def mock_stagehand_modules(mock_stagehand_instance):
    """Mock Stagehand and StagehandConfig."""
    mock_stagehand_class = MagicMock(return_value=mock_stagehand_instance)
    mock_config_class = MagicMock()

    # Mock the module-level imports in stagehand_service
    def mock_import(name, *args, **kwargs):
        if 'stagehand' in name:
            mock_module = MagicMock()
            mock_module.Stagehand = mock_stagehand_class
            mock_module.StagehandConfig = mock_config_class
            return mock_module
        return original_import(name, *args, **kwargs)

    original_import = __builtins__.__import__

    with patch("builtins.__import__", side_effect=mock_import):
        yield {
            "stagehand_class": mock_stagehand_class,
            "config_class": mock_config_class
        }


@pytest.fixture
def mock_stagehand_config():
    """Create a mock StagehandConfig class."""
    return MagicMock()


@pytest.fixture
def mock_stagehand_class(mock_stagehand_instance):
    """Create a mock Stagehand class."""
    return MagicMock(return_value=mock_stagehand_instance)


@pytest.fixture
async def app_client(test_env_vars):
    """Create a test client for the FastAPI app."""
    # Import after environment is set up
    from main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def sync_client(test_env_vars):
    """Create a synchronous test client."""
    from main import app

    with TestClient(app) as client:
        yield client
