import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.remote.webdriver import WebDriver
from typing import Any, Optional

from .base import AbstractBrowser, AbstractBrowserContext
from .selenium_context import SeleniumBrowserContext
from src.utils.webdriver_utils import find_chromedriver_executable # New import

class SeleniumBrowser(AbstractBrowser[SeleniumBrowserContext]):
    def __init__(self): # Removed webdriver_path from __init__
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

        # Determine chromedriver path
        chromedriver_exe_path = kwargs.get("executable_path")
        if not chromedriver_exe_path:
            chromedriver_exe_path = find_chromedriver_executable()

        try:
            if chromedriver_exe_path:
                self.driver = webdriver.Chrome(executable_path=chromedriver_exe_path, options=options)
            else:
                # Last resort: try with no explicit path (Selenium checks PATH)
                print("ChromeDriver executable_path not provided and not found by auto-discovery. Attempting to launch from system PATH.")
                self.driver = webdriver.Chrome(options=options)
            
            if not self.driver: # Should not happen if webdriver.Chrome() succeeds.
                 raise RuntimeError("Failed to initialize Selenium WebDriver.")

        except Exception as e:
            print(f"Failed to launch Selenium WebDriver: {e}")
            print("Please ensure ChromeDriver is installed and accessible in your PATH,")
            print("or provide the 'executable_path' in the browser configuration.")
            self.driver = None
            raise # Re-raise the exception

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
