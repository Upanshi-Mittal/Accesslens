
import asyncio
from typing import Optional, Dict, Any, List
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import logging
from datetime import datetime
import traceback

class BrowserManager:


    _instance = None
    _browser: Optional[Browser] = None
    _context: Optional[BrowserContext] = None
    _playwright = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._logger = logging.getLogger(__name__)
        self._active_pages = 0
        self._max_concurrent_pages = 5
        self._lock = asyncio.Lock()

    async def initialize(self, headless: bool = True):

        if self._browser:
            return

        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=headless,
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-gpu'
                ]
            )


            self._context = await self._browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            self._logger.info("Browser initialized successfully")
        except Exception as e:
            self._logger.error(f"Failed to initialize browser: {e}")
            raise

    async def get_page(self) -> Page:

        while True:
            async with self._lock:
                can_allocate = self._active_pages < self._max_concurrent_pages
                if can_allocate:
                    self._active_pages += 1
                    break

            self._logger.warning("Max concurrent pages reached, waiting...")
            await asyncio.sleep(1)

        if not self._context:
            await self.initialize()

        page = await self._context.new_page()


        page.set_default_timeout(30000)

        return page

    async def release_page(self, page: Page):

        async with self._lock:
            try:
                await page.close()
            except Exception as e:
                self._logger.error(f"Error closing page: {e}")
            finally:
                self._active_pages -= 1

    async def close(self):

        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._context = None
        self._playwright = None
        self._logger.info("Browser closed")


browser_manager = BrowserManager()