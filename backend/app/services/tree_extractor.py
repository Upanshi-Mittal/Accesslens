from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import asyncio

async def extract_accessibility_tree(url: str) -> dict:
    """
    Extracts the rendered accessibility tree from a webpage using CDP.

    Args:
        url (str): Target webpage URL

    Returns:
        dict: Accessibility tree snapshot

    Raises:
        RuntimeError: If extraction fails
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state("networkidle")

                # Using CDP to get the full accessibility tree, same as core extractor
                client = await page.context.new_cdp_session(page)
                await client.send("Accessibility.enable")
                result = await client.send("Accessibility.getFullAXTree")
                
                raw_tree = {"nodes": result.get("nodes", [])}

                if not raw_tree.get("nodes"):
                    # Fallback to page.accessibility.snapshot() if it exists
                    try:
                        raw_tree = await page.accessibility.snapshot()
                    except:
                        raise RuntimeError("Accessibility tree snapshot returned empty.")

                return raw_tree

            finally:
                await browser.close()

    except PlaywrightTimeoutError:
        raise RuntimeError("Page load timed out while extracting accessibility tree.")
    except Exception as e:
        raise RuntimeError(f"Accessibility tree extraction failed: {str(e)}")