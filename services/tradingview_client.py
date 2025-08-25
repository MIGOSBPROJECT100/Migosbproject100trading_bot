import asyncio, os
from playwright.async_api import async_playwright
from config.settings import TRADINGVIEW
from utils.logger import get_logger
from pathlib import Path

log = get_logger("tv")

class TradingViewClient:
    def __init__(self):
        self.email = TRADINGVIEW["email"]
        self.password = TRADINGVIEW["password"]

    async def screenshot_symbol(self, symbol="XAUUSD", timeframe="15", out_dir="runtime/cache"):
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        out = f"{out_dir}/{symbol}_{timeframe}.png"
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context()
            page = await ctx.new_page()
            try:
                await page.goto("https://www.tradingview.com/#signin", timeout=60000)
                await page.click('button:has-text("Email")')
                await page.fill('input[name="username"]', self.email)
                await page.fill('input[name="password"]', self.password)
                await page.click('button[type="submit"]')
                await page.wait_for_timeout(4000)
                await page.goto(f"https://www.tradingview.com/chart/?symbol={symbol}", timeout=60000)
                # Select timeframe (e.g., 15 for 15m)
                await page.keyboard.press("Key5") if timeframe == "15" else None
                await page.wait_for_timeout(5000)
                await page.screenshot(path=out, full_page=True)
            except Exception as e:
                log.exception("TradingView screenshot failed: %s", e)
            finally:
                await browser.close()
        return out
