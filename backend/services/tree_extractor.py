from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def extract_accessibility_tree(url: str) -> dict:
    """
    Extracts the rendered accessibility tree from a webpage.

    Args:
        url (str): Target webpage URL

    Returns:
        dict: Accessibility tree snapshot

    Raises:
        RuntimeError: If extraction fails
    """

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle")

            raw_tree = page.accessibility.snapshot()

            browser.close()

            if not raw_tree:
                raise RuntimeError("Accessibility tree snapshot returned None.")

            return raw_tree

    except PlaywrightTimeoutError:
        raise RuntimeError("Page load timed out while extracting accessibility tree.")

    except Exception as e:
        raise RuntimeError(f"Accessibility tree extraction failed: {str(e)}")