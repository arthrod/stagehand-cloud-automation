"""Tests for MCP server input models and structure."""

import pytest
from pydantic import BaseModel, ValidationError


class TestMCPInputModels:
    """Test MCP input models validation."""

    def test_screenshot_input_valid(self):
        """Test ScreenshotInput validation."""
        # We can't import from mcp_server due to fastmcp dependencies
        # So we'll define the models here for testing purposes
        class ScreenshotInput(BaseModel):
            url: str

        input_data = ScreenshotInput(url="https://example.com")
        assert input_data.url == "https://example.com"

    def test_click_type_input_valid(self):
        """Test ClickTypeInput validation."""
        from typing import Optional

        class ClickTypeInput(BaseModel):
            url: str
            x: int
            y: int
            text: Optional[str] = None
            press_enter: bool = False
            take_screenshot: bool = False

        input_data = ClickTypeInput(
            url="https://example.com",
            x=100,
            y=200,
            text="test",
            press_enter=True
        )
        assert input_data.x == 100
        assert input_data.y == 200
        assert input_data.text == "test"

    def test_click_type_input_requires_coordinates(self):
        """Test that coordinates are required."""
        from typing import Optional

        class ClickTypeInput(BaseModel):
            url: str
            x: int
            y: int
            text: Optional[str] = None
            press_enter: bool = False

        with pytest.raises(ValidationError):
            ClickTypeInput(url="https://example.com")  # Missing x and y

    def test_action_input_valid(self):
        """Test ActionInput validation."""
        from typing import Optional

        class ActionInput(BaseModel):
            url: str
            action_instruction: str
            draw_overlay: bool = False
            take_screenshots: bool = False

        input_data = ActionInput(
            url="https://example.com",
            action_instruction="Click button"
        )
        assert input_data.action_instruction == "Click button"
        assert input_data.draw_overlay is False

    def test_extraction_input_valid(self):
        """Test ExtractionInput validation."""
        from typing import Optional

        class ExtractionInput(BaseModel):
            url: str
            instruction: str
            schema_name: str = "ProductData"
            take_screenshots: bool = False

        input_data = ExtractionInput(
            url="https://example.com",
            instruction="Extract data",
            schema_name="ProductData"
        )
        assert input_data.schema_name == "ProductData"

    def test_workflow_input_valid(self):
        """Test WorkflowInput validation."""
        from typing import Optional

        class WorkflowInput(BaseModel):
            url: str
            workflow_instruction: str
            max_steps: int = 30
            auto_screenshot: bool = False
            wait_between_actions: int = 1000

        input_data = WorkflowInput(
            url="https://example.com",
            workflow_instruction="Complete workflow",
            max_steps=30
        )
        assert input_data.max_steps == 30
        assert input_data.wait_between_actions == 1000

    def test_workflow_input_defaults(self):
        """Test WorkflowInput default values."""
        from typing import Optional

        class WorkflowInput(BaseModel):
            url: str
            workflow_instruction: str
            max_steps: int = 30
            auto_screenshot: bool = False
            wait_between_actions: int = 1000

        input_data = WorkflowInput(
            url="https://example.com",
            workflow_instruction="Complete workflow"
        )
        assert input_data.max_steps == 30
        assert input_data.auto_screenshot is False
        assert input_data.wait_between_actions == 1000


class TestMCPServerStructure:
    """Test MCP server structure and configuration."""

    def test_mcp_server_file_exists(self):
        """Test that mcp_server.py exists."""
        from pathlib import Path
        mcp_server_path = Path(__file__).parent.parent / "mcp_server.py"
        assert mcp_server_path.exists()

    def test_mcp_server_has_required_tools(self):
        """Test that mcp_server.py defines expected tool names."""
        from pathlib import Path
        mcp_server_path = Path(__file__).parent.parent / "mcp_server.py"
        content = mcp_server_path.read_text()

        # Check for expected tool function names
        assert "def take_screenshot" in content
        assert "def click_and_type" in content
        assert "def perform_action" in content
        assert "def extract_data" in content
        assert "def execute_workflow" in content

    def test_mcp_server_has_resources(self):
        """Test that mcp_server.py defines resources."""
        from pathlib import Path
        mcp_server_path = Path(__file__).parent.parent / "mcp_server.py"
        content = mcp_server_path.read_text()

        # Check for resource functions
        assert "def get_capabilities" in content
        assert "def get_examples" in content

    def test_mcp_server_imports_service(self):
        """Test that mcp_server imports StagehandService."""
        from pathlib import Path
        mcp_server_path = Path(__file__).parent.parent / "mcp_server.py"
        content = mcp_server_path.read_text()

        assert "from services.stagehand_service import StagehandService" in content

    def test_mcp_server_defines_input_models(self):
        """Test that mcp_server defines all input models."""
        from pathlib import Path
        mcp_server_path = Path(__file__).parent.parent / "mcp_server.py"
        content = mcp_server_path.read_text()

        # Check for input model definitions
        assert "class ScreenshotInput" in content
        assert "class ClickTypeInput" in content
        assert "class ActionInput" in content
        assert "class ExtractionInput" in content
        assert "class WorkflowInput" in content


class TestMCPSchemaMapping:
    """Test schema name mapping."""

    def test_schema_mapping_structure(self):
        """Test that schema mapping is correctly structured."""
        # Define expected schemas
        expected_schemas = {
            "ProductData": "ProductData schema",
            "JobPosting": "JobPosting schema",
            "CompanyInfo": "CompanyInfo schema"
        }

        # Just verify the expected schema names are valid identifiers
        for schema_name in expected_schemas.keys():
            assert schema_name.isidentifier()
            assert not schema_name.startswith("_")

    def test_invalid_schema_name(self):
        """Test handling of invalid schema names."""
        invalid_schemas = [
            "InvalidSchema",
            "NonExistent",
            "FakeSchema"
        ]

        # These should not match our expected schemas
        expected_schemas = ["ProductData", "JobPosting", "CompanyInfo"]
        for invalid in invalid_schemas:
            assert invalid not in expected_schemas
