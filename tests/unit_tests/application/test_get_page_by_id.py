"""Unit tests for GetPageByIdUseCase."""

from unittest.mock import MagicMock

from fern.application.use_cases.get_page_by_id import GetPageByIdUseCase
from fern.domain.entities import Page


def test_get_page_by_id_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = Page(id=1, title="T", content="C")

    use_case = GetPageByIdUseCase(page_repository=repo)
    out = use_case.execute(GetPageByIdUseCase.Input(page_id=1))

    assert out.success is True
    assert out.id == 1
    assert out.title == "T"
    assert out.content == "C"
    repo.get_by_id.assert_called_once_with(1)


def test_get_page_by_id_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    use_case = GetPageByIdUseCase(page_repository=repo)
    out = use_case.execute(GetPageByIdUseCase.Input(page_id=999))

    assert out.success is False
