from __future__ import annotations

from abc import ABC, abstractmethod

from fern.domain.entities import Page, Property


class PageRepository(ABC):
    """Port for persisting and retrieving Page entities."""

    @abstractmethod
    def get_by_id(self, page_id: int) -> Page | None:
        """Return the page with the given id, or None if not found."""
        ...

    @abstractmethod
    def list_all(self) -> list[Page]:
        """Return all pages, in no particular order."""
        ...

    @abstractmethod
    def update(
        self,
        page_id: int,
        title: str,
        content: str,
        *,
        properties: list[Property] | None = None,
    ) -> None:
        """Update the page; if properties is given, replace the page's properties list."""
        ...

    @abstractmethod
    def create(self, title: str, content: str) -> Page:
        """Create a new page with the given title and content; returns the created Page (with generated id)."""
        ...

    @abstractmethod
    def delete(self, page_id: int) -> None:
        """Remove the page with the given id. No-op if not found."""
        ...
