import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver
from typing import Any, Optional

from .base import AbstractBrowser, AbstractBrowserContext
from .selenium_context import SeleniumBrowserContext # This will be created in the next step

class SeleniumBrowser(AbstractBrowser[SeleniumBrowserContext]):
    def __init__(self, webdriver_path: Optional[str] = None):
        self.webdriver_path: Optional[str] = webdriver_path
        self.driver: Optional[WebDriver] = None
        self.launch_options: dict[str, Any] = {}

    async def launch(self, **kwargs: Any) -> None:
        if self.driver:
            # Already launched
            return

        self.launch_options = kwargs
        options = ChromeOptions()

        if kwargs.get("headless", False):
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")  # Recommended for headless

        window_size = kwargs.get("browser_window_size")
        if window_size and isinstance(window_size, dict):
            width = window_size.get("width", 1280)
            height = window_size.get("height", 720)
            options.add_argument(f"--window-size={width},{height}")
        
        # Add any other desired options from kwargs
        # Example: options.add_argument("--disable-extensions")

        # The executable_path can be passed in kwargs or use self.webdriver_path
        executable_path = kwargs.get("executable_path", self.webdriver_path)

        try:
            if executable_path:
                self.driver = webdriver.Chrome(executable_path=executable_path, options=options)
            else:
                # Attempt to use WebDriver from PATH if executable_path is not provided
                self.driver = webdriver.Chrome(options=options)
            # Potentially add a check here to ensure driver started, e.g., by getting title
        except Exception as e:
            # Log error or raise a custom exception
            print(f"Failed to launch Selenium WebDriver: {e}")
            self.driver = None
            raise # Re-raise the exception to signal failure

    async def new_context(self, **kwargs: Any) -> SeleniumBrowserContext:
        if not self.driver:
            raise ConnectionError("Browser is not launched or not connected.")
        # For Selenium, a "context" can be considered the browser instance itself.
        # We'll pass the driver and this browser instance to SeleniumBrowserContext.
        # kwargs here could be used by SeleniumBrowserContext if needed in the future.
        return SeleniumBrowserContext(browser=self, driver=self.driver, context_kwargs=kwargs)

    async def close(self) -> None:
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                # Log error
                print(f"Error closing Selenium WebDriver: {e}")
            finally:
                self.driver = None

    @property
    def is_connected(self) -> bool:
        return self.driver is not None and self.driver.session_id is not None
