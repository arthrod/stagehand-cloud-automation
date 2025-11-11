"""Tests for FastAPI main application."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check(self, sync_client):
        """Test basic health check endpoint."""
        response = sync_client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_readiness_check_not_ready(self, sync_client):
        """Test readiness check when not configured."""
        with patch("services.stagehand_service.StagehandService.test_connection", new=AsyncMock(return_value=False)):
            response = sync_client.get("/health/ready")

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            data = response.json()
            assert data["status"] == "not_ready"

    def test_readiness_check_ready(self, sync_client):
        """Test readiness check when ready."""
        with patch("services.stagehand_service.StagehandService.test_connection", new=AsyncMock(return_value=True)):
            response = sync_client.get("/health/ready")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "ready"


class TestActionEndpoint:
    """Test action endpoint."""

    def test_action_endpoint_success(self, sync_client):
        """Test successful action execution."""
        mock_result = {
            "success": True,
            "action": "Click button",
            "observed_elements": 2,
            "artifacts": [],
            "url": "https://example.com",
            "timestamp": "2024-01-01T00:00:00Z",
            "processing_time": 1.5,
        }

        with patch(
            "services.stagehand_service.StagehandService.perform_action_with_observe",
            new=AsyncMock(return_value=mock_result),
        ):
            response = sync_client.post(
                "/api/v1/stagehand/action",
                json={
                    "url": "https://example.com",
                    "action_instruction": "Click button",
                    "draw_overlay": False,
                    "take_screenshots": False,
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["action"] == "Click button"

    def test_action_endpoint_error(self, sync_client):
        """Test action endpoint with error."""
        with patch(
            "services.stagehand_service.StagehandService.perform_action_with_observe",
            new=AsyncMock(side_effect=Exception("Test error")),
        ):
            response = sync_client.post(
                "/api/v1/stagehand/action",
                json={
                    "url": "https://example.com",
                    "action_instruction": "Click button",
                },
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestExtractionEndpoint:
    """Test extraction endpoint."""

    def test_extraction_endpoint_success(self, sync_client):
        """Test successful data extraction."""
        mock_result = {
            "success": True,
            "data": {"name": "Product A", "price": 99.99},
            "schema": "ProductData",
            "instruction": "Extract product",
            "artifacts": [],
            "url": "https://example.com",
            "timestamp": "2024-01-01T00:00:00Z",
            "processing_time": 2.0,
        }

        with patch(
            "services.stagehand_service.StagehandService.extract_with_schema",
            new=AsyncMock(return_value=mock_result),
        ):
            response = sync_client.post(
                "/api/v1/stagehand/extract",
                json={
                    "url": "https://example.com",
                    "instruction": "Extract product",
                    "schema_name": "ProductData",
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "data" in data

    def test_extraction_endpoint_invalid_schema(self, sync_client):
        """Test extraction with invalid schema name."""
        response = sync_client.post(
            "/api/v1/stagehand/extract",
            json={
                "url": "https://example.com",
                "instruction": "Extract data",
                "schema_name": "InvalidSchema",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestWorkflowEndpoint:
    """Test workflow endpoint."""

    def test_workflow_endpoint_success(self, sync_client):
        """Test successful workflow execution."""
        mock_result = {
            "success": True,
            "workflow": "Navigate and apply",
            "result": {"completed": True},
            "url": "https://example.com",
            "timestamp": "2024-01-01T00:00:00Z",
            "processing_time": 5.0,
            "execution_method": "agent",
        }

        with patch(
            "services.stagehand_service.StagehandService.execute_workflow_with_agent",
            new=AsyncMock(return_value=mock_result),
        ):
            response = sync_client.post(
                "/api/v1/stagehand/workflow",
                json={
                    "url": "https://example.com",
                    "workflow_instruction": "Navigate and apply",
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True


class TestMultiStepEndpoint:
    """Test multi-step endpoint."""

    def test_multistep_endpoint_success(self, sync_client):
        """Test successful multi-step execution."""
        mock_result = {
            "job_id": "job_123",
            "url": "https://example.com",
            "success": True,
            "total_steps": 2,
            "completed_steps": 2,
            "steps": [
                {
                    "step_number": 1,
                    "instruction_type": "goto",
                    "instruction_text": "https://example.com",
                    "success": True,
                    "data": None,
                    "screenshot": None,
                    "error": None,
                    "error_code": None,
                    "execution_time": 1.0,
                    "timestamp": "2024-01-01T00:00:00Z",
                },
                {
                    "step_number": 2,
                    "instruction_type": "act",
                    "instruction_text": "Click button",
                    "success": True,
                    "data": None,
                    "screenshot": None,
                    "error": None,
                    "error_code": None,
                    "execution_time": 1.0,
                    "timestamp": "2024-01-01T00:00:01Z",
                },
            ],
            "total_execution_time": 3.0,
            "started_at": "2024-01-01T00:00:00Z",
            "completed_at": "2024-01-01T00:00:03Z",
        }

        with patch(
            "services.stagehand_service.StagehandService.process_multi_step_instructions",
            new=AsyncMock(return_value=mock_result),
        ):
            response = sync_client.post(
                "/api/v1/stagehand/multistep",
                json={
                    "url": "https://example.com",
                    "instructions": [
                        {"step_number": 1, "instruction_type": "goto", "instruction_text": "https://example.com"},
                        {"step_number": 2, "instruction_type": "act", "instruction_text": "Click button"},
                    ],
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["total_steps"] == 2


class TestSchemasEndpoint:
    """Test schemas listing endpoint."""

    def test_list_schemas(self, sync_client):
        """Test listing available schemas."""
        response = sync_client.get("/api/v1/stagehand/schemas")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "schemas" in data
        assert len(data["schemas"]) >= 3


class TestSimpleScreenshotEndpoint:
    """Test simple screenshot endpoint."""

    def test_screenshot_endpoint_success(self, sync_client):
        """Test successful screenshot."""
        mock_result = {
            "success": True,
            "screenshot": "base64data",
            "url": "https://example.com",
            "timestamp": "2024-01-01T00:00:00Z",
            "processing_time": 2.0,
        }

        with patch(
            "services.stagehand_service.StagehandService.take_screenshot",
            new=AsyncMock(return_value=mock_result),
        ):
            response = sync_client.post(
                "/api/v1/simple/screenshot",
                json={"url": "https://example.com"},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["screenshot"] == "base64data"

    def test_screenshot_endpoint_error(self, sync_client):
        """Test screenshot with error."""
        with patch(
            "services.stagehand_service.StagehandService.take_screenshot",
            new=AsyncMock(side_effect=Exception("Screenshot failed")),
        ):
            response = sync_client.post(
                "/api/v1/simple/screenshot",
                json={"url": "https://example.com"},
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestSimpleClickTypeEndpoint:
    """Test simple click/type endpoint."""

    def test_click_type_endpoint_success(self, sync_client):
        """Test successful click/type action."""
        mock_result = {
            "success": True,
            "action": "Clicked at (100, 200) → Typed: 'test'",
            "screenshot": None,
            "url": "https://example.com",
            "timestamp": "2024-01-01T00:00:00Z",
            "processing_time": 1.5,
        }

        with patch(
            "services.stagehand_service.StagehandService.click_type_enter",
            new=AsyncMock(return_value=mock_result),
        ):
            response = sync_client.post(
                "/api/v1/simple/click-type",
                json={
                    "url": "https://example.com",
                    "x": 100,
                    "y": 200,
                    "text": "test",
                    "press_enter": False,
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "Clicked" in data["action"]

    def test_click_type_endpoint_with_screenshot(self, sync_client):
        """Test click/type with screenshot."""
        mock_result = {
            "success": True,
            "action": "Clicked at (50, 75)",
            "screenshot": "base64screenshot",
            "url": "https://example.com",
            "timestamp": "2024-01-01T00:00:00Z",
            "processing_time": 1.5,
        }

        with patch(
            "services.stagehand_service.StagehandService.click_type_enter",
            new=AsyncMock(return_value=mock_result),
        ):
            response = sync_client.post(
                "/api/v1/simple/click-type",
                json={
                    "url": "https://example.com",
                    "x": 50,
                    "y": 75,
                    "take_screenshot": True,
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["screenshot"] == "base64screenshot"

    def test_click_type_endpoint_validation_error(self, sync_client):
        """Test click/type with invalid coordinates."""
        response = sync_client.post(
            "/api/v1/simple/click-type",
            json={
                "url": "https://example.com",
                "x": -10,  # Invalid negative coordinate
                "y": 100,
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestErrorHandlers:
    """Test error handling."""

    def test_http_exception_handler(self, sync_client):
        """Test HTTP exception handler."""
        # Trigger a 400 error by sending invalid schema name
        response = sync_client.post(
            "/api/v1/stagehand/extract",
            json={
                "url": "https://example.com",
                "instruction": "Extract",
                "schema_name": "NonExistentSchema",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    def test_validation_error(self, sync_client):
        """Test validation error handling."""
        # Missing required field
        response = sync_client.post(
            "/api/v1/stagehand/action",
            json={
                "url": "https://example.com",
                # Missing action_instruction
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_general_exception_handler(self, sync_client):
        """Test general exception handler for unhandled errors."""
        with patch(
            "services.stagehand_service.StagehandService.perform_action_with_observe",
            side_effect=Exception("Unhandled error"),
        ):
            response = sync_client.post(
                "/action",
                json={"action": "test"},
            )
            assert response.status_code == 500
            assert "error" in response.json()

    def test_general_exception_handler_with_error_code(self, sync_client):
        """Test general exception handler includes error_code when present."""

        class CustomException(Exception):
            def __init__(self, message, error_code):
                super().__init__(message)
                self.error_code = error_code

        with patch(
            "services.stagehand_service.StagehandService.perform_action_with_observe",
            side_effect=CustomException("Specific error", error_code="E1234"),
        ):
            response = sync_client.post(
                "/action",
                json={"action": "test"},
            )
            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert "error_code" in data
            assert data["error_code"] == "E1234"
            "services.stagehand_service.StagehandService.take_screenshot",
            new=AsyncMock(side_effect=RuntimeError("Unexpected error")),
        ):
            response = sync_client.post(
                "/api/v1/simple/screenshot",
                json={"url": "https://example.com"},
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
