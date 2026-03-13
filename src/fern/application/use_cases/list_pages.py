"""List all pages from the repository."""

from __future__ import annotations

from dataclasses import dataclass

from fern.domain.repositories.page_repository import PageRepository


class ListPagesUseCase:
    """Use case: list all pages from the repository."""

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
        self._page_repository = page_repository

    def execute(self, input_data: Input) -> Output:
        """Return output DTO with all pages."""
        pages = self._page_repository.list_all()
        return self.Output(
            pages=tuple(
                self.PageOutput(id=p.id, title=p.title, content=p.content)
                for p in pages
            )
        )
