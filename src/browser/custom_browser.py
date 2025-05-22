import asyncio
from typing import Any
from playwright.async_api import Browser as PlaywrightBrowser, async_playwright, Playwright
import logging

from .base import AbstractBrowser
from .custom_context import CustomBrowserContext
# Removed: from browser_use.browser.context import BrowserContext, BrowserContextConfig
# Removed: from browser_use.browser.browser import Browser
# Removed: import pdb
# Removed: from playwright.async_api import BrowserContext as PlaywrightBrowserContext (duplicate)


logger = logging.getLogger(__name__)


class CustomBrowser(AbstractBrowser[CustomBrowserContext]):

    def __init__(self) -> None:
        self.playwright: Playwright | None = None
        self.browser: PlaywrightBrowser | None = None
        self.launch_args: dict[str, Any] = {}

    async def launch(self, **kwargs: Any) -> None:
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(**kwargs)
        self.launch_args = kwargs

    async def new_context(self, **kwargs: Any) -> CustomBrowserContext:
        if not self.browser:
            raise ConnectionError("Browser not launched yet. Call launch() first.")
        
        # If a pydantic model like object is passed in kwargs under 'config'
        # and it has a .model_dump() method (like BrowserContextConfig might have had)
        # extract it. Otherwise, assume kwargs is already the flat dict.
        config_data = kwargs
        if 'config' in kwargs and hasattr(kwargs['config'], 'model_dump'):
            config_data = kwargs['config'].model_dump()
        elif 'config' in kwargs and isinstance(kwargs['config'], dict):
            config_data = kwargs['config']

        pw_context = await self.browser.new_context(**config_data)
        # Pass the original kwargs (or config_data if preferred) to CustomBrowserContext
        return CustomBrowserContext(pw_context=pw_context, browser=self, config=config_data)

    async def close(self) -> None:
        if self.browser and self.browser.is_connected():
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.browser = None
        self.playwright = None

    @property
    def is_connected(self) -> bool:
        return self.browser is not None and self.browser.is_connected()
