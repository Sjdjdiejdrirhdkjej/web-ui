import logging
from typing import Any, TYPE_CHECKING

from playwright.async_api import BrowserContext as PlaywrightBrowserContext
from playwright.async_api import Page as PlaywrightPageType

from .base import AbstractBrowserContext

if TYPE_CHECKING:
    from .base import AbstractBrowser # To avoid circular import for type hinting

logger = logging.getLogger(__name__)


class CustomBrowserContext(AbstractBrowserContext[PlaywrightPageType]):
    def __init__(
        self,
        pw_context: PlaywrightBrowserContext,
        browser: "AbstractBrowser", # Use forward reference string
        config: dict[str, Any] | None = None # config is now a dict
    ):
        self.pw_context = pw_context
        self.browser = browser
        self.config = config if config is not None else {}

    async def new_page(self) -> PlaywrightPageType:
        return await self.pw_context.new_page()

    async def pages(self) -> list[PlaywrightPageType]:
        return self.pw_context.pages

    async def close(self) -> None:
        await self.pw_context.close()
