"""Unit tests for ListPagesUseCase."""

from unittest.mock import MagicMock

from fern.application.use_cases.list_pages import ListPagesUseCase
from fern.domain.entities import Page


def test_list_pages_returns_all() -> None:
    repo = MagicMock()
    repo.list_all.return_value = [
        Page(id=1, title="A", content=""),
        Page(id=2, title="B", content=""),
    ]

    use_case = ListPagesUseCase(page_repository=repo)
    out = use_case.execute(ListPagesUseCase.Input())

    assert len(out.pages) == 2
    assert out.pages[0].id == 1 and out.pages[0].title == "A"
    assert out.pages[1].id == 2 and out.pages[1].title == "B"
    repo.list_all.assert_called_once()
