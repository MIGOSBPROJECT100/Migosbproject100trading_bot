import os, asyncio
from services.logger import get_logger
from config import TV_EMAIL, TV_PASSWORD, SCREENSHOT_DIR

logger = get_logger("tradingview")

# Playwright automation for TradingView chart screenshots
async def screenshot_chart(symbol: str, timeframe: str = "15", dark: bool = True) -> str:
    """
    Returns the local file path to the captured chart screenshot, or '' on failure.
    """
    try:
        from playwright.async_api import async_playwright
    except Exception as e:
        logger.exception("Playwright import error: %s", e)
        return ""

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    out_path = os.path.join(SCREENSHOT_DIR, f"{symbol.replace('/','_')}_{timeframe}.png")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context()
            page = await context.new_page()

            # Login
            await page.goto("https://www.tradingview.com/#signin")
            await page.wait_for_timeout(2500)
            await page.click("text=Email")
            await page.wait_for_selector("input[name='email']")
            await page.fill("input[name='email']", TV_EMAIL)
            await page.fill("input[name='password']", TV_PASSWORD)
            await page.click("button[type='submit']")

            await page.wait_for_timeout(4000)
            # Open chart for symbol (general URL pattern)
            await page.goto(f"https://www.tradingview.com/chart/?symbol=FX_IDC:{symbol.replace('/','')}")
            await page.wait_for_timeout(5000)

            # Set timeframe
            await page.keyboard.press("KeyS")  # open symbol/timeframe panel if needed
            await page.wait_for_timeout(500)
            # Use URL param fallback for timeframe by navigating again
            await page.goto(f"https://www.tradingview.com/chart/?symbol=FX_IDC:{symbol.replace('/','')}&interval={timeframe}")
            await page.wait_for_timeout(4000)

            # Optional dark/light toggles can be skipped; capture viewport
            await page.screenshot(path=out_path, full_page=True)

            await context.close()
            await browser.close()
            logger.info("Saved TradingView screenshot: %s", out_path)
            return out_path
    except Exception as e:
        logger.exception("TradingView screenshot error: %s", e)
        return ""
