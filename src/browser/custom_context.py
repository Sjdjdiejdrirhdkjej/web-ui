import base64 # Added import
import logging
from typing import Any, List, Optional, TYPE_CHECKING

from playwright.async_api import BrowserContext as PlaywrightBrowserContext
from playwright.async_api import Page as PlaywrightPageType
from playwright.async_api import ElementHandle # Added for PlaywrightPage
from .base import AbstractBrowserContext, AbstractPage

if TYPE_CHECKING:
    from .base import AbstractBrowser # To avoid circular import for type hinting
    # from .selenium_browser import SeleniumBrowser # Example if it were needed

logger = logging.getLogger(__name__)


class PlaywrightPage(AbstractPage[ElementHandle]):
    def __init__(self, pw_page: PlaywrightPageType):
        self.pw_page: PlaywrightPageType = pw_page

    async def goto(self, url: str, timeout: Optional[int] = None, wait_until: Optional[str] = None) -> None:
        # Playwright's goto timeout is in milliseconds
        await self.pw_page.goto(url, timeout=timeout, wait_until=wait_until)

    async def get_content(self, timeout: Optional[int] = None) -> str:
        # Playwright's content() does not take a timeout directly.
        # If timeout is critical, it might need to be wrapped, e.g. with asyncio.wait_for.
        return await self.pw_page.content()

    async def query_selector(self, selector: str, timeout: Optional[int] = None) -> Optional[ElementHandle]:
        # Playwright's query_selector has an optional timeout in some versions/contexts (e.g. page.wait_for_selector)
        # but the direct page.query_selector does not. For simple query, it's immediate.
        # If waiting is needed, page.wait_for_selector(selector, timeout=timeout) would be used.
        # For now, direct query:
        return await self.pw_page.query_selector(selector)

    async def click(self, selector: str, timeout: Optional[int] = None) -> None:
        # Playwright's click timeout is in milliseconds
        await self.pw_page.click(selector, timeout=timeout)

    async def type(self, selector: str, text: str, timeout: Optional[int] = None) -> None:
        # Playwright's type timeout is in milliseconds, applies to the entire operation
        await self.pw_page.type(selector, text, timeout=timeout)

    async def type_active(self, text: str, timeout: Optional[int] = None) -> None:
        # Playwright's keyboard.type has a `delay` option (ms between key presses), not a total timeout.
        # If timeout is crucial as an overall limit, asyncio.wait_for would be needed.
        # Using timeout as delay here is an approximation.
        delay = timeout if timeout is not None else 0
        await self.pw_page.keyboard.type(text, delay=delay)

    async def close(self) -> None:
        await self.pw_page.close()

    async def title(self) -> str:
        return await self.pw_page.title()
    
    async def get_current_url(self) -> str:
        return self.pw_page.url

    async def go_back(self) -> None:
        await self.pw_page.go_back()

    async def go_forward(self) -> None:
        await self.pw_page.go_forward()

    async def reload(self) -> None:
        await self.pw_page.reload()

    async def wait_for_load_state(self, state: Optional[str] = None, timeout: Optional[int] = None) -> None:
        # Playwright's wait_for_load_state timeout is in milliseconds
        await self.pw_page.wait_for_load_state(state, timeout=timeout)


class CustomBrowserContext(AbstractBrowserContext[PlaywrightPage]): # Changed generic type
    def __init__(
        self,
        pw_context: PlaywrightBrowserContext,
        browser: "AbstractBrowser", 
        config: dict[str, Any] | None = None
    ):
        self.pw_context: PlaywrightBrowserContext = pw_context
        self.browser = browser 
        self.config = config if config is not None else {}

    async def new_page(self) -> PlaywrightPage: # Return type changed
        pw_page = await self.pw_context.new_page()
        return PlaywrightPage(pw_page)

    async def pages(self) -> List[PlaywrightPage]: # Return type changed
        pw_pages = self.pw_context.pages
        return [PlaywrightPage(p) for p in pw_pages]

    async def close(self) -> None:
        await self.pw_context.close()

    async def get_current_page(self) -> PlaywrightPage: # Implemented
        pw_pages = self.pw_context.pages
        if not pw_pages:
            # Or, if context should always have a page, create one:
            # return await self.new_page()
            raise RuntimeError("No pages available in the browser context.")
        return PlaywrightPage(pw_pages[-1]) # Assuming last page is current

    async def get_state(self, **kwargs: Any) -> dict[str, Any]:
        current_page_wrapper = await self.get_current_page()
        if not current_page_wrapper:
            # This case should ideally not happen if a page is always present
            # or created by get_current_page if none exist.
            return {
                "url": "",
                "html_content": "",
                "accessibility_tree": None,
                "focused_element_id": None,
                "viewport_size": self.pw_context.viewport_size or {"width": 0, "height": 0}, # Context viewport if no page
                "screenshot": None, # Could take screenshot of empty page if needed
            }

        page = current_page_wrapper.pw_page # Access the underlying Playwright Page

        # 1. Get URL
        url = page.url

        # 2. Get HTML Content
        try:
            html_content = await page.content()
        except Exception:
            html_content = "" # Or handle error appropriately

        # 3. Get Accessibility Tree
        # include_text_content=True can be added if text directly in snapshot is desired
        try:
            accessibility_tree = await page.accessibility.snapshot(interesting_only=kwargs.get("interesting_only", False))
        except Exception:
            accessibility_tree = None # Or handle error

        # 4. Get Focused Element (this requires custom JS or Playwright's locator focus state)
        # For simplicity, this is a placeholder. A robust solution might involve:
        # - page.evaluate("document.activeElement ? document.activeElement.id : null")
        # - Or finding an element with a 'focused' state if Playwright's locators support it.
        # For now, we'll represent this as not easily available without more complex logic.
        focused_element_info = None 
        try:
            # Attempt to get focused element via JS. Requires element to have an ID.
            focused_element_id = await page.evaluate("document.activeElement && document.activeElement.id ? document.activeElement.id : null")
            if focused_element_id:
                # Optionally, try to find this element in the accessibility tree if IDs are consistent
                # This is non-trivial. For now, just the ID.
                focused_element_info = {"id": focused_element_id}
            # If no ID, one could try to get other attributes or a unique selector,
            # but this quickly becomes complex.
        except Exception:
            focused_element_info = None


        # 5. Get Viewport Size (from the page, which is more accurate than context if available)
        viewport_size = page.viewport_size if page.viewport_size else self.pw_context.viewport_size

        # 6. Get Screenshot (optional, as base64)
        screenshot_base64 = None
        if kwargs.get("capture_screenshot", True): # Default to true, allow disabling
            try:
                screenshot_bytes = await page.screenshot()
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            except Exception:
                screenshot_base64 = None # Or handle error

        return {
            "url": url,
            "html_content": html_content,
            "accessibility_tree": accessibility_tree,
            "focused_element_info": focused_element_info, # Placeholder for now
            "viewport_size": viewport_size or {"width": 0, "height": 0},
            "screenshot_base64": screenshot_base64,
            # Consider adding other useful state like cookies, page title etc.
            "title": await page.title()
        }
