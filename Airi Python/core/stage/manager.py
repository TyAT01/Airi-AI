import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class PageConfig(BaseModel):
    id: str
    title: str
    route: str
    metadata: Dict[str, Any] = {}

class StageManager:
    def __init__(self):
        self.pages: Dict[str, PageConfig] = {}
        self.active_page_id: Optional[str] = None
        self._initialize_pages()

    def _initialize_pages(self):
        # Mirroring common pages in Stage UI
        self.add_page(PageConfig(id="home", title="Home", route="/"))
        self.add_page(PageConfig(id="settings", title="Settings", route="/settings"))
        self.add_page(PageConfig(id="devtools", title="DevTools", route="/devtools"))
        self.active_page_id = "home"

    def add_page(self, page: PageConfig):
        self.pages[page.id] = page
        logger.info(f"Page added: {page.title}")

    def navigate_to(self, page_id: str):
        if page_id in self.pages:
            self.active_page_id = page_id
            logger.info(f"Navigated to: {self.pages[page_id].title}")
        else:
            logger.warning(f"Page not found: {page_id}")

class LayoutConfig(BaseModel):
    show_sidebar: bool = True
    theme: str = "dark"
    widgets: List[str] = []

class LayoutManager:
    def __init__(self):
        self.config = LayoutConfig()

    def update_layout(self, updates: Dict[str, Any]):
        new_config = self.config.dict()
        new_config.update(updates)
        self.config = LayoutConfig(**new_config)
        logger.info(f"Layout updated: {self.config}")
