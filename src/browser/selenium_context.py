from typing import Any, List, Optional, TYPE_CHECKING
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import AbstractBrowserContext, AbstractPage

if TYPE_CHECKING:
    from .selenium_browser import SeleniumBrowser # To avoid circular import

class SeleniumPage(AbstractPage[WebElement]):
    def __init__(self, driver: WebDriver):
        self.driver: WebDriver = driver

    async def goto(self, url: str, timeout: Optional[int] = None, wait_until: Optional[str] = None) -> None:
        # Selenium's get command waits for page load by default.
        # 'wait_until' is more a Playwright concept, can be partially simulated if needed.
        if timeout:
            self.driver.set_page_load_timeout(timeout / 1000 if timeout else 30) # Selenium expects seconds
        self.driver.get(url)

    async def get_content(self, timeout: Optional[int] = None) -> str:
        # timeout is not directly applicable here in a simple way as page_source is immediate
        return self.driver.page_source

    async def query_selector(self, selector: str, timeout: Optional[int] = None) -> Optional[WebElement]:
        try:
            if timeout:
                element = WebDriverWait(self.driver, timeout / 1000 if timeout else 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
            else:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
            return element
        except: # Broad exception for TimeoutException, NoSuchElementException
            return None

    async def click(self, selector: str, timeout: Optional[int] = None) -> None:
        element = await self.query_selector(selector, timeout)
        if element:
            element.click()
        else:
            raise Exception(f"Element with selector '{selector}' not found for click.")

    async def type(self, selector: str, text: str, timeout: Optional[int] = None) -> None:
        element = await self.query_selector(selector, timeout)
        if element:
            element.send_keys(text)
        else:
            raise Exception(f"Element with selector '{selector}' not found for type.")

    async def close(self) -> None:
        # In Selenium, a "page" is usually a window or tab. Closing it means closing the window/tab.
        # If it's the last window, it might quit the browser.
        self.driver.close() 

    async def title(self) -> str:
        return self.driver.title

    async def get_current_url(self) -> str:
        return self.driver.current_url

    async def go_back(self) -> None:
        self.driver.back()

    async def go_forward(self) -> None:
        self.driver.forward()

    async def reload(self) -> None:
        self.driver.refresh()

    async def wait_for_load_state(self, state: Optional[str] = None, timeout: Optional[int] = None) -> None:
        # Selenium waits for document.readyState to be 'complete' by default on driver.get().
        # This is a simplified simulation. For specific states like 'domcontentloaded' or 'networkidle',
        # more complex JavaScript execution or checks would be needed.
        # For now, we assume 'complete' is the primary state handled by driver.get().
        # If a timeout is provided, we can use WebDriverWait for a general condition.
        if timeout:
            try:
                WebDriverWait(self.driver, timeout / 1000 if timeout else 30).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
            except: # TimeoutException
                # Handle or log timeout if necessary
                pass 
        # If no timeout, assume previous operations handled load state or it's not critical.

    async def type_active(self, text: str, timeout: Optional[int] = None) -> None:
        """Types text into the currently focused element on the page."""
        try:
            active_element = self.driver.switch_to.active_element
            # Consider adding a wait here if needed, though active_element should be immediate
            active_element.send_keys(text)
        except Exception as e:
            # Log or handle case where there might not be an active element
            # or it's not interactable. For now, re-raise or log.
            print(f"Error typing into active element: {e}")
            # raise  # Optionally re-raise


class SeleniumBrowserContext(AbstractBrowserContext[SeleniumPage]):
    def __init__(self, browser: "SeleniumBrowser", driver: WebDriver, context_kwargs: Optional[dict[str, Any]] = None):
        self.browser: "SeleniumBrowser" = browser
        self.driver: WebDriver = driver
        self.context_kwargs = context_kwargs if context_kwargs else {}
        self._current_page: SeleniumPage = SeleniumPage(self.driver) # Main window/tab as the initial page

    async def new_page(self) -> SeleniumPage:
        # Selenium handles new "pages" as new windows/tabs.
        # This could open a new tab/window and switch to it.
        # For simplicity, we'll assume for now new_page might just return the current page
        # or if an action causes a new window to open, the driver will switch to it.
        # A more robust implementation could manage multiple window handles.
        # Let's return a new SeleniumPage instance for the current driver focus.
        # If the user wants a *new* tab, they'd typically use an action that does driver.execute_script("window.open('');")
        # and then this context would need to switch to it.
        return SeleniumPage(self.driver) # Returns a new Page wrapper for the *current* driver window

    async def pages(self) -> List[SeleniumPage]:
        # A more complex implementation would list all window handles and create SeleniumPage for each.
        # For now, return a list containing the current page.
        return [self._current_page]

    async def close(self) -> None:
        # In Selenium, a context doesn't have an independent lifecycle like in Playwright if it's tied to the main driver.
        # Closing the browser itself is handled by SeleniumBrowser.close().
        # This method could close all windows/tabs opened by this "context" except the initial one,
        # or simply do nothing if the context is just a view over the single driver.
        # For now, let's make it a no-op.
        pass

    async def get_current_page(self) -> SeleniumPage:
        """Returns the current page associated with this context."""
        # Assuming self._current_page is always up-to-date or represents the primary window/tab
        return self._current_page

    async def get_state(self, **kwargs: Any) -> dict[str, Any]:
        if not self._current_page: # Should not happen if __init__ always creates one
            return {
                "url": "", "html_content": "", "accessibility_tree": None,
                "focused_element_info": None, "viewport_size": {"width": 0, "height": 0},
                "screenshot_base64": None, "title": ""
            }

        page_driver = self._current_page.driver # Access the WebDriver instance

        # 1. Get URL
        url = page_driver.current_url

        # 2. Get HTML Content
        try:
            html_content = page_driver.page_source
        except Exception:
            html_content = ""

        # 3. Accessibility Tree (Not available directly in Selenium like Playwright)
        # We can include a message indicating this or return a very simplified structure if needed.
        # For now, returning None or an empty structure.
        accessibility_tree = None 

        # 4. Get Focused Element
        focused_element_info = None
        try:
            active_element = page_driver.switch_to.active_element
            if active_element:
                # Try to get some identifying attributes
                tag_name = active_element.tag_name
                elem_id = active_element.get_attribute('id')
                elem_name = active_element.get_attribute('name')
                # More attributes could be fetched: active_element.text, active_element.get_attribute('class'), etc.
                focused_element_info = {
                    "tag_name": tag_name,
                    "id": elem_id if elem_id else None,
                    "name": elem_name if elem_name else None,
                    # "text": active_element.text # Be careful, .text can be slow or stale
                }
        except Exception: # NoSuchElementException if no active element, or stale element
            focused_element_info = None
            
        # 5. Get Viewport Size (Window size in Selenium)
        try:
            window_size = page_driver.get_window_size() # Returns {'width': ..., 'height': ...}
        except Exception:
            window_size = {"width": 0, "height": 0}


        # 6. Get Screenshot (optional, as base64)
        screenshot_base64 = None
        if kwargs.get("capture_screenshot", True): # Default to true
            try:
                screenshot_base64 = page_driver.get_screenshot_as_base64()
            except Exception:
                screenshot_base64 = None
        
        # 7. Get Page Title
        try:
            title = page_driver.title
        except Exception:
            title = ""

        return {
            "url": url,
            "html_content": html_content,
            "accessibility_tree": accessibility_tree, # Basic placeholder
            "focused_element_info": focused_element_info,
            "viewport_size": window_size,
            "screenshot_base64": screenshot_base64,
            "title": title
        }
