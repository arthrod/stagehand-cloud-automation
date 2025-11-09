"""Tests for CLI."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from typer.testing import CliRunner


runner = CliRunner()


class TestCLIScreenshot:
    """Test CLI screenshot command."""

    def test_screenshot_success(self):
        """Test screenshot command success."""
        from cli import app

        mock_result = {
            "success": True,
            "screenshot": "base64data",
            "url": "https://example.com",
            "processing_time": 1.5
        }

        with patch("cli.service.take_screenshot", new=AsyncMock(return_value=mock_result)):
            result = runner.invoke(app, ["screenshot", "https://example.com"])

            assert result.exit_code == 0
            assert "Screenshot captured successfully" in result.stdout

    def test_screenshot_with_output(self, tmp_path):
        """Test screenshot command with file output."""
        from cli import app

        mock_result = {
            "success": True,
            "screenshot": "dGVzdA==",  # base64 "test"
            "url": "https://example.com",
            "processing_time": 1.5
        }

        output_file = tmp_path / "screenshot.png"

        with patch("cli.service.take_screenshot", new=AsyncMock(return_value=mock_result)):
            result = runner.invoke(app, ["screenshot", "https://example.com", "--output", str(output_file)])

            assert result.exit_code == 0
            assert "Saved to" in result.stdout
            assert output_file.exists()

    def test_screenshot_json_output(self):
        """Test screenshot command with JSON output."""
        from cli import app

        mock_result = {
            "success": True,
            "screenshot": "base64data",
            "url": "https://example.com",
            "processing_time": 1.5
        }

        with patch("cli.service.take_screenshot", new=AsyncMock(return_value=mock_result)):
            result = runner.invoke(app, ["screenshot", "https://example.com", "--json"])

            assert result.exit_code == 0
            assert "url" in result.stdout

    def test_screenshot_failure(self):
        """Test screenshot command failure."""
        from cli import app

        mock_result = {
            "success": False,
            "error": "Page load failed"
        }

        with patch("cli.service.take_screenshot", new=AsyncMock(return_value=mock_result)):
            result = runner.invoke(app, ["screenshot", "https://example.com"])

            assert result.exit_code == 1
            assert "failed" in result.stdout


class TestCLIClick:
    """Test CLI click command."""

    def test_click_success(self):
        """Test click command success."""
        from cli import app

        mock_result = {
            "success": True,
            "action": "Clicked at (100, 200)",
            "url": "https://example.com",
            "processing_time": 1.0
        }

        with patch("cli.service.click_type_enter", new=AsyncMock(return_value=mock_result)):
            result = runner.invoke(app, ["click", "https://example.com", "--x", "100", "--y", "200"])

            assert result.exit_code == 0
            assert "Action completed successfully" in result.stdout

    def test_click_with_text_and_enter(self):
        """Test click command with text and enter."""
        from cli import app

        mock_result = {
            "success": True,
            "action": "Clicked at (100, 200) → Typed: 'test' → Pressed Enter",
            "url": "https://example.com",
            "processing_time": 1.5
        }

        with patch("cli.service.click_type_enter", new=AsyncMock(return_value=mock_result)):
            result = runner.invoke(
                app,
                ["click", "https://example.com", "--x", "100", "--y", "200", "--text", "test", "--enter"]
            )

            assert result.exit_code == 0
            assert "Action completed" in result.stdout


class TestCLIAction:
    """Test CLI action command."""

    def test_action_success(self):
        """Test action command success."""
        from cli import app

        mock_result = {
            "success": True,
            "action": "Click button",
            "observed_elements": 3,
            "url": "https://example.com",
            "processing_time": 2.0
        }

        with patch("cli.service.perform_action_with_observe", new=AsyncMock(return_value=mock_result)):
            result = runner.invoke(app, ["action", "https://example.com", "Click the sign in button"])

            assert result.exit_code == 0
            assert "Action completed" in result.stdout
            assert "Observed elements: 3" in result.stdout

    def test_action_with_screenshot(self):
        """Test action command with screenshot."""
        from cli import app

        mock_result = {
            "success": True,
            "action": "Click button",
            "observed_elements": 2,
            "url": "https://example.com",
            "processing_time": 2.0
        }

        with patch("cli.service.perform_action_with_observe", new=AsyncMock(return_value=mock_result)):
            result = runner.invoke(
                app,
                ["action", "https://example.com", "Click button", "--screenshot"]
            )

            assert result.exit_code == 0


class TestCLIExtract:
    """Test CLI extract command."""

    def test_extract_success(self):
        """Test extract command success."""
        from cli import app

        mock_result = {
            "success": True,
            "data": {"name": "Product A", "price": 99.99, "rating": 4.5, "in_stock": True},
            "url": "https://example.com",
            "processing_time": 2.5
        }

        with patch("cli.service.extract_with_schema", new=AsyncMock(return_value=mock_result)):
            result = runner.invoke(
                app,
                ["extract", "https://example.com", "Extract product data"]
            )

            assert result.exit_code == 0
            assert "Data extracted successfully" in result.stdout

    def test_extract_with_custom_schema(self):
        """Test extract command with custom schema."""
        from cli import app

        mock_result = {
            "success": True,
            "data": {"title": "Engineer", "company": "TechCo"},
            "url": "https://example.com",
            "processing_time": 2.0
        }

        with patch("cli.service.extract_with_schema", new=AsyncMock(return_value=mock_result)):
            result = runner.invoke(
                app,
                ["extract", "https://example.com", "Extract job", "--schema", "JobPosting"]
            )

            assert result.exit_code == 0

    def test_extract_invalid_schema(self):
        """Test extract command with invalid schema."""
        from cli import app

        result = runner.invoke(
            app,
            ["extract", "https://example.com", "Extract", "--schema", "InvalidSchema"]
        )

        assert result.exit_code == 1
        assert "Unknown schema" in result.stdout


class TestCLIWorkflow:
    """Test CLI workflow command."""

    def test_workflow_success(self):
        """Test workflow command success."""
        from cli import app

        mock_result = {
            "success": True,
            "workflow": "Apply to jobs",
            "result": {"completed": True, "jobs_applied": 3},
            "url": "https://example.com",
            "processing_time": 15.0,
            "execution_method": "agent"
        }

        with patch("cli.service.execute_workflow_with_agent", new=AsyncMock(return_value=mock_result)):
            result = runner.invoke(
                app,
                ["workflow", "https://example.com", "Apply to software engineer positions"]
            )

            assert result.exit_code == 0
            assert "Workflow completed" in result.stdout

    def test_workflow_with_custom_params(self):
        """Test workflow command with custom parameters."""
        from cli import app

        mock_result = {
            "success": True,
            "workflow": "Complex task",
            "result": {},
            "url": "https://example.com",
            "processing_time": 20.0
        }

        with patch("cli.service.execute_workflow_with_agent", new=AsyncMock(return_value=mock_result)):
            result = runner.invoke(
                app,
                ["workflow", "https://example.com", "Do task", "--max-steps", "50", "--wait", "2000"]
            )

            assert result.exit_code == 0


class TestCLIInfo:
    """Test CLI info command."""

    def test_info_command(self):
        """Test info command."""
        from cli import app

        result = runner.invoke(app, ["info"])

        assert result.exit_code == 0
        assert "Stagehand AI Automation CLI" in result.stdout
        assert "Capabilities" in result.stdout


class TestCLIHelpers:
    """Test CLI helper functions."""

    def test_run_async(self):
        """Test run_async helper."""
        from cli import run_async

        async def test_coro():
            return "test"

        result = run_async(test_coro())
        assert result == "test"
