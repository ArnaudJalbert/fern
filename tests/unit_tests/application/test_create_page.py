"""Unit tests for CreatePageUseCase."""

from unittest.mock import MagicMock

from fern.application.use_cases.create_page import CreatePageUseCase
from fern.domain.entities import Page


def test_create_page_returns_created_page() -> None:
    repo = MagicMock()
    created = Page(id=42, title="New", content="body")
    repo.create.return_value = created

    use_case = CreatePageUseCase(page_repository=repo)
    out = use_case.execute(CreatePageUseCase.Input(title="New", content="body"))

    assert out.page_id == 42
    assert out.title == "New"
    assert out.content == "body"
    repo.create.assert_called_once_with("New", "body")
