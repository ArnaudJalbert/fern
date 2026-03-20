from fern.application.repositories.page_repository import PageRepository
from fern.domain.entities.page import Page
from fern.domain.entities.properties import Property


class InMemoryPageRepository(PageRepository):
    """In-memory implementation of PageRepository for development and testing."""

    def __init__(self, pages: dict[int, Page] | None = None) -> None:
        self._pages: dict[int, Page] = dict(pages) if pages else {}

    def get_by_id(self, page_id: int) -> Page | None:
        return self._pages.get(page_id)

    def list_all(self) -> list[Page]:
        return list(self._pages.values())

    def update(
        self,
        page_id: int,
        title: str,
        content: str,
        *,
        properties: list[Property] | None = None,
    ) -> None:
        if page_id not in self._pages:
            return
        p = self._pages[page_id]
        props = list(p.properties) if properties is None else properties
        self._pages[page_id] = Page(
            id=page_id, title=title, content=content, properties=props
        )

    def create(self, title: str, content: str) -> Page:
        next_id = max(self._pages.keys(), default=0) + 1
        page = Page(id=next_id, title=title, content=content, properties=[])
        self._pages[next_id] = page
        return page

    def delete(self, page_id: int) -> None:
        self._pages.pop(page_id, None)
