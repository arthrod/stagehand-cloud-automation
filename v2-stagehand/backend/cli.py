#!/usr/bin/env python3
"""Stagehand CLI - Command-line interface for browser automation.

A powerful CLI for web automation using AI and direct browser control.

Usage:
    # Simple screenshot
    python cli.py screenshot https://example.com

    # Click and type
    python cli.py click https://google.com --x 500 --y 300 --text "search" --enter

    # AI-powered action
    python cli.py action https://example.com "Click the sign in button"

    # Extract data
    python cli.py extract https://shop.example.com/product "Extract product info" --schema ProductData

    # Execute workflow
    python cli.py workflow https://jobs.example.com "Apply to software engineer positions"
"""

import asyncio
import json
import sys
from typing import Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.json import JSON
from rich.progress import Progress, SpinnerColumn, TextColumn

from services.stagehand_service import StagehandService
from schemas.stagehand_schemas import ProductData, JobPosting, CompanyInfo

app = typer.Typer(
    name="stagehand",
    help="Stagehand AI Automation CLI - Powerful web automation with AI",
    add_completion=False
)
console = Console()
service = StagehandService()


def run_async(coro):
    """Helper to run async functions in CLI."""
    return asyncio.run(coro)


@app.command()
def screenshot(
    url: str = typer.Argument(..., help="URL to screenshot"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save screenshot to file (PNG)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Take a screenshot of a webpage.

    Simple, fast screenshot capture without AI.

    Examples:
        stagehand screenshot https://example.com
        stagehand screenshot https://example.com --output screenshot.png
        stagehand screenshot https://example.com --json
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Capturing screenshot of {url}...", total=None)

        result = run_async(service.take_screenshot(url=url))

        progress.remove_task(task)

    if result.get("success"):
        if json_output:
            # Output JSON without screenshot data (too large)
            output_data = {k: v for k, v in result.items() if k != "screenshot"}
            console.print(JSON(json.dumps(output_data)))
        else:
            console.print(f"[green]✓[/green] Screenshot captured successfully!")
            console.print(f"URL: {result['url']}")
            console.print(f"Processing time: {result['processing_time']:.2f}s")

            if output:
                # Save screenshot to file
                import base64
                screenshot_data = base64.b64decode(result["screenshot"])
                Path(output).write_bytes(screenshot_data)
                console.print(f"[green]✓[/green] Saved to: {output}")
            else:
                console.print(f"[yellow]ℹ[/yellow] Use --output to save the screenshot to a file")
    else:
        console.print(f"[red]✗[/red] Screenshot failed: {result.get('error')}")
        raise typer.Exit(code=1)


@app.command()
def click(
    url: str = typer.Argument(..., help="URL to interact with"),
    x: int = typer.Option(..., "--x", help="X coordinate to click"),
    y: int = typer.Option(..., "--y", help="Y coordinate to click"),
    text: Optional[str] = typer.Option(None, "--text", "-t", help="Text to type after clicking"),
    enter: bool = typer.Option(False, "--enter", help="Press Enter after typing"),
    screenshot: bool = typer.Option(False, "--screenshot", "-s", help="Take screenshot after action"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save screenshot to file"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Click at coordinates and optionally type text.

    Direct browser control without AI - fast and precise.

    Examples:
        stagehand click https://google.com --x 500 --y 300
        stagehand click https://google.com --x 500 --y 300 --text "search query" --enter
        stagehand click https://example.com --x 100 --y 200 --screenshot --output result.png
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Executing click action on {url}...", total=None)

        result = run_async(service.click_type_enter(
            url=url,
            x=x,
            y=y,
            text=text,
            press_enter=enter,
            take_screenshot=screenshot
        ))

        progress.remove_task(task)

    if result.get("success"):
        if json_output:
            output_data = {k: v for k, v in result.items() if k != "screenshot"}
            console.print(JSON(json.dumps(output_data)))
        else:
            console.print("[green]✓[/green] Action completed successfully!")
            console.print(f"Action: {result['action']}")
            console.print(f"Processing time: {result['processing_time']:.2f}s")

            if output and result.get("screenshot"):
                import base64
                screenshot_data = base64.b64decode(result["screenshot"])
                Path(output).write_bytes(screenshot_data)
                console.print(f"[green]✓[/green] Screenshot saved to: {output}")
    else:
        console.print(f"[red]✗[/red] Action failed: {result.get('error')}")
        raise typer.Exit(code=1)


@app.command()
def action(
    url: str = typer.Argument(..., help="URL to interact with"),
    instruction: str = typer.Argument(..., help="Natural language instruction"),
    overlay: bool = typer.Option(False, "--overlay", help="Show visual overlay"),
    screenshot: bool = typer.Option(False, "--screenshot", "-s", help="Take screenshot"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Perform an AI-guided action on a webpage.

    Uses AI to understand the page and execute actions.

    Examples:
        stagehand action https://example.com "Click the sign in button"
        stagehand action https://shop.example.com "Add the first product to cart"
        stagehand action https://form.example.com "Fill in the email field with test@example.com" --screenshot
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Performing AI-guided action...", total=None)

        result = run_async(service.perform_action_with_observe(
            url=url,
            action_instruction=instruction,
            config={
                "draw_overlay": overlay,
                "take_screenshots": screenshot
            }
        ))

        progress.remove_task(task)

    if result.get("success"):
        if json_output:
            output_data = {k: v for k, v in result.items() if k != "artifacts"}
            console.print(JSON(json.dumps(output_data)))
        else:
            console.print(f"[green]✓[/green] Action completed!")
            console.print(f"Instruction: {result['action']}")
            console.print(f"Observed elements: {result['observed_elements']}")
            console.print(f"Processing time: {result['processing_time']:.2f}s")
    else:
        console.print(f"[red]✗[/red] Action failed: {result.get('error')}")
        raise typer.Exit(code=1)


@app.command()
def extract(
    url: str = typer.Argument(..., help="URL to extract data from"),
    instruction: str = typer.Argument(..., help="What data to extract"),
    schema: str = typer.Option("ProductData", "--schema", help="Schema: ProductData, JobPosting, or CompanyInfo"),
    screenshot: bool = typer.Option(False, "--screenshot", "-s", help="Take screenshot"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Extract structured data from a webpage using AI.

    Available schemas:
    - ProductData: name, price, rating, in_stock, description
    - JobPosting: title, company, location, salary_range, description, requirements
    - CompanyInfo: name, description, founded_year, employee_count, industry

    Examples:
        stagehand extract https://shop.example.com/product "Extract product info"
        stagehand extract https://jobs.example.com/posting "Get job details" --schema JobPosting
        stagehand extract https://company.example.com "Extract company info" --schema CompanyInfo --json
    """
    schema_map = {
        "ProductData": ProductData,
        "JobPosting": JobPosting,
        "CompanyInfo": CompanyInfo
    }

    schema_class = schema_map.get(schema)
    if not schema_class:
        console.print(f"[red]✗[/red] Unknown schema: {schema}")
        console.print(f"Available schemas: {', '.join(schema_map.keys())}")
        raise typer.Exit(code=1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Extracting data from {url}...", total=None)

        result = run_async(service.extract_with_schema(
            url=url,
            instruction=instruction,
            schema=schema_class,
            config={"take_screenshots": screenshot}
        ))

        progress.remove_task(task)

    if result.get("success"):
        if json_output:
            console.print(JSON(json.dumps(result)))
        else:
            console.print(f"[green]✓[/green] Data extracted successfully!")
            console.print(f"\n[bold]Extracted Data ({schema}):[/bold]")

            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Field")
            table.add_column("Value")

            for key, value in result["data"].items():
                table.add_row(str(key), str(value))

            console.print(table)
            console.print(f"\nProcessing time: {result['processing_time']:.2f}s")
    else:
        console.print(f"[red]✗[/red] Extraction failed: {result.get('error')}")
        raise typer.Exit(code=1)


@app.command()
def workflow(
    url: str = typer.Argument(..., help="Starting URL for workflow"),
    instruction: str = typer.Argument(..., help="Workflow description"),
    max_steps: int = typer.Option(20, "--max-steps", help="Maximum number of steps"),
    screenshot: bool = typer.Option(True, "--screenshot/--no-screenshot", help="Auto-screenshot"),
    wait: int = typer.Option(1000, "--wait", help="Milliseconds to wait between actions"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Execute a complex multi-step workflow using AI agent.

    The agent can navigate, fill forms, and make decisions.

    Examples:
        stagehand workflow https://jobs.example.com "Apply to software engineer positions"
        stagehand workflow https://shop.example.com "Find and add laptop to cart" --max-steps 30
        stagehand workflow https://form.example.com "Complete the registration form" --json
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Executing workflow...", total=None)

        result = run_async(service.execute_workflow_with_agent(
            url=url,
            workflow_instruction=instruction,
            config={
                "max_steps": max_steps,
                "auto_screenshot": screenshot,
                "wait_between_actions": wait
            }
        ))

        progress.remove_task(task)

    if result.get("success"):
        if json_output:
            console.print(JSON(json.dumps(result)))
        else:
            console.print(f"[green]✓[/green] Workflow completed!")
            console.print(f"\nWorkflow: {result['workflow']}")
            console.print(f"Processing time: {result['processing_time']:.2f}s")
            console.print(f"Execution method: {result.get('execution_method', 'agent')}")

            if result.get("result"):
                console.print(f"\n[bold]Result:[/bold]")
                console.print(Panel(JSON(json.dumps(result["result"]))))
    else:
        console.print(f"[red]✗[/red] Workflow failed: {result.get('error')}")
        raise typer.Exit(code=1)


@app.command()
def info():
    """Show information about Stagehand capabilities."""
    console.print(Panel.fit(
        "[bold cyan]Stagehand AI Automation CLI[/bold cyan]\n\n"
        "Powerful web automation combining AI and direct browser control.\n\n"
        "[bold]Capabilities:[/bold]\n"
        "  • Screenshot capture\n"
        "  • Direct click/type automation\n"
        "  • AI-guided actions\n"
        "  • Structured data extraction\n"
        "  • Complex workflow execution\n\n"
        "[bold]Supported Browsers (Mac):[/bold]\n"
        "  Chrome, Arc, Zen, Firefox, Vivaldi\n\n"
        "[bold]Usage:[/bold]\n"
        "  stagehand --help\n"
        "  stagehand screenshot https://example.com\n"
        "  stagehand action https://example.com \"Click sign in\"\n",
        title="ℹ️  Stagehand Info",
        border_style="cyan"
    ))


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
