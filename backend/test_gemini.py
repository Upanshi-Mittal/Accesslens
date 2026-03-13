
import asyncio
from playwright.async_api import async_playwright

async def test_gemini():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        url = "https://gemini.google.com/"
        print(f"Navigating to {url}...")
        try:
            # Try 'load' instead of 'networkidle'
            response = await page.goto(url, wait_until="load", timeout=60000)
            print(f"Response status: {response.status if response else 'No response'}")
            
            # Check for bot detection or blocking
            title = await page.title()
            print(f"Page title: {title}")
            
            # Print a snippet of HTML to see what's there
            content = await page.content()
            print(f"Page content length: {len(content)}")
            print(f"HTML snippet: {content[:1000]}")
            
            if "Google" in title or "Gemini" in title:
                print("Initial load successful.")
            else:
                print("Likely blocked or redirected.")
                
            # Wait a bit more
            await asyncio.sleep(5)
            
            # Check accessibility tree availability
            try:
                snapshot = await page.accessibility.snapshot()
                print(f"Accessibility snapshot size: {len(str(snapshot))}")
            except Exception as e:
                print(f"Accessibility snapshot failed: {e}")
                
        except Exception as e:
            print(f"Navigation/Extraction failed: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_gemini())
