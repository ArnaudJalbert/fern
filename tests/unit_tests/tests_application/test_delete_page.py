"""Unit tests for DeletePageUseCase."""

import pytest
from unittest.mock import MagicMock

from fern.application.errors import PageNotFoundError
from fern.application.use_cases.delete_page import DeletePageUseCase
from fern.domain.entities import Page


def test_delete_page_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = Page(id=1, title="T", content="")

    use_case = DeletePageUseCase(page_repository=repo)
    use_case.execute(DeletePageUseCase.Input(page_id=1))

    repo.delete.assert_called_once_with(1)


def test_delete_page_not_found() -> None:
    repo = MagicMock()
    repo.get_by_id.return_value = None

    use_case = DeletePageUseCase(page_repository=repo)
    with pytest.raises(PageNotFoundError):
        use_case.execute(DeletePageUseCase.Input(page_id=999))

    repo.delete.assert_not_called()
