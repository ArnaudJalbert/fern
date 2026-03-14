"""Use case: remove a page from the repository (configured database folder)."""

from __future__ import annotations

from dataclasses import dataclass

from fern.application.errors import PageNotFoundError
from fern.domain.repositories.page_repository import PageRepository


class DeletePageUseCase:
    """Delete a page by id."""

    @dataclass(frozen=True)
    class Input:
        page_id: int

    def __init__(self, page_repository: PageRepository) -> None:
        """Initialize the use case with the page repository.

        Args:
            page_repository: The repository for loading and deleting pages.
        """
        self._page_repository = page_repository

    def execute(self, input_data: Input) -> None:
        """Delete the page with the given id.

        Raises:
            PageNotFoundError: If the page is not found.
        """
        # Retrieve the page or raise if not found
        page = self._page_repository.get_by_id(input_data.page_id)
        if page is None:
            raise PageNotFoundError(page_id=input_data.page_id)

        # Remove the page from the repository
        self._page_repository.delete(input_data.page_id)
