from abc import ABC, abstractmethod
from typing import Any, Optional, TypeVar, Generic

# Type variable for Browser class
B = TypeVar('B')
# Type variable for BrowserContext class
BC = TypeVar('BC')
# Type variable for Page class
P = TypeVar('P')
# Type variable for Element class
E = TypeVar('E')


class AbstractPage(ABC, Generic[E]):
    @abstractmethod
    async def goto(self, url: str, timeout: Optional[int] = None, wait_until: Optional[str] = None) -> None:
        pass

    @abstractmethod
    async def get_content(self, timeout: Optional[int] = None) -> str:
        pass

    @abstractmethod
    async def query_selector(self, selector: str, timeout: Optional[int] = None) -> Optional[E]:
        pass

    @abstractmethod
    async def click(self, selector: str, timeout: Optional[int] = None) -> None:
        pass

    @abstractmethod
    async def type(self, selector: str, text: str, timeout: Optional[int] = None) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

    @abstractmethod
    async def title(self) -> str:
        pass
    
    @abstractmethod
    async def get_current_url(self) -> str:
        pass

    @abstractmethod
    async def go_back(self) -> None:
        pass

    @abstractmethod
    async def go_forward(self) -> None:
        pass

    @abstractmethod
    async def reload(self) -> None:
        pass

    @abstractmethod
    async def wait_for_load_state(self, state: Optional[str] = None, timeout: Optional[int] = None) -> None:
        pass

    @abstractmethod
    async def type_active(self, text: str, timeout: Optional[int] = None) -> None:
        """Types text into the currently focused element on the page."""
        pass

class AbstractBrowserContext(ABC, Generic[P]):
    @abstractmethod
    async def new_page(self) -> P:
        pass

    @abstractmethod
    async def pages(self) -> list[P]:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

    @abstractmethod
    async def get_state(self, **kwargs: Any) -> Any: # Define a proper BrowserState Pydantic model later if possible
        pass

    @abstractmethod
    async def get_current_page(self) -> P: # P is the generic Page type (AbstractPage)
        pass


class AbstractBrowser(ABC, Generic[BC]):
    @abstractmethod
    async def launch(self, **kwargs: Any) -> None:
        pass

    @abstractmethod
    async def new_context(self, **kwargs: Any) -> BC:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        pass
