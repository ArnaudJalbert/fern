"""Unit tests for DeletePageUseCase."""

from unittest.mock import MagicMock

from fern.application.use_cases.delete_page import DeletePageUseCase
from fern.domain.entities import Page


def test_delete_page_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = Page(id=1, title="T", content="")

    use_case = DeletePageUseCase(page_repository=repo)
    out = use_case.execute(DeletePageUseCase.Input(page_id=1))

    assert out.deleted is True
    repo.delete.assert_called_once_with(1)


def test_delete_page_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    use_case = DeletePageUseCase(page_repository=repo)
    out = use_case.execute(DeletePageUseCase.Input(page_id=999))

    assert out.deleted is False
    repo.delete.assert_not_called()
