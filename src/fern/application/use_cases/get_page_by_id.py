"""Retrieve a single page by its id."""

from __future__ import annotations

from dataclasses import dataclass

from fern.domain.repositories.page_repository import PageRepository


class GetPageByIdUseCase:
    """Use case: retrieve a single page by its id."""

    @dataclass(frozen=True)
    class Input:
        page_id: int

    @dataclass(frozen=True)
    class PageOutput:
        id: int
        title: str
        content: str

    @dataclass(frozen=True)
    class Output:
        success: bool
        id: int = 0
        title: str = ""
        content: str = ""

    def __init__(self, page_repository: PageRepository) -> None:
        self._page_repository = page_repository

    def execute(self, input_data: Input) -> Output:
        """Return output DTO for the page, or success=False if not found."""
        page = self._page_repository.get_by_id(input_data.page_id)
        if page is None:
            return self.Output(success=False)
        return self.Output(
            success=True,
            id=page.id,
            title=page.title,
            content=page.content,
        )
