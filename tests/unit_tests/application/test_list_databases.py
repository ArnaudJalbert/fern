"""Unit tests for ListDatabasesUseCase."""

from unittest.mock import MagicMock

from fern.application.use_cases.list_databases import ListDatabasesUseCase
from fern.domain.entities import Database


def test_list_databases_returns_sorted() -> None:
    repo = MagicMock()
    repo.list_all.return_value = [
        Database(name="Z", pages=[]),
        Database(name="A", pages=[]),
    ]

    use_case = ListDatabasesUseCase(database_repository=repo)
    out = use_case.execute(ListDatabasesUseCase.Input())

    assert [d.name for d in out.databases] == ["A", "Z"]
    repo.list_all.assert_called_once()


def test_list_databases_empty() -> None:
    repo = MagicMock()
    repo.list_all.return_value = []

    use_case = ListDatabasesUseCase(database_repository=repo)
    out = use_case.execute(ListDatabasesUseCase.Input())

    assert out.databases == ()
