
from typing import Dict, Any, Optional
from playwright.async_api import Page
import asyncio
import logging
from .browser_manager import browser_manager
from .accessibility_tree import AccessibilityTreeExtractor

class PageController:


    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._tree_extractor = AccessibilityTreeExtractor()
        self._current_page: Optional[Page] = None

    async def navigate_and_extract(
        self,
        url: str,
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:

        options = options or {}
        page = None

        try:

            page = await browser_manager.get_page()
            self._current_page = page


            await self._configure_page(page, options)


            await self._navigate(page, url, options)


            await self._wait_for_content(page, options)


            screenshot = await self._take_screenshot(page)


            accessibility_data = await self._tree_extractor.extract(page)


            accessibility_data["screenshot"] = screenshot


            metrics = await self._get_page_metrics(page)
            accessibility_data["metrics"] = metrics

            return accessibility_data

        except Exception as e:
            self._logger.error(f"Page navigation and extraction failed: {e}")
            return {
                "error": str(e),
                "url": url,
                "timestamp": self._tree_extractor._get_timestamp()
            }
        finally:
            if page:
                await browser_manager.release_page(page)
                self._current_page = None

    async def _configure_page(self, page: Page, options: Dict[str, Any]):


        viewport = options.get("viewport", {"width": 1280, "height": 720})
        await page.set_viewport_size(viewport)


        if "headers" in options:
            await page.set_extra_http_headers(options["headers"])


        if "cookies" in options:
            await page.context.add_cookies(options["cookies"])


        page.on("console", lambda msg: self._logger.debug(f"PAGE LOG: {msg.text}"))


        page.on("dialog", lambda dialog: dialog.dismiss())

    async def _navigate(self, page: Page, url: str, options: Dict[str, Any]):

        timeout = options.get("timeout", 30000)
        wait_until = options.get("wait_until", "networkidle")

        try:
            response = await page.goto(
                url,
                wait_until=wait_until,
                timeout=timeout
            )

            if response and not response.ok:
                self._logger.warning(f"Page returned {response.status}: {response.status_text}")

        except Exception as e:
            self._logger.error(f"Navigation failed: {e}")
            raise

    async def _wait_for_content(self, page: Page, options: Dict[str, Any]):

        wait_for = options.get("wait_for", [])

        for selector in wait_for:
            try:
                await page.wait_for_selector(selector, timeout=5000)
            except Exception as e:
                self._logger.warning(f"Timeout waiting for {selector}: {e}")


        if options.get("wait_for_network_idle", True):
            await page.wait_for_load_state("networkidle")


        await asyncio.sleep(1)

    async def _take_screenshot(self, page: Page) -> Optional[str]:

        try:
            screenshot = await page.screenshot(
                full_page=True,
                type="jpeg",
                quality=80
            )
            import base64
            return base64.b64encode(screenshot).decode('utf-8')
        except Exception as e:
            self._logger.warning(f"Screenshot failed: {e}")
            return None

    async def _get_page_metrics(self, page: Page) -> Dict[str, Any]:

        try:
            metrics = await page.metrics()


            perf = await page.evaluate("() => window.performance.getEntriesByType('navigation')[0]?.toJSON() || {}")

            return {
                "timestamp": self._tree_extractor._get_timestamp(),
                "metrics": metrics,
                "navigation_timing": perf
            }
        except Exception as e:
            self._logger.warning(f"Metrics collection failed: {e}")
            return {}

    async def execute_script(self, script: str) -> Any:

        if not self._current_page:
            raise RuntimeError("No active page")
        return await self._current_page.evaluate(script)

    async def highlight_element(self, selector: str) -> bool:

        if not self._current_page:
            return False

        try:
            await self._current_page.evaluate("(selector) => { const el = document.querySelector(selector); if (el) { el.style.outline = '5px solid yellow'; el.scrollIntoView({ behavior: 'smooth', block: 'center' }); } }", selector)
            return True
        except Exception as e:
            self._logger.warning(f"Failed to highlight element: {e}")
            return False