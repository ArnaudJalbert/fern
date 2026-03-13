"""Use case: remove a page from the repository (configured database folder)."""

from dataclasses import dataclass

from fern.domain.repositories.page_repository import PageRepository


class DeletePageUseCase:
    """Delete a page by id; returns whether it was found and removed."""

    @dataclass(frozen=True)
    class Input:
        page_id: int

    @dataclass(frozen=True)
    class Output:
        deleted: bool

    def __init__(self, page_repository: PageRepository) -> None:
        self._page_repository = page_repository

    def execute(self, input_data: Input) -> Output:
        page = self._page_repository.get_by_id(input_data.page_id)
        if page is None:
            return self.Output(deleted=False)
        self._page_repository.delete(input_data.page_id)
        return self.Output(deleted=True)
