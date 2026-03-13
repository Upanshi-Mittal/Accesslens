import pytest
import asyncio
from app.core.browser_manager import BrowserManager
from playwright.async_api import Page
import time

@pytest.mark.asyncio
async def test_browser_manager_singleton():
    """Verify BrowserManager is a singleton."""
    bm1 = BrowserManager()
    bm2 = BrowserManager()
    assert bm1 is bm2

@pytest.mark.asyncio
async def test_browser_manager_max_concurrent_pages():
    """Verify max concurrent pages logic and timeout handling."""
    bm = BrowserManager()
    await bm.initialize(headless=True)
    
    # Temporarily reduce max for faster testing
    original_max = bm._max_concurrent_pages
    bm._max_concurrent_pages = 2
    
    pages = []
    try:
        # Allocate max pages
        pages.append(await bm.get_page(timeout=5.0))
        pages.append(await bm.get_page(timeout=5.0))
        assert bm._active_pages == 2

        # 3rd page should timeout after hitting max
        with pytest.raises(TimeoutError, match="Timeout acquiring browser page"):
            await bm.get_page(timeout=1.0)
            
    finally:
        for p in pages:
            await bm.release_page(p)
        bm._max_concurrent_pages = original_max
        assert bm._active_pages == 0

@pytest.mark.asyncio
async def test_browser_context_manager():
    """Verify the async context manager automatically releases the page."""
    bm = BrowserManager()
    await bm.initialize(headless=True)
    
    initial_active = bm._active_pages
    
    async with bm.page_session(timeout=5.0) as page:
        assert bm._active_pages == initial_active + 1
        assert isinstance(page, Page)
        
    assert bm._active_pages == initial_active
    
    # Clean up
    await bm.close()
