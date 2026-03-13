


import pytest
import asyncio
from typing import Generator, Dict, Any
from playwright.async_api import async_playwright, Browser, Page
from app.core.config import settings
from app.core.browser_manager import browser_manager

@pytest.fixture(scope="session")
def event_loop():

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def browser():

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()

@pytest.fixture
async def page(browser: Browser):

    page = await browser.new_page()
    yield page
    await page.close()

@pytest.fixture
def test_html() -> str:

    from . import SAMPLE_HTML
    return SAMPLE_HTML

@pytest.fixture
def inaccessible_html() -> str:

    from . import INACCESSIBLE_HTML
    return INACCESSIBLE_HTML

@pytest.fixture
def mock_audit_request() -> Dict[str, Any]:

    return {
        "url": "https://example.com",
        "engines": ["wcag_deterministic", "contrast_engine", "structural_engine"],
        "enable_ai": False,
        "depth": "quick",
        "viewport": {"width": 1280, "height": 720},
        "wait_for_network_idle": True
    }

from app.main import app, lifespan

@pytest.fixture(autouse=True)
async def setup_test_env():


    settings.debug = True
    settings.log_level = "DEBUG"

    async with lifespan(app):
        yield




@pytest.fixture
async def initialized_browser_manager():

    await browser_manager.initialize(headless=True)
    yield browser_manager
    await browser_manager.close()