import pytest
import asyncio
from src.browser.selenium_browser import SeleniumBrowser
from src.browser.base import AbstractBrowser, AbstractBrowserContext, AbstractPage # For type hints

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
async def selenium_browser() -> AbstractBrowser:
    browser = SeleniumBrowser()
    # Launch arguments can be empty if relying on find_chromedriver_executable
    # Or, provide a specific path for testing if available in the test environment:
    # await browser.launch(executable_path='/path/to/your/chromedriver')
    await browser.launch() 
    yield browser
    await browser.close()

@pytest.fixture
async def selenium_context(selenium_browser: AbstractBrowser) -> AbstractBrowserContext:
    context = await selenium_browser.new_context()
    yield context
    # Context close for selenium might be a no-op or handled by browser.close()
    # await context.close() # Ensure this is handled gracefully if it does nothing

@pytest.fixture
async def selenium_page(selenium_context: AbstractBrowserContext) -> AbstractPage:
    page = await selenium_context.new_page()
    # In Selenium, a "page" might not need explicit closing if it's just a view of the driver
    # and the browser context / browser handles cleanup.
    return page


async def test_selenium_launch_and_navigate(selenium_page: AbstractPage):
    """Test launching Selenium, navigating to a page, and checking title."""
    navigate_url = "http://example.com"
    expected_title = "Example Domain"

    await selenium_page.goto(navigate_url)
    page_title = await selenium_page.title()

    assert page_title == expected_title

async def test_selenium_get_content(selenium_page: AbstractPage):
    """Test getting content from a page using Selenium."""
    navigate_url = "http://example.com"
    await selenium_page.goto(navigate_url)
    content = await selenium_page.get_content()

    assert "<h1>Example Domain</h1>" in content
    assert "</html>" in content

# Add more tests here as needed, e.g., for query_selector, click, type_active
