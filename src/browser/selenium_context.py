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
