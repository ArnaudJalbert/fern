"""List all pages from the repository."""

from __future__ import annotations

from dataclasses import dataclass

from fern.domain.repositories.page_repository import PageRepository


class ListPagesUseCase:
    """List all pages from the repository."""

    @dataclass(frozen=True)
    class Input:
        """No input required."""

        pass

    @dataclass(frozen=True)
    class PageOutput:
        id: int
        title: str
        content: str

    @dataclass(frozen=True)
    class Output:
        pages: tuple[ListPagesUseCase.PageOutput, ...]

    def __init__(self, page_repository: PageRepository) -> None:
        """Initialize the use case with the page repository.

        Args:
            page_repository: The repository for listing pages.
        """
        self._page_repository = page_repository

    def execute(self, input_data: Input) -> Output:
        """Return output DTO with all pages."""
        # Load all pages from the repository
        pages = self._page_repository.list_all()

        # Build and return output DTO
        return self.Output(
            pages=tuple(
                self.PageOutput(
                    id=page.id,
                    title=page.title,
                    content=page.content,
                )
                for page in pages
            )
        )
