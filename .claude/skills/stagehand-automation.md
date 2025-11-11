---
description: Using Stagehand for browser automation via MCP and CLI
tags: [automation, browser, mcp, cli, ai, web-scraping]
---

# Stagehand AI Automation

Powerful browser automation combining AI intelligence with direct browser control. Available through both MCP (Model Context Protocol) and CLI interfaces.

## When to Use This Tool

Use Stagehand when you need to:

- **Capture screenshots** of webpages programmatically
- **Automate web interactions** (clicking, typing, form filling)
- **Extract structured data** from websites (products, jobs, companies)
- **Execute complex workflows** requiring multiple steps and AI decisions
- **Test web applications** with AI-guided scenarios
- **Scrape dynamic content** that requires JavaScript execution

## Available Interfaces

### 1. MCP Server (Recommended for AI Assistants)

The MCP server exposes Stagehand capabilities to AI assistants through the Model Context Protocol.

**When to use MCP:**
- Working with AI assistants that support MCP
- Need programmatic access from other tools
- Want AI to autonomously perform web automation
- Building AI-powered workflows

**Setup:**
```bash
cd v2-stagehand/backend
python mcp_server.py
```

**Available MCP Tools:**
- `take_screenshot` - Capture webpage screenshots
- `click_and_type` - Direct coordinate-based automation
- `perform_action` - AI-guided webpage interactions
- `extract_data` - Extract structured data with schemas
- `execute_workflow` - Complex multi-step automation

### 2. CLI (Recommended for Scripts and Humans)

The typer-based CLI provides a rich command-line interface with progress indicators and formatted output.

**When to use CLI:**
- Running automation from scripts or cron jobs
- Interactive command-line workflows
- Quick one-off automation tasks
- Debugging and testing automation scenarios
- CI/CD pipeline integration

**Commands:**
```bash
# Screenshot
python cli.py screenshot https://example.com --output screenshot.png

# Click and type
python cli.py click https://google.com --x 500 --y 300 --text "search" --enter

# AI-guided action
python cli.py action https://example.com "Click the sign in button"

# Extract data
python cli.py extract https://shop.example.com/product "Extract product info" --schema ProductData

# Execute workflow
python cli.py workflow https://jobs.example.com "Apply to software engineer positions"
```

## Capabilities

### Simple Actions (No AI Required)

These are fast, direct browser operations:

#### Screenshot
Capture PNG screenshots of any webpage.

**MCP:**
```json
{
  "tool": "take_screenshot",
  "input": {
    "url": "https://example.com"
  }
}
```

**CLI:**
```bash
python cli.py screenshot https://example.com --output page.png
```

#### Click and Type
Click at specific coordinates and optionally type text.

**MCP:**
```json
{
  "tool": "click_and_type",
  "input": {
    "url": "https://google.com",
    "x": 500,
    "y": 300,
    "text": "search query",
    "press_enter": true,
    "take_screenshot": false
  }
}
```

**CLI:**
```bash
python cli.py click https://google.com --x 500 --y 300 --text "query" --enter
```

### AI-Powered Actions

These use AI to understand pages and execute actions:

#### Perform Action
AI observes the page and executes natural language instructions.

**MCP:**
```json
{
  "tool": "perform_action",
  "input": {
    "url": "https://example.com",
    "action_instruction": "Click the sign in button",
    "draw_overlay": false,
    "take_screenshots": true
  }
}
```

**CLI:**
```bash
python cli.py action https://example.com "Click the sign in button" --screenshot
```

**Use cases:**
- Clicking dynamically positioned buttons
- Filling forms with intelligent field detection
- Navigating complex UIs
- Interacting with JavaScript-heavy sites

#### Extract Data
Extract structured data using predefined schemas.

**Available Schemas:**
- `ProductData` - E-commerce products (name, price, rating, in_stock, description)
- `JobPosting` - Job listings (title, company, location, salary_range, description, requirements)
- `CompanyInfo` - Company data (name, description, founded_year, employee_count, industry)

**MCP:**
```json
{
  "tool": "extract_data",
  "input": {
    "url": "https://shop.example.com/product",
    "instruction": "Extract the product information",
    "schema_name": "ProductData",
    "take_screenshots": false
  }
}
```

**CLI:**
```bash
python cli.py extract https://shop.example.com/product "Extract product" --schema ProductData --json
```

#### Execute Workflow
Run complex multi-step workflows with AI decision-making.

**MCP:**
```json
{
  "tool": "execute_workflow",
  "input": {
    "url": "https://jobs.example.com",
    "workflow_instruction": "Find and apply to software engineer positions",
    "max_steps": 30,
    "auto_screenshot": true,
    "wait_between_actions": 1000
  }
}
```

**CLI:**
```bash
python cli.py workflow https://jobs.example.com "Apply to engineer jobs" --max-steps 30
```

**Use cases:**
- Multi-page form completion
- E-commerce checkout flows
- Account creation and setup
- Data collection across multiple pages

## Browser Configuration

Stagehand supports multiple browsers on Mac via environment variables:

```bash
# .env configuration
STAGEHAND_ENV=LOCAL  # or BROWSERBASE for cloud
BROWSER_TYPE=chrome  # chrome, arc, zen, firefox, vivaldi

# Attach to existing browser session
USE_EXISTING_SESSION=true
BROWSER_CDP_URL=http://localhost:9222

# Or launch new browser
USE_EXISTING_SESSION=false
HEADLESS=true
```

## Best Practices

### Choosing Between MCP and CLI

**Use MCP when:**
- Building AI-powered automation agents
- Integrating with AI assistants
- Need tool discoverability and schema validation
- Want AI to make autonomous decisions

**Use CLI when:**
- Writing shell scripts
- Running from cron jobs
- Interactive debugging
- CI/CD pipeline integration
- Prefer human-readable output

### Error Handling

Both interfaces return structured error information:

**Success Response:**
```json
{
  "success": true,
  "message": "Action completed",
  "data": {...},
  "processing_time": 1.5
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Element not found",
  "error_code": "NO_ELEMENTS_FOUND"
}
```

**CLI:** Exits with code 1 on errors

### Performance Tips

1. **Use simple actions when possible** - They're faster than AI-powered ones
2. **Adjust wait times** - Reduce for fast sites, increase for slow ones
3. **Limit max_steps** - Prevents runaway workflows
4. **Disable screenshots** - Unless you need them (saves time/bandwidth)
5. **Reuse browser sessions** - Attach to existing session for speed

## Examples

### Example 1: E-commerce Price Monitoring

**MCP:**
```json
{
  "tool": "extract_data",
  "input": {
    "url": "https://shop.example.com/product/123",
    "instruction": "Get current product price and availability",
    "schema_name": "ProductData"
  }
}
```

**CLI:**
```bash
#!/bin/bash
# price_monitor.sh
python cli.py extract \
  "https://shop.example.com/product/123" \
  "Get current price" \
  --schema ProductData \
  --json > product_data.json
```

### Example 2: Automated Testing

**CLI:**
```bash
# test_login.sh
python cli.py action "https://app.example.com" "Click sign in button"
python cli.py click "https://app.example.com/login" --x 300 --y 150 --text "user@example.com"
python cli.py click "https://app.example.com/login" --x 300 --y 200 --text "password" --enter
python cli.py screenshot "https://app.example.com/dashboard" --output dashboard.png
```

### Example 3: Job Application Workflow

**MCP:**
```json
{
  "tool": "execute_workflow",
  "input": {
    "url": "https://jobs.company.com",
    "workflow_instruction": "Search for 'senior software engineer' positions in San Francisco, filter by remote options, and save the first 5 job IDs",
    "max_steps": 50,
    "auto_screenshot": true
  }
}
```

## Troubleshooting

### Common Issues

**"Browser not found"**
- Set `BROWSER_EXECUTABLE_PATH` in `.env`
- Check browser is installed
- Verify browser type matches installation

**"Connection refused"**
- Start browser with `--remote-debugging-port=9222`
- Check `BROWSER_CDP_URL` is correct
- Ensure no firewall blocking port

**"AI model error"**
- Verify `MODEL_API_KEY` is set
- Check `MODEL_NAME` is valid
- Confirm API quota/limits

**"Element not found"**
- Increase wait times
- Try `draw_overlay=true` to debug
- Use screenshot to verify page state
- Check for dynamic content loading

## Running the Tools

### Start MCP Server
```bash
cd v2-stagehand/backend
python mcp_server.py
```

### Run CLI Commands
```bash
cd v2-stagehand/backend
python cli.py --help
python cli.py info  # Show capabilities
```

### Running Tests
```bash
cd v2-stagehand/backend
python -m pytest tests/ -v --cov=. --cov-report=html
```

## Integration Examples

### With Make
```makefile
.PHONY: screenshot
screenshot:
	cd v2-stagehand/backend && \
	python cli.py screenshot $(URL) --output $(OUTPUT)

.PHONY: extract-products
extract-products:
	cd v2-stagehand/backend && \
	python cli.py extract $(URL) "Extract all products" --schema ProductData --json
```

### With Python
```python
import subprocess
import json

# Run CLI command
result = subprocess.run(
    ["python", "cli.py", "extract", url, instruction, "--schema", "ProductData", "--json"],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)
print(f"Extracted: {data['data']}")
```

### With Shell Script
```bash
#!/bin/bash
set -e

echo "Starting automation workflow..."

# Take before screenshot
python cli.py screenshot https://example.com --output before.png

# Perform action
python cli.py action https://example.com "Complete the form with test data"

# Take after screenshot
python cli.py screenshot https://example.com/success --output after.png

echo "Workflow complete!"
```

## Summary

Stagehand provides powerful browser automation through two interfaces:
- **MCP** for AI assistant integration and programmatic access
- **CLI** for scripts, humans, and traditional automation

Choose the interface that best fits your use case, and leverage both simple and AI-powered capabilities to automate web interactions effectively.
