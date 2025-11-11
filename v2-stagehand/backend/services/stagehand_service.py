import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from config import settings


logger = logging.getLogger(__name__)


class StagehandService:
    def __init__(self):
        pass

    def _get_browser_executable_path(self, browser_type: str) -> Optional[str]:
        """
        Get the executable path for the specified browser on Mac.
        Returns None if browser is not found or on non-Mac systems.
        """
        if settings.BROWSER_EXECUTABLE_PATH:
            return settings.BROWSER_EXECUTABLE_PATH

        # Default Mac paths for different browsers
        browser_paths = {
            "chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "arc": "/Applications/Arc.app/Contents/MacOS/Arc",
            "zen": "/Applications/Zen Browser.app/Contents/MacOS/zen",
            "firefox": "/Applications/Firefox.app/Contents/MacOS/firefox",
            "vivaldi": "/Applications/Vivaldi.app/Contents/MacOS/Vivaldi"
        }

        import os
        path = browser_paths.get(browser_type.lower())
        if path and os.path.exists(path):
            return path

        logger.warning(f"Browser executable not found for {browser_type} at {path}")
        return None

    async def _create_local_browser_session(self, config: Dict[str, Any] = None):  # pragma: no cover
        """
        Create a local browser session using Playwright.
        Supports Chrome, Arc, Zen, Firefox, and Vivaldi on Mac.
        Can attach to existing session if USE_EXISTING_SESSION is enabled.
        """
        try:  # pragma: no cover
            from stagehand import Stagehand, StagehandConfig  # pragma: no cover

            logger.info("Creating local browser session")

            # Build config parameters
            config_params: Dict[str, Any] = {
                "env": "LOCAL",
                "verbose": settings.VERBOSE,
                "dom_settle_timeout_ms": settings.DOM_SETTLE_TIMEOUT_MS,
                "self_heal": settings.SELF_HEAL,
                "headless": settings.HEADLESS if not settings.USE_EXISTING_SESSION else False,
            }

            # Add AI model configuration if available
            if settings.MODEL_NAME:
                config_params["model_name"] = settings.MODEL_NAME
            if settings.MODEL_API_KEY:
                config_params["model_api_key"] = settings.MODEL_API_KEY
            if settings.MODEL_BASE_URL and "openrouter" in settings.MODEL_BASE_URL.lower():
                try:
                    config_params["model_client_options"] = {
                        "api_base": settings.MODEL_BASE_URL
                    }
                except Exception as e:
                    logger.warning(f"Could not set model_client_options: {e}")

            # Configure browser type and executable path
            browser_type = settings.BROWSER_TYPE.lower()
            executable_path = self._get_browser_executable_path(browser_type)

            if executable_path:
                config_params["browser_executable_path"] = executable_path
                logger.info(f"Using {browser_type} browser at: {executable_path}")
            else:
                logger.info(f"Using default browser (no executable path specified)")

            # Handle existing session attachment
            if settings.USE_EXISTING_SESSION:
                if settings.BROWSER_CDP_URL:
                    config_params["cdp_url"] = settings.BROWSER_CDP_URL
                    logger.info(f"Attaching to existing browser session at: {settings.BROWSER_CDP_URL}")
                else:
                    logger.warning("USE_EXISTING_SESSION is true but BROWSER_CDP_URL is not set. Using default CDP URL.")
                    config_params["cdp_url"] = "http://localhost:9222"

            logger.info(f"Initializing Stagehand with local browser: {browser_type}")

            # Create and initialize session
            stagehand_config = StagehandConfig(**config_params)
            stagehand = Stagehand(stagehand_config)
            await stagehand.init()

            logger.info("✓ Local browser session created successfully")
            return stagehand

        except Exception as e:
            logger.error(f"Failed to create local browser session: {e}")
            raise

    async def _create_browserbase_session(self, config: Dict[str, Any] = None):  # pragma: no cover
        try:  # pragma: no cover
            import os  # pragma: no cover
            from stagehand import Stagehand, StagehandConfig  # pragma: no cover

            logger.info("Creating new Browserbase session")

            using_openrouter = (
                settings.MODEL_BASE_URL and "openrouter" in settings.MODEL_BASE_URL.lower()
            )

            # Build config parameters
            config_params: Dict[str, Any] = {
                "env": "BROWSERBASE",
                "verbose": settings.VERBOSE,
                "dom_settle_timeout_ms": settings.DOM_SETTLE_TIMEOUT_MS,
                "self_heal": settings.SELF_HEAL,
                "api_key": settings.BROWSERBASE_API_KEY,
                "project_id": settings.BROWSERBASE_PROJECT_ID,
                "system_prompt": "You are a browser automation assistant that helps users navigate websites effectively.",

            }

            if settings.MODEL_NAME:
                config_params["model_name"] = settings.MODEL_NAME
            if settings.MODEL_API_KEY:
                config_params["model_api_key"] = settings.MODEL_API_KEY

            # OpenRouter configuration
            if using_openrouter and settings.MODEL_BASE_URL:
                try:
                    config_params["model_client_options"] = {
                        "api_base": settings.MODEL_BASE_URL
                    }
                    logger.info(f"Using OpenRouter base URL: {settings.MODEL_BASE_URL}")
                except Exception as e:
                    logger.warning(f"Could not set model_client_options: {e}")

            logger.info(f"Initializing Stagehand with model: {config_params.get('model_name')}")
            logger.info(f"Browserbase mode: env=BROWSERBASE")

            # Create and initialize session
            stagehand_config = StagehandConfig(**config_params)
            stagehand = Stagehand(stagehand_config)
            await stagehand.init()

            logger.info("✓ Browserbase session created successfully")
            return stagehand

        except ValueError as ve:
            logger.error(f"Configuration error: {ve}")
            raise

        except Exception as e:
            logger.error(f"Failed to create Browserbase session: {e}")
            raise

    async def _create_session(self, config: Dict[str, Any] = None):
        """
        Create a Stagehand session based on STAGEHAND_ENV setting.
        Routes to either Browserbase or local browser session.
        """
        if settings.STAGEHAND_ENV == "LOCAL":
            return await self._create_local_browser_session(config)
        else:
            return await self._create_browserbase_session(config)

    async def _close_session(self, stagehand):
        """
        Close a Stagehand session (works for both Browserbase and local).
        """
        if not stagehand:
            return

        try:
            if hasattr(stagehand, 'close'):
                await stagehand.close()
                logger.info("✓ Session closed successfully")
            else:
                logger.warning("Stagehand instance has no close method")
        except Exception as e:
            logger.error(f"Error closing session: {e}")
            # Don't raise - we want to continue even if close fails

    async def _close_browserbase_session(self, stagehand):
        """Legacy method - now calls _close_session"""
        await self._close_session(stagehand)

    async def test_connection(self) -> bool:
        try:
            if settings.STAGEHAND_ENV == "LOCAL":
                # For local mode, verify browser executable exists
                browser_type = settings.BROWSER_TYPE.lower()
                executable_path = self._get_browser_executable_path(browser_type)

                if settings.USE_EXISTING_SESSION:
                    # Just verify CDP URL is set
                    if not settings.BROWSER_CDP_URL:
                        logger.warning("USE_EXISTING_SESSION is true but BROWSER_CDP_URL not configured")
                        return False
                    logger.info(f"✓ Local browser configuration verified (will attach to existing session at {settings.BROWSER_CDP_URL})")
                    return True
                elif executable_path:
                    logger.info(f"✓ Local browser configuration verified (will use {browser_type} at {executable_path})")
                    return True
                else:
                    logger.warning(f"Browser executable not found for {browser_type}")
                    # Still return True as it might work with system default
                    return True
            else:
                # Verify Browserbase configuration
                if not settings.BROWSERBASE_API_KEY:
                    logger.warning("BROWSERBASE_API_KEY not configured")
                    return False
                if not settings.BROWSERBASE_PROJECT_ID:
                    logger.warning("BROWSERBASE_PROJECT_ID not configured")
                    return False
                if not settings.MODEL_API_KEY:
                    logger.warning("MODEL_API_KEY not configured")
                    return False

                logger.info("✓ Browserbase configuration verified (will connect on first job)")
                return True

        except Exception as e:
            logger.error(f"Configuration test failed: {e}")
            return False

    async def perform_action_with_observe(
        self,
        url: str,
        action_instruction: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        start_time = time.time()
        stagehand = None

        try:
            # Create session
            stagehand = await self._create_session(config)
            page = stagehand.page

            # Navigate to URL
            await page.goto(url)

            # Use observe to plan the action
            draw_overlay = config.get("draw_overlay", False)
            results = await page.observe(
                instruction=action_instruction,
                draw_overlay=draw_overlay
            )

            # Execute the action using the first observed result
            if results:
                logger.info(f"Observed {len(results)} elements, executing action: {action_instruction}")
                await page.act(results[0])

                # Take screenshot if requested
                artifacts = []
                if config.get("take_screenshots", False):
                    import base64
                    screenshot_bytes = await page.screenshot()
                    screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                    artifacts.append({
                        "type": "screenshot",
                        "data": screenshot_b64,
                        "format": "png"
                    })

                return {
                    "success": True,
                    "action": action_instruction,
                    "observed_elements": len(results),
                    "artifacts": artifacts,
                    "url": url,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "processing_time": time.time() - start_time
                }
            else:
                return {
                    "success": False,
                    "error": "No elements observed for the given instruction",
                    "error_code": "NO_ELEMENTS_FOUND",
                    "action": action_instruction,
                    "observed_elements": 0,  # No elements found
                    "artifacts": [],
                    "url": url,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "processing_time": time.time() - start_time
                }

        except Exception as e:
            logger.error(f"Error performing action: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "ACTION_EXECUTION_ERROR",
                "action": action_instruction,
                "observed_elements": 0,  # Error occurred before observing
                "artifacts": [],
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "processing_time": time.time() - start_time
            }

        finally:
            # Always close session
            if stagehand:
                await self._close_session(stagehand)

    async def extract_with_schema(
        self,
        url: str,
        instruction: str,
        schema: Any,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        start_time = time.time()
        stagehand = None

        try:
            # Schema extraction works in both Browserbase and local modes
            # Create session
            stagehand = await self._create_session(config)
            page = stagehand.page

            # Navigate to URL
            await page.goto(url)

            # Extract data using schema
            data = await page.extract(
                instruction=instruction,
                schema=schema
            )

            # Take screenshot if requested
            artifacts = []
            if config.get("take_screenshots", False):
                import base64
                screenshot_bytes = await page.screenshot()
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                artifacts.append({
                    "type": "screenshot",
                    "data": screenshot_b64,
                    "format": "png"
                })

            return {
                "success": True,
                "data": data.model_dump() if hasattr(data, 'model_dump') else data,
                "schema": schema.__name__ if hasattr(schema, '__name__') else str(schema),
                "instruction": instruction,
                "artifacts": artifacts,
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "processing_time": time.time() - start_time
            }

        except Exception as e:
            logger.error(f"Error extracting with schema: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "EXTRACTION_ERROR",
                "data": {},  # Empty dict for failed extraction
                "schema": schema.__name__ if hasattr(schema, '__name__') else str(schema),
                "instruction": instruction,
                "artifacts": [],
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "processing_time": time.time() - start_time
            }

        finally:
            # Always close session
            if stagehand:
                await self._close_session(stagehand)

    async def execute_workflow_with_agent(
        self,
        url: str,
        workflow_instruction: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        start_time = time.time()
        stagehand = None

        try:
            # Create session
            stagehand = await self._create_session(config)
            page = stagehand.page

            # Navigate to URL
            await page.goto(url)

            # Create agent
            agent_model = config.get("agent_model", "computer-use-preview")
            agent_instructions = config.get("agent_instructions", "You are a helpful web navigation assistant.")

            # Get API key based on model
            api_key = None
            if "claude" in agent_model.lower():
                api_key = config.get("anthropic_api_key") or settings.MODEL_API_KEY
            elif "gpt" in agent_model.lower() or "computer-use" in agent_model.lower():
                api_key = config.get("openai_api_key") or settings.MODEL_API_KEY

            agent_options = {}
            if api_key:
                agent_options["apiKey"] = api_key

            agent = stagehand.agent(
                model=agent_model,
                instructions=agent_instructions,
                options=agent_options
            )

            # Execute workflow
            max_steps = config.get("max_steps", 20)
            auto_screenshot = config.get("auto_screenshot", True)
            wait_between_actions = config.get("wait_between_actions", 1000)

            result = await agent.execute(
                instruction=workflow_instruction,
                max_steps=max_steps,
                auto_screenshot=auto_screenshot,
                wait_between_actions=wait_between_actions
            )

            return {
                "success": True,
                "workflow": workflow_instruction,
                "result": result,
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "processing_time": time.time() - start_time,
                "execution_method": "agent"
            }

        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "WORKFLOW_EXECUTION_ERROR",
                "workflow": workflow_instruction,
                "result": None,  # No result when error occurs
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "processing_time": time.time() - start_time,
                "execution_method": "agent"
            }

        finally:
            # Always close session
            if stagehand:
                await self._close_session(stagehand)

    async def cleanup(self):
        try:
            # No Stagehand session to clean - sessions are per-job
            logger.info("StagehandService cleanup completed (session-per-job mode)")


        except Exception as e:
            logger.error(f"Error during StagehandService cleanup: {e}")

    async def process_multi_step_instructions(
        self,
        url: str,
        instructions: list,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        start_time = time.time()
        stagehand = None

        try:
            logger.info("Creating session for multi-step workflow")
            stagehand = await self._create_session(config)
            page = stagehand.page
            steps_results = []

            await page.goto(url)
            logger.info(f"Navigated to {url}")

            await asyncio.sleep(2)
            logger.info("Page load wait completed")

            # Process each instruction sequentially
            for idx, instruction in enumerate(instructions, 1):
                step_start = time.time()
                step_type = instruction.get("instruction_type", "act")
                instruction_text = instruction.get("instruction_text", "")
                wait_after = instruction.get("wait_after", 1000)

                logger.info(f"Processing step {idx}: {step_type} - {instruction_text}")

                step_result = {
                    "step_number": idx,
                    "instruction_type": step_type,
                    "instruction_text": instruction_text,
                    "success": False,
                    "data": None,
                    "screenshot": None,
                    "error": None,
                    "error_code": None,
                    "execution_time": 0,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                try:
                    if step_type == "goto":
                        await page.goto(instruction_text)
                        step_result["success"] = True

                    elif step_type == "observe":
                        try:
                            logger.info(f"Calling page.observe with instruction: '{instruction_text}'")
                            results = await page.observe(
                                instruction=instruction_text,
                                draw_overlay=config.get("draw_overlay", False)
                            )
                            step_result["success"] = True
                            step_result["data"] = {
                                "observed_elements": len(results),
                                "elements_found": len(results) > 0
                            }
                            logger.info(f"Observe found {len(results)} elements")
                        except Exception as observe_error:
                            logger.error(f"Observe error: {observe_error}")
                            step_result["success"] = False
                            error_msg = str(observe_error)

                            if "Server returned error" in error_msg:
                                step_result["error"] = (
                                    f"Stagehand AI model error: {error_msg}. "
                                    "Possible causes:\n"
                                    "1. Missing or invalid MODEL_API_KEY in .env\n"
                                    "2. MODEL_NAME not supported or incorrectly configured\n"
                                    "3. Page content too complex for the instruction\n"
                                    "4. Network issues with AI provider\n"
                                    f"Current config: MODEL_NAME={settings.MODEL_NAME}, "
                                    f"API_KEY={'set' if settings.MODEL_API_KEY else 'NOT SET'}"
                                )
                                step_result["error_code"] = "AI_MODEL_ERROR"
                            else:
                                step_result["error"] = f"Observe failed: {error_msg}"
                                step_result["error_code"] = "OBSERVE_ERROR"

                    elif step_type == "act":
                        results = await page.observe(instruction=instruction_text)
                        if results:
                            await page.act(results[0])
                            step_result["success"] = True
                            step_result["data"] = {"action_performed": True}
                        else:
                            step_result["error"] = "No elements found to act upon"
                            step_result["error_code"] = "NO_ELEMENTS_FOUND"

                    elif step_type == "extract":
                        try:
                            logger.info(f"Calling page.extract with instruction: '{instruction_text}'")
                            extracted_data = await page.extract(instruction_text)

                            if extracted_data is None:
                                step_result["success"] = False
                                step_result["error"] = "Extraction returned no data"
                                step_result["error_code"] = "NO_DATA_EXTRACTED"
                            elif isinstance(extracted_data, dict):
                                step_result["success"] = True
                                step_result["data"] = extracted_data
                            elif isinstance(extracted_data, str):
                                step_result["success"] = True
                                step_result["data"] = {"extracted_text": extracted_data}
                            elif hasattr(extracted_data, 'model_dump'):
                                step_result["success"] = True
                                step_result["data"] = extracted_data.model_dump()
                            else:
                                step_result["success"] = True
                                step_result["data"] = {"content": str(extracted_data)}

                        except Exception as extract_error:
                            import traceback
                            error_tb = traceback.format_exc()
                            logger.error(f"Extract error: {extract_error}")
                            logger.error(f"Extract traceback:\n{error_tb}")

                            error_msg = str(extract_error)
                            if "Server returned error" in error_msg:
                                step_result["error"] = f"Stagehand server error: {error_msg}."
                                step_result["error_code"] = "AI_MODEL_ERROR"
                            else:
                                step_result["error"] = f"Extraction failed: {str(extract_error)}"
                                step_result["error_code"] = "EXTRACTION_ERROR"

                            step_result["success"] = False
                            step_result["data"] = None

                    elif step_type == "wait":
                        wait_ms = int(instruction_text) if instruction_text.isdigit() else wait_after
                        await asyncio.sleep(wait_ms / 1000)
                        step_result["success"] = True
                        step_result["data"] = {"waited_ms": wait_ms}

                    elif step_type == "screenshot":
                        import base64
                        screenshot_bytes = await page.screenshot()
                        screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                        step_result["success"] = True
                        step_result["screenshot"] = screenshot_b64
                        step_result["data"] = {"screenshot_taken": True}

                    # Take screenshot if configured
                    if config.get("take_screenshots", False) and step_type != "screenshot":
                        try:
                            import base64
                            screenshot_bytes = await page.screenshot()
                            step_result["screenshot"] = base64.b64encode(screenshot_bytes).decode('utf-8')
                        except Exception as e:
                            logger.warning(f"Screenshot failed for step {idx}: {e}")

                    # Wait after step
                    if wait_after > 0:
                        await asyncio.sleep(wait_after / 1000)

                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    logger.error(f"Error in step {idx}: {e}")
                    logger.error(f"Traceback: {error_details}")
                    step_result["error"] = str(e)
                    step_result["error_code"] = "STEP_EXECUTION_ERROR"
                    step_result["success"] = False

                    if config.get("stop_on_error", False):
                        steps_results.append(step_result)
                        break

                finally:
                    step_result["execution_time"] = time.time() - step_start
                    steps_results.append(step_result)

            # Calculate overall success
            all_success = all(step["success"] for step in steps_results)

            # Generate job ID for tracking
            import uuid
            job_id = f"job_{uuid.uuid4().hex[:12]}"

            end_time = datetime.now(timezone.utc)

            return {
                "job_id": job_id,
                "url": url,
                "success": all_success,
                "total_steps": len(instructions),
                "completed_steps": len(steps_results),
                "steps": steps_results,
                "total_execution_time": time.time() - start_time,
                "started_at": datetime.fromtimestamp(start_time, tz=timezone.utc).isoformat(),
                "completed_at": end_time.isoformat()
            }

        except Exception as e:
            logger.error(f"Error in multi-step processing: {e}")
            import uuid
            job_id = f"job_{uuid.uuid4().hex[:12]}"
            end_time = datetime.now(timezone.utc)

            return {
                "job_id": job_id,
                "url": url,
                "success": False,
                "error": str(e),
                "error_code": "MULTISTEP_PROCESSING_ERROR",
                "total_steps": len(instructions),
                "completed_steps": 0,
                "steps": [],
                "total_execution_time": time.time() - start_time,
                "started_at": datetime.fromtimestamp(start_time, tz=timezone.utc).isoformat(),
                "completed_at": end_time.isoformat()
            }

        finally:
            # Always close session
            if stagehand:
                logger.info("Closing session after workflow")
                await self._close_session(stagehand)

    async def take_screenshot(
        self,
        url: str
    ) -> Dict[str, Any]:
        """
        Take a screenshot of a webpage without using AI.
        Simple, direct action.
        """
        start_time = time.time()
        stagehand = None

        try:
            logger.info(f"Taking screenshot of {url}")
            stagehand = await self._create_session({})
            page = stagehand.page

            # Navigate to URL
            await page.goto(url)

            # Wait for network to be idle to ensure page is fully loaded
            await page.wait_for_load_state('networkidle')

            # Take screenshot
            import base64
            screenshot_bytes = await page.screenshot()
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            return {
                "success": True,
                "screenshot": screenshot_b64,
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "processing_time": time.time() - start_time
            }

        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return {
                "success": False,
                "screenshot": None,
                "error": str(e),
                "error_code": "SCREENSHOT_ERROR",
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "processing_time": time.time() - start_time
            }

        finally:
            if stagehand:
                await self._close_session(stagehand)

    async def click_type_enter(
        self,
        url: str,
        x: int,
        y: int,
        text: Optional[str] = None,
        press_enter: bool = False,
        take_screenshot: bool = False
    ) -> Dict[str, Any]:
        """
        Click at coordinates, optionally type text and press enter.
        No AI required - direct browser automation.
        """
        start_time = time.time()
        stagehand = None

        try:
            logger.info(f"Click at ({x}, {y}) on {url}")
            stagehand = await self._create_session({})
            page = stagehand.page

            # Navigate to URL
            await page.goto(url)

            # Wait a bit for page to settle
            await asyncio.sleep(2)

            # Ensure target coordinates are within current viewport by scrolling if necessary
            viewport = await page.viewport_size()
            if viewport:
              vw, vh = viewport.get("width", 0), viewport.get("height", 0)
              # If coordinates exceed viewport, try to scroll to bring them into view
              if x > vw or y > vh:
                  await page.evaluate(
                      """([x, y]) => { window.scrollTo(Math.max(0, x - 50), Math.max(0, y - 50)); }""",
                      [x, y]
                  )
                  await asyncio.sleep(0.3)

            # Click at coordinates
            await page.mouse.click(x, y)
            logger.info(f"Clicked at ({x}, {y})")

            # Build action description
            actions = [f"Clicked at ({x}, {y})"]

            # Type text if provided
            if text:
                # Focus the element at the clicked coordinates before typing
                await page.evaluate(
                    """([x, y]) => {
                        const el = document.elementFromPoint(x, y);
                        if (el) el.focus();
                    }""",
                    [x, y]
                )
                logger.info(f"Focused element at ({x}, {y}) before typing")
                actions.append(f"Focused element at ({x}, {y})")
                await page.keyboard.type(text)
                logger.info(f"Typed text: {text}")
                actions.append(f"Typed: '{text}'")

            # Press Enter if requested
            if press_enter:
                await page.keyboard.press("Enter")
                logger.info("Pressed Enter")
                actions.append("Pressed Enter")

            # Wait a bit after action
            await asyncio.sleep(1)

            # Take screenshot if requested
            screenshot_b64 = None
            if take_screenshot:
                import base64
                screenshot_bytes = await page.screenshot()
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            action_description = " → ".join(actions)

            return {
                "success": True,
                "action": action_description,
                "screenshot": screenshot_b64,
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "processing_time": time.time() - start_time
            }

        except Exception as e:
            logger.error(f"Error in click/type/enter action: {e}")
            return {
                "success": False,
                "action": f"Failed to perform action at ({x}, {y})",
                "screenshot": None,
                "error": str(e),
                "error_code": "CLICK_TYPE_ERROR",
                "url": url,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "processing_time": time.time() - start_time
            }

        finally:
            if stagehand:
                await self._close_session(stagehand)

