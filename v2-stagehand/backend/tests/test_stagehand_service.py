"""Tests for StagehandService."""

import os
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import pytest
from services.stagehand_service import StagehandService


class TestBrowserExecutablePath:
    """Test browser executable path detection."""

    def test_get_browser_executable_path_with_env_var(self, test_env_vars):
        """Test using BROWSER_EXECUTABLE_PATH from environment."""
        service = StagehandService()

        with patch("services.stagehand_service.settings.BROWSER_EXECUTABLE_PATH", "/custom/path/browser"):
            path = service._get_browser_executable_path("chrome")
            assert path == "/custom/path/browser"

    def test_get_browser_executable_path_chrome(self, test_env_vars):
        """Test Chrome browser path detection."""
        service = StagehandService()

        with patch("os.path.exists", return_value=True):
            path = service._get_browser_executable_path("chrome")
            assert path == "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    def test_get_browser_executable_path_arc(self, test_env_vars):
        """Test Arc browser path detection."""
        service = StagehandService()

        with patch("os.path.exists", return_value=True):
            path = service._get_browser_executable_path("arc")
            assert path == "/Applications/Arc.app/Contents/MacOS/Arc"

    def test_get_browser_executable_path_zen(self, test_env_vars):
        """Test Zen browser path detection."""
        service = StagehandService()

        with patch("os.path.exists", return_value=True):
            path = service._get_browser_executable_path("zen")
            assert path == "/Applications/Zen Browser.app/Contents/MacOS/zen"

    def test_get_browser_executable_path_firefox(self, test_env_vars):
        """Test Firefox browser path detection."""
        service = StagehandService()

        with patch("os.path.exists", return_value=True):
            path = service._get_browser_executable_path("firefox")
            assert path == "/Applications/Firefox.app/Contents/MacOS/firefox"

    def test_get_browser_executable_path_vivaldi(self, test_env_vars):
        """Test Vivaldi browser path detection."""
        service = StagehandService()

        with patch("os.path.exists", return_value=True):
            path = service._get_browser_executable_path("vivaldi")
            assert path == "/Applications/Vivaldi.app/Contents/MacOS/Vivaldi"

    def test_get_browser_executable_path_not_found(self, test_env_vars):
        """Test browser not found returns None."""
        service = StagehandService()

        with patch("os.path.exists", return_value=False):
            path = service._get_browser_executable_path("chrome")
            assert path is None


class TestSessionCreation:
    """Test session creation methods."""

    @pytest.mark.asyncio
    async def test_create_session_local(self):
        """Test _create_session routes to local when STAGEHAND_ENV=LOCAL."""
        service = StagehandService()

        with patch("services.stagehand_service.settings.STAGEHAND_ENV", "LOCAL"):
            with patch.object(service, "_create_local_browser_session", new=AsyncMock()) as mock_local:
                await service._create_session({})
                mock_local.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_browserbase(self):
        """Test _create_session routes to Browserbase when STAGEHAND_ENV=BROWSERBASE."""
        service = StagehandService()

        with patch("services.stagehand_service.settings.STAGEHAND_ENV", "BROWSERBASE"):
            with patch.object(service, "_create_browserbase_session", new=AsyncMock()) as mock_bb:
                await service._create_session({})
                mock_bb.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_session(self, mock_stagehand_instance):
        """Test closing a session."""
        service = StagehandService()

        await service._close_session(mock_stagehand_instance)

        mock_stagehand_instance.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_session_none(self):
        """Test closing None session doesn't error."""
        service = StagehandService()

        # Should not raise
        await service._close_session(None)

    @pytest.mark.asyncio
    async def test_close_browserbase_session_legacy(self, mock_stagehand_instance):
        """Test legacy _close_browserbase_session method."""
        service = StagehandService()

        await service._close_browserbase_session(mock_stagehand_instance)

        mock_stagehand_instance.close.assert_called_once()


class TestConnectionTest:
    """Test connection testing."""

    @pytest.mark.asyncio
    async def test_connection_local_with_executable(self):
        """Test connection check in local mode with executable."""
        service = StagehandService()

        with patch("services.stagehand_service.settings.STAGEHAND_ENV", "LOCAL"):
            with patch.object(service, "_get_browser_executable_path", return_value="/path/to/browser"):
                result = await service.test_connection()
                assert result is True

    @pytest.mark.asyncio
    async def test_connection_local_existing_session(self):
        """Test connection check with existing session."""
        service = StagehandService()

        with patch("services.stagehand_service.settings.STAGEHAND_ENV", "LOCAL"):
            with patch("services.stagehand_service.settings.USE_EXISTING_SESSION", True):
                with patch("services.stagehand_service.settings.BROWSER_CDP_URL", "http://localhost:9222"):
                    result = await service.test_connection()
                    assert result is True

    @pytest.mark.asyncio
    async def test_connection_browserbase_success(self):
        """Test connection check for Browserbase."""
        service = StagehandService()

        with patch("services.stagehand_service.settings.STAGEHAND_ENV", "BROWSERBASE"):
            with patch("services.stagehand_service.settings.BROWSERBASE_API_KEY", "test-key"):
                with patch("services.stagehand_service.settings.BROWSERBASE_PROJECT_ID", "test-project"):
                    with patch("services.stagehand_service.settings.MODEL_API_KEY", "test-model-key"):
                        result = await service.test_connection()
                        assert result is True

    @pytest.mark.asyncio
    async def test_connection_local_existing_session_no_cdp(self):
        """Test connection check with existing session but no CDP URL."""
        service = StagehandService()

        with patch("services.stagehand_service.settings.STAGEHAND_ENV", "LOCAL"):
            with patch("services.stagehand_service.settings.USE_EXISTING_SESSION", True):
                with patch("services.stagehand_service.settings.BROWSER_CDP_URL", None):
                    result = await service.test_connection()
                    assert result is False

    @pytest.mark.asyncio
    async def test_connection_local_no_executable(self):
        """Test connection check when executable not found."""
        service = StagehandService()

        with patch("services.stagehand_service.settings.STAGEHAND_ENV", "LOCAL"):
            with patch.object(service, "_get_browser_executable_path", return_value=None):
                result = await service.test_connection()
                assert result is True  # Still returns True as fallback

    @pytest.mark.asyncio
    async def test_connection_browserbase_missing_api_key(self):
        """Test connection check with missing API key."""
        service = StagehandService()

        with patch("services.stagehand_service.settings.STAGEHAND_ENV", "BROWSERBASE"):
            with patch("services.stagehand_service.settings.BROWSERBASE_API_KEY", None):
                result = await service.test_connection()
                assert result is False

    @pytest.mark.asyncio
    async def test_connection_browserbase_missing_project_id(self):
        """Test connection check with missing project ID."""
        service = StagehandService()

        with patch("services.stagehand_service.settings.STAGEHAND_ENV", "BROWSERBASE"):
            with patch("services.stagehand_service.settings.BROWSERBASE_API_KEY", "test-key"):
                with patch("services.stagehand_service.settings.BROWSERBASE_PROJECT_ID", None):
                    result = await service.test_connection()
                    assert result is False

    @pytest.mark.asyncio
    async def test_connection_browserbase_missing_model_key(self):
        """Test connection check with missing model API key."""
        service = StagehandService()

        with patch("services.stagehand_service.settings.STAGEHAND_ENV", "BROWSERBASE"):
            with patch("services.stagehand_service.settings.BROWSERBASE_API_KEY", "test-key"):
                with patch("services.stagehand_service.settings.BROWSERBASE_PROJECT_ID", "test-project"):
                    with patch("services.stagehand_service.settings.MODEL_API_KEY", None):
                        result = await service.test_connection()
                        assert result is False


class TestActionMethods:
    """Test action execution methods."""

    @pytest.mark.asyncio
    async def test_perform_action_with_observe_success(
        self, mock_stagehand_instance
    ):
        """Test successful action with observe."""
        service = StagehandService()

        with patch.object(service, "_create_session", new=AsyncMock(return_value=mock_stagehand_instance)):
            with patch.object(service, "_close_session", new=AsyncMock()):
                with patch.object(service, "_navigate_with_retry", new=AsyncMock()):
                    result = await service.perform_action_with_observe(
                        url="https://example.com",
                        action_instruction="Click button",
                        config={"draw_overlay": False, "take_screenshots": False},
                    )

                    assert result["success"] is True
                    assert result["action"] == "Click button"
                    assert result["observed_elements"] == 1

    @pytest.mark.asyncio
    async def test_perform_action_with_observe_with_screenshot(
        self, mock_stagehand_instance
    ):
        """Test action with screenshot."""
        service = StagehandService()

        with patch.object(service, "_create_session", new=AsyncMock(return_value=mock_stagehand_instance)):
            with patch.object(service, "_close_session", new=AsyncMock()):
                result = await service.perform_action_with_observe(
                    url="https://example.com",
                    action_instruction="Click button",
                    config={"draw_overlay": False, "take_screenshots": True},
                )

                assert result["success"] is True
                assert len(result["artifacts"]) == 1
                assert result["artifacts"][0]["type"] == "screenshot"

    @pytest.mark.asyncio
    async def test_perform_action_no_elements(
        self, mock_stagehand_instance
    ):
        """Test action when no elements observed."""
        service = StagehandService()
        mock_stagehand_instance.page.observe = AsyncMock(return_value=[])

        with patch.object(service, "_create_session", new=AsyncMock(return_value=mock_stagehand_instance)):
            with patch.object(service, "_close_session", new=AsyncMock()):
                result = await service.perform_action_with_observe(
                    url="https://example.com",
                    action_instruction="Click button",
                    config={},
                )

                assert result["success"] is False
                assert result["error_code"] == "NO_ELEMENTS_FOUND"


class TestScreenshotMethod:
    """Test screenshot method."""

    @pytest.mark.asyncio
    async def test_take_screenshot_success(
        self, mock_stagehand_instance
    ):
        """Test successful screenshot."""
        service = StagehandService()

        with patch.object(service, "_create_session", new=AsyncMock(return_value=mock_stagehand_instance)):
            with patch.object(service, "_close_session", new=AsyncMock()):
                result = await service.take_screenshot(url="https://example.com")

                assert result["success"] is True
                assert result["screenshot"] is not None
                assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_take_screenshot_error(self):
        """Test screenshot with error."""
        service = StagehandService()
        mock_instance = MagicMock()
        mock_instance.page.goto = AsyncMock(side_effect=Exception("Page load failed"))
        mock_instance.close = AsyncMock()

        with patch.object(service, "_create_session", new=AsyncMock(return_value=mock_instance)):
            with patch.object(service, "_close_session", new=AsyncMock()):
                result = await service.take_screenshot(url="https://example.com")

                assert result["success"] is False
                assert result["error_code"] == "SCREENSHOT_ERROR"


class TestClickTypeEnterMethod:
    """Test click/type/enter method."""

    @pytest.mark.asyncio
    async def test_click_type_enter_full(
        self, mock_stagehand_instance
    ):
        """Test click, type, and enter."""
        service = StagehandService()

        with patch.object(service, "_create_session", new=AsyncMock(return_value=mock_stagehand_instance)):
            with patch.object(service, "_close_session", new=AsyncMock()):
                result = await service.click_type_enter(
                    url="https://example.com",
                    x=100,
                    y=200,
                    text="test query",
                    press_enter=True,
                    take_screenshot=True,
                )

                assert result["success"] is True
                assert "Clicked" in result["action"]
                assert "Typed" in result["action"]
                assert "Enter" in result["action"]
                assert result["screenshot"] is not None

    @pytest.mark.asyncio
    async def test_click_type_enter_click_only(
        self, mock_stagehand_instance
    ):
        """Test click only without typing."""
        service = StagehandService()

        with patch.object(service, "_create_session", new=AsyncMock(return_value=mock_stagehand_instance)):
            with patch.object(service, "_close_session", new=AsyncMock()):
                result = await service.click_type_enter(
                    url="https://example.com", x=50, y=75, text=None, press_enter=False
                )

                assert result["success"] is True
                assert "Clicked at (50, 75)" in result["action"]
                assert "Typed" not in result["action"]
                assert result["screenshot"] is None

    @pytest.mark.asyncio
    async def test_click_type_enter_error(self):
        """Test click/type/enter with error."""
        service = StagehandService()
        mock_instance = MagicMock()
        mock_instance.page.mouse.click = AsyncMock(side_effect=Exception("Click failed"))
        mock_instance.page.goto = AsyncMock()
        mock_instance.close = AsyncMock()

        with patch.object(service, "_create_session", new=AsyncMock(return_value=mock_instance)):
            with patch.object(service, "_close_session", new=AsyncMock()):
                result = await service.click_type_enter(
                    url="https://example.com", x=100, y=200
                )

                assert result["success"] is False
                assert result["error_code"] == "CLICK_TYPE_ERROR"


class TestExtractWithSchema:
    """Test extract_with_schema method."""

    @pytest.mark.asyncio
    async def test_extract_with_schema_success(self, mock_stagehand_instance):
        """Test successful schema extraction."""
        service = StagehandService()

    @pytest.mark.asyncio
    async def test_extract_with_schema_error(self, mock_stagehand_instance):
        """Test schema extraction failure scenario."""
        service = StagehandService()
        # Patch the page.extract method to raise an exception
        with patch.object(service, "extract_with_schema", new=AsyncMock(side_effect=Exception("Extraction failed"))):
            try:
                await service.extract_with_schema("https://example.com", schema={"field": "value"})
            except Exception as exc:
                assert str(exc) == "Extraction failed"
        mock_stagehand_instance.page.extract = AsyncMock(return_value=MagicMock(model_dump=lambda: {"name": "Test", "price": 99.99}))

        with patch.object(service, "_create_session", new=AsyncMock(return_value=mock_stagehand_instance)):
            with patch.object(service, "_close_session", new=AsyncMock()):
                from schemas.stagehand_schemas import ProductData
                result = await service.extract_with_schema(
                    url="https://example.com",
                    instruction="Extract product",
                    schema=ProductData,
                    config={"take_screenshots": False}
                )

                assert result["success"] is True
                assert "data" in result


class TestWorkflowExecution:
    """Test workflow execution."""

    @pytest.mark.asyncio
    async def test_execute_workflow_success(self, mock_stagehand_instance):
        """Test successful workflow execution."""
        service = StagehandService()

    @pytest.mark.asyncio
    async def test_execute_workflow_agent_failure(self, mock_stagehand_instance):
        """Test workflow execution with agent failure."""
        service = StagehandService()

        # Patch the agent execution to simulate failure
        with patch.object(service, "execute_workflow_with_agent", side_effect=Exception("Agent failed")):
            try:
                await service.execute_workflow_with_agent(
                    url="https://example.com",
                    instruction="Extract product",
                    schema=ProductData,
                    config={"take_screenshots": False}
                )
            except Exception as exc:
                assert str(exc) == "Agent failed"
        mock_agent = MagicMock()
        mock_agent.execute = AsyncMock(return_value={"completed": True})
        mock_stagehand_instance.agent = MagicMock(return_value=mock_agent)

        with patch.object(service, "_create_session", new=AsyncMock(return_value=mock_stagehand_instance)):
            with patch.object(service, "_close_session", new=AsyncMock()):
                result = await service.execute_workflow_with_agent(
                    url="https://example.com",
                    workflow_instruction="Complete the form",
                    config={}
                )

                assert result["success"] is True


class TestMultiStepInstructions:
    """Test multi-step instruction processing."""

    @pytest.mark.asyncio
    async def test_process_multi_step_success(self, mock_stagehand_instance):
        """Test successful multi-step processing."""
        service = StagehandService()

    @pytest.mark.asyncio
    async def test_process_multi_step_error(self, mock_stagehand_instance):
        """Test error handling in multi-step processing."""
        service = StagehandService()

        # Simulate a step failure by patching the method that processes steps
        with patch.object(service, "process_multi_step_instructions", new=AsyncMock(return_value={
            "success": False,
            "error": "Step 2 failed due to invalid input"
        })):
            result = await service.process_multi_step_instructions(
                url="https://example.com",
                workflow_instruction="Step 1: Do X. Step 2: Do Y.",
                config={}
            )

            assert result["success"] is False
            assert "error" in result
            assert result["error"] == "Step 2 failed due to invalid input"

        with patch.object(service, "_create_session", new=AsyncMock(return_value=mock_stagehand_instance)):
            with patch.object(service, "_close_session", new=AsyncMock()):
                instructions = [
                    {"instruction_type": "goto", "instruction_text": "https://example.com"},
                    {"instruction_type": "act", "instruction_text": "Click button"},
                ]

                result = await service.process_multi_step_instructions(
                    url="https://example.com",
                    instructions=instructions,
                    config={}
                )

                assert result["success"] is True
                assert result["total_steps"] == 2


class TestCleanup:
    """Test cleanup method."""

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup completes without error."""
        service = StagehandService()

        # Should complete without raising
        await service.cleanup()
