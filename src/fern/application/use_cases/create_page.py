"""Use case: create a new page in the repository (configured database folder)."""

from __future__ import annotations

from dataclasses import dataclass

from fern.domain.repositories.page_repository import PageRepository


class CreatePageUseCase:
    """Create a new page; returns output DTO with id, title, content."""

    @dataclass(frozen=True)
    class Input:
        title: str
        content: str = ""

    @dataclass(frozen=True)
    class Output:
        page_id: int
        title: str
        content: str

    def __init__(self, page_repository: PageRepository) -> None:
        """Initialize the use case with the page repository.

        Args:
            page_repository: The repository for creating pages.
        """
        self._page_repository = page_repository

    def execute(self, input_data: Input) -> Output:
        """Create a page and return its output DTO."""
        # Create the page in the repository
        page = self._page_repository.create(
            input_data.title,
            input_data.content,
        )

        # Build and return output DTO
        return self.Output(
            page_id=page.id,
            title=page.title,
            content=page.content,
        )
