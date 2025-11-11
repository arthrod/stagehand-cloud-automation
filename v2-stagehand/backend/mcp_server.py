"""MCP Server for Stagehand AI Automation.

This MCP server exposes all Stagehand automation capabilities via the Model Context Protocol,
allowing AI assistants to interact with web browsers and perform automation tasks.

Usage:
    # Run the MCP server
    python mcp_server.py

    # Or use with uvx
    uvx mcp install ./mcp_server.py
"""

import asyncio
import base64
import logging
from typing import Optional, List, Dict, Any

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from services.stagehand_service import StagehandService
from schemas.stagehand_schemas import ProductData, JobPosting, CompanyInfo

# Configure logging
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("Stagehand AI Automation")

# Initialize service
service = StagehandService()


# Pydantic models for tool inputs
class ScreenshotInput(BaseModel):
    """Input for taking a screenshot."""
    url: str = Field(..., description="URL of the webpage to screenshot")


class ClickTypeInput(BaseModel):
    """Input for clicking and typing on a webpage."""
    url: str = Field(..., description="URL of the webpage")
    x: int = Field(..., description="X coordinate to click", ge=0)
    y: int = Field(..., description="Y coordinate to click", ge=0)
    text: Optional[str] = Field(None, description="Text to type after clicking")
    press_enter: bool = Field(False, description="Press Enter after typing")
    take_screenshot: bool = Field(False, description="Take screenshot after action")


class ActionInput(BaseModel):
    """Input for performing an AI-guided action."""
    url: str = Field(..., description="URL of the webpage")
    action_instruction: str = Field(..., description="Natural language instruction for the action")
    draw_overlay: bool = Field(False, description="Show visual overlay on observed elements")
    take_screenshots: bool = Field(False, description="Take screenshot after action")


class ExtractionInput(BaseModel):
    """Input for extracting structured data."""
    url: str = Field(..., description="URL of the webpage")
    instruction: str = Field(..., description="What data to extract")
    schema_name: str = Field(..., description="Schema to use: ProductData, JobPosting, or CompanyInfo")
    take_screenshots: bool = Field(False, description="Take screenshot after extraction")


class WorkflowInput(BaseModel):
    """Input for executing a multi-step workflow."""
    url: str = Field(..., description="Starting URL for the workflow")
    workflow_instruction: str = Field(..., description="Natural language description of the workflow")
    max_steps: int = Field(20, description="Maximum number of steps", ge=1, le=100)
    auto_screenshot: bool = Field(True, description="Auto-screenshot at each step")
    wait_between_actions: int = Field(1000, description="Milliseconds to wait between actions")


# MCP Tools (exposed to AI assistants)

@mcp.tool()
async def take_screenshot(input: ScreenshotInput) -> Dict[str, Any]:
    """Take a screenshot of a webpage.

    This is a simple, fast operation that doesn't require AI.
    Returns a base64-encoded PNG image of the webpage.

    Args:
        input: Screenshot parameters

    Returns:
        dict: Success status, screenshot data, and metadata
    """
    try:
        result = await service.take_screenshot(url=input.url)

        if result.get("success"):
            return {
                "success": True,
                "message": f"Screenshot captured from {input.url}",
                "screenshot_base64": result["screenshot"],
                "url": result["url"],
                "processing_time": result["processing_time"]
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Screenshot failed"),
                "error_code": result.get("error_code")
            }
    except Exception as e:
        logger.error(f"Unhandled exception in take_screenshot: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_code": "INTERNAL_ERROR"
        }


@mcp.tool()
async def click_and_type(input: ClickTypeInput) -> Dict[str, Any]:
    """Click at specific coordinates and optionally type text.

    This tool performs direct browser automation without AI:
    - Click at (x, y) coordinates
    - Optionally type text
    - Optionally press Enter
    - Optionally capture screenshot

    Args:
        input: Click and type parameters

    Returns:
        dict: Success status and action details
    """
    try:
        result = await service.click_type_enter(
            url=input.url,
            x=input.x,
            y=input.y,
            text=input.text,
            press_enter=input.press_enter,
            take_screenshot=input.take_screenshot
        )

        if result.get("success"):
            response = {
                "success": True,
                "message": result["action"],
                "url": result["url"],
                "processing_time": result["processing_time"]
            }
            if result.get("screenshot"):
                response["screenshot_base64"] = result["screenshot"]
            return response
        else:
            return {
                "success": False,
                "error": result.get("error", "Click/type action failed"),
                "error_code": result.get("error_code")
            }
    except Exception as e:
        logger.error(f"Unhandled exception in click_and_type: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_code": "INTERNAL_ERROR"
        }


@mcp.tool()
async def perform_action(input: ActionInput) -> Dict[str, Any]:
    """Perform an AI-guided action on a webpage.

    Uses AI to observe the page and execute actions like:
    - Clicking buttons or links
    - Filling forms
    - Navigating menus
    - Interacting with dynamic elements

    Args:
        input: Action parameters

    Returns:
        dict: Success status, observed elements, and optional screenshots
    """
    try:
        result = await service.perform_action_with_observe(
            url=input.url,
            action_instruction=input.action_instruction,
            config={
                "draw_overlay": input.draw_overlay,
                "take_screenshots": input.take_screenshots
            }
        )

        if result.get("success"):
            response = {
                "success": True,
                "message": f"Action completed: {result['action']}",
                "observed_elements": result["observed_elements"],
                "url": result["url"],
                "processing_time": result["processing_time"]
            }
            if result.get("artifacts"):
                response["artifacts"] = result["artifacts"]
            return response
        else:
            return {
                "success": False,
                "error": result.get("error", "Action failed"),
                "error_code": result.get("error_code")
            }
    except Exception as e:
        logger.error(f"Unhandled exception in perform_action: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_code": "INTERNAL_ERROR"
        }


@mcp.tool()
async def extract_data(input: ExtractionInput) -> Dict[str, Any]:
    """Extract structured data from a webpage using AI.

    Supports schemas:
    - ProductData: name, price, rating, in_stock, description
    - JobPosting: title, company, location, salary_range, description, requirements
    - CompanyInfo: name, description, founded_year, employee_count, industry

    Args:
        input: Extraction parameters

    Returns:
        dict: Extracted structured data
    """
    try:
        # Map schema name to class
        schema_map = {
            "ProductData": ProductData,
            "JobPosting": JobPosting,
            "CompanyInfo": CompanyInfo
        }

        schema = schema_map.get(input.schema_name)
        if not schema:
            return {
                "success": False,
                "error": f"Unknown schema: {input.schema_name}. Available: {list(schema_map.keys())}",
                "error_code": "INVALID_SCHEMA"
            }

        result = await service.extract_with_schema(
            url=input.url,
            instruction=input.instruction,
            schema=schema,
            config={"take_screenshots": input.take_screenshots}
        )

        if result.get("success"):
            response = {
                "success": True,
                "message": f"Data extracted using {input.schema_name}",
                "data": result["data"],
                "url": result["url"],
                "processing_time": result["processing_time"]
            }
            if result.get("artifacts"):
                response["artifacts"] = result["artifacts"]
            return response
        else:
            return {
                "success": False,
                "error": result.get("error", "Extraction failed"),
                "error_code": result.get("error_code")
            }
    except Exception as e:
        logger.error(f"Unhandled exception in extract_data: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_code": "INTERNAL_ERROR"
        }


@mcp.tool()
async def execute_workflow(input: WorkflowInput) -> Dict[str, Any]:
    """Execute a complex multi-step workflow using an AI agent.

    The agent can:
    - Navigate through multiple pages
    - Fill out complex forms
    - Handle dynamic content
    - Make decisions based on page content
    - Execute up to max_steps actions

    Args:
        input: Workflow parameters

    Returns:
        dict: Workflow execution results
    """
    try:
        result = await service.execute_workflow_with_agent(
            url=input.url,
            workflow_instruction=input.workflow_instruction,
            config={
                "max_steps": input.max_steps,
                "auto_screenshot": input.auto_screenshot,
                "wait_between_actions": input.wait_between_actions
            }
        )

        if result.get("success"):
            return {
                "success": True,
                "message": f"Workflow completed: {result['workflow']}",
                "result": result["result"],
                "url": result["url"],
                "processing_time": result["processing_time"],
                "execution_method": result.get("execution_method", "agent")
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Workflow execution failed"),
                "error_code": result.get("error_code")
            }
    except Exception as e:
        logger.error(f"Unhandled exception in execute_workflow: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_code": "INTERNAL_ERROR"
        }


# MCP Resources (for documentation and examples)

@mcp.resource("stagehand://capabilities")
async def get_capabilities() -> str:
    """Get information about Stagehand capabilities."""
    return """
# Stagehand AI Automation Capabilities

## Simple Actions (No AI Required)
- **take_screenshot**: Capture webpage screenshots
- **click_and_type**: Click coordinates and type text

## AI-Powered Actions
- **perform_action**: AI-guided webpage interactions
- **extract_data**: Extract structured data with schemas
- **execute_workflow**: Complex multi-step automation

## Available Extraction Schemas
- ProductData: E-commerce product information
- JobPosting: Job listings and details
- CompanyInfo: Company information and metadata

## Browser Support (Mac)
- Chrome
- Arc
- Zen
- Firefox
- Vivaldi

Can attach to existing browser sessions or launch new ones.
"""


@mcp.resource("stagehand://examples")
async def get_examples() -> str:
    """Get usage examples."""
    return """
# Stagehand MCP Examples

## Take Screenshot
{
  "url": "https://example.com"
}

## Click and Type
{
  "url": "https://google.com",
  "x": 500,
  "y": 300,
  "text": "search query",
  "press_enter": true
}

## Perform Action
{
  "url": "https://example.com",
  "action_instruction": "Click the sign in button",
  "take_screenshots": true
}

## Extract Data
{
  "url": "https://shop.example.com/product",
  "instruction": "Extract the product information",
  "schema_name": "ProductData"
}

## Execute Workflow
{
  "url": "https://jobs.example.com",
  "workflow_instruction": "Find and apply to software engineer positions",
  "max_steps": 30
}
"""


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
