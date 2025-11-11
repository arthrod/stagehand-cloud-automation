"""Tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError
from schemas.stagehand_schemas import (
    ActionRequest,
    ActionResponse,
    ScreenshotRequest,
    ScreenshotResponse,
    ClickTypeRequest,
    ClickTypeResponse,
    ExtractionRequest,
    ExtractionResponse,
    WorkflowRequest,
    WorkflowResponse,
    ProductData,
    JobPosting,
    CompanyInfo,
    get_extraction_schema,
)
from schemas.common import HealthResponse


class TestActionSchemas:
    """Test Action request/response schemas."""

    def test_action_request_valid(self):
        """Test valid ActionRequest."""
        request = ActionRequest(
            url="https://example.com",
            action_instruction="Click the button",
            draw_overlay=True,
            take_screenshots=True
        )

        assert request.url == "https://example.com"
        assert request.action_instruction == "Click the button"
        assert request.draw_overlay is True
        assert request.take_screenshots is True

    def test_action_request_defaults(self):
        """Test ActionRequest with default values."""
        request = ActionRequest(
            url="https://example.com",
            action_instruction="Click the button"
        )

        assert request.draw_overlay is False
        assert request.take_screenshots is False

    def test_action_response_success(self):
        """Test successful ActionResponse."""
        response = ActionResponse(
            success=True,
            action="Click the button",
            observed_elements=3,
            artifacts=[],
            url="https://example.com",
            timestamp="2024-01-01T00:00:00Z",
            processing_time=1.5
        )

        assert response.success is True
        assert response.observed_elements == 3
        assert response.error is None

    def test_action_response_error(self):
        """Test error ActionResponse."""
        response = ActionResponse(
            success=False,
            action="Click the button",
            observed_elements=0,
            artifacts=[],
            url="https://example.com",
            timestamp="2024-01-01T00:00:00Z",
            processing_time=0.5,
            error="Element not found",
            error_code="NO_ELEMENTS_FOUND"
        )

        assert response.success is False
        assert response.error == "Element not found"
        assert response.error_code == "NO_ELEMENTS_FOUND"


class TestScreenshotSchemas:
    """Test Screenshot request/response schemas."""

    def test_screenshot_request_valid(self):
        """Test valid ScreenshotRequest."""
        request = ScreenshotRequest(url="https://example.com")

        assert request.url == "https://example.com"

    def test_screenshot_request_missing_url(self):
        """Test ScreenshotRequest requires URL."""
        with pytest.raises(ValidationError):
            ScreenshotRequest()

    def test_screenshot_response_success(self):
        """Test successful ScreenshotResponse."""
        response = ScreenshotResponse(
            success=True,
            screenshot="base64data",
            url="https://example.com",
            timestamp="2024-01-01T00:00:00Z",
            processing_time=2.0
        )

        assert response.success is True
        assert response.screenshot == "base64data"
        assert response.error is None

    def test_screenshot_response_error(self):
        """Test error ScreenshotResponse."""
        response = ScreenshotResponse(
            success=False,
            screenshot=None,
            url="https://example.com",
            timestamp="2024-01-01T00:00:00Z",
            processing_time=0.5,
            error="Page load failed",
            error_code="SCREENSHOT_ERROR"
        )

        assert response.success is False
        assert response.screenshot is None
        assert response.error == "Page load failed"


class TestClickTypeSchemas:
    """Test ClickType request/response schemas."""

    def test_click_type_request_valid(self):
        """Test valid ClickTypeRequest."""
        request = ClickTypeRequest(
            url="https://example.com",
            x=100,
            y=200,
            text="search query",
            press_enter=True,
            take_screenshot=True
        )

        assert request.x == 100
        assert request.y == 200
        assert request.text == "search query"
        assert request.press_enter is True

    def test_click_type_request_defaults(self):
        """Test ClickTypeRequest with defaults."""
        request = ClickTypeRequest(
            url="https://example.com",
            x=50,
            y=100
        )

        assert request.text is None
        assert request.press_enter is False
        assert request.take_screenshot is False

    def test_click_type_request_negative_coords(self):
        """Test ClickTypeRequest rejects negative coordinates."""
        with pytest.raises(ValidationError):
            ClickTypeRequest(
                url="https://example.com",
                x=-10,
                y=100
            )

    def test_click_type_response_success(self):
        """Test successful ClickTypeResponse."""
        response = ClickTypeResponse(
            success=True,
            action="Clicked at (100, 200) → Typed: 'test'",
            screenshot="base64data",
            url="https://example.com",
            timestamp="2024-01-01T00:00:00Z",
            processing_time=1.5
        )

        assert response.success is True
        assert "Clicked" in response.action
        assert response.screenshot == "base64data"


class TestExtractionSchemas:
    """Test Extraction request/response schemas."""

    def test_extraction_request_valid(self):
        """Test valid ExtractionRequest."""
        request = ExtractionRequest(
            url="https://example.com",
            instruction="Extract product info",
            schema_name="ProductData",
            take_screenshots=True
        )

        assert request.schema_name == "ProductData"
        assert request.take_screenshots is True

    def test_extraction_response_success(self):
        """Test successful ExtractionResponse."""
        response = ExtractionResponse(
            success=True,
            data={"name": "Product A", "price": 99.99},
            schema="ProductData",
            instruction="Extract product info",
            artifacts=[],
            url="https://example.com",
            timestamp="2024-01-01T00:00:00Z",
            processing_time=2.5
        )

        assert response.success is True
        assert response.data["name"] == "Product A"


class TestWorkflowSchemas:
    """Test Workflow request/response schemas."""

    def test_workflow_request_valid(self):
        """Test valid WorkflowRequest."""
        request = WorkflowRequest(
            url="https://example.com",
            workflow_instruction="Navigate and apply",
            max_steps=30,
            auto_screenshot=True,
            wait_between_actions=2000
        )

        assert request.max_steps == 30
        assert request.wait_between_actions == 2000

    def test_workflow_request_defaults(self):
        """Test WorkflowRequest defaults."""
        request = WorkflowRequest(
            url="https://example.com",
            workflow_instruction="Test workflow"
        )

        assert request.max_steps == 20
        assert request.auto_screenshot is True
        assert request.wait_between_actions == 1000

    def test_workflow_response_success(self):
        """Test successful WorkflowResponse."""
        response = WorkflowResponse(
            success=True,
            workflow="Test workflow",
            result={"completed": True},
            url="https://example.com",
            timestamp="2024-01-01T00:00:00Z",
            processing_time=10.5,
            execution_method="agent"
        )

        assert response.success is True
        assert response.execution_method == "agent"


class TestDataSchemas:
    """Test data extraction schemas."""

    def test_product_data_valid(self):
        """Test valid ProductData."""
        product = ProductData(
            name="Test Product",
            price=29.99,
            rating=4.5,
            in_stock=True,
            description="Great product"
        )

        assert product.name == "Test Product"
        assert product.price == 29.99

    def test_job_posting_valid(self):
        """Test valid JobPosting."""
        job = JobPosting(
            title="Software Engineer",
            company="Tech Corp",
            location="Remote",
            salary_range="$100k-$150k",
            description="Great job",
            requirements=["Python", "FastAPI"]
        )

        assert job.title == "Software Engineer"
        assert len(job.requirements) == 2

    def test_company_info_valid(self):
        """Test valid CompanyInfo."""
        company = CompanyInfo(
            name="Tech Corp",
            description="Tech company",
            founded_year=2020,
            employee_count="50-100",
            industry="Technology"
        )

        assert company.name == "Tech Corp"
        assert company.founded_year == 2020


class TestHealthSchema:
    """Test health check schema."""

    def test_health_response_valid(self):
        """Test valid HealthResponse."""
        from datetime import datetime, timezone

        response = HealthResponse(
            status="healthy",
            timestamp=datetime.now(timezone.utc),
            version="1.0.0"
        )

        assert response.status == "healthy"
        assert response.version == "1.0.0"


class TestSchemaRegistry:
    """Test schema registry functions."""

    def test_get_extraction_schema_valid(self):
        """Test retrieving valid extraction schema."""
        schema = get_extraction_schema("ProductData")
        assert schema == ProductData

    def test_get_extraction_schema_invalid(self):
        """Test retrieving invalid schema returns None."""
        schema = get_extraction_schema("InvalidSchema")
        assert schema is None

    def test_get_all_schemas(self):
        """Test all schemas are registered."""
        assert get_extraction_schema("ProductData") is not None
        assert get_extraction_schema("JobPosting") is not None
        assert get_extraction_schema("CompanyInfo") is not None
