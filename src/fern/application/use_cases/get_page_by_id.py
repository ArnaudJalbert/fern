"""Use case: retrieve a single page by its id."""

from __future__ import annotations

from dataclasses import dataclass

from fern.application.errors import PageNotFoundError
from fern.application.repositories.page_repository import PageRepository


class GetPageByIdUseCase:
    """Retrieve a single page by its id."""

    @dataclass(frozen=True)
    class Input:
        page_id: int

    @dataclass(frozen=True)
    class Output:
        id: int
        title: str
        content: str

    def __init__(self, page_repository: PageRepository) -> None:
        """Initialize the use case with the page repository.

        Args:
            page_repository: The repository for loading pages.
        """
        self._page_repository = page_repository

    def execute(self, input_data: Input) -> Output:
        """Return output DTO for the page.

        Raises:
            PageNotFoundError: If the page is not found.
        """
        # Retrieve the page or raise if not found
        page = self._page_repository.get_by_id(input_data.page_id)
        if page is None:
            raise PageNotFoundError(page_id=input_data.page_id)

        # Build and return the output DTO
        return self.Output(id=page.id, title=page.title, content=page.content)
