"""List databases via a repository. The use case does not depend on the filesystem."""

from __future__ import annotations

from dataclasses import dataclass

from fern.domain.repositories.database_repository import DatabaseRepository


class ListDatabasesUseCase:
    """Use case: list all databases from the given repository."""

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
    class DatabaseOutput:
        name: str
        pages: tuple[ListDatabasesUseCase.PageOutput, ...]

    @dataclass(frozen=True)
    class Output:
        databases: tuple[ListDatabasesUseCase.DatabaseOutput, ...]

    def __init__(self, database_repository: DatabaseRepository) -> None:
        self._database_repository = database_repository

    def execute(self, input_data: Input) -> Output:
        """Return output DTO with all databases."""
        db_list = sorted(
            self._database_repository.list_all(),
            key=lambda d: d.name,
        )
        databases = tuple(
            self.DatabaseOutput(
                name=db.name,
                pages=tuple(
                    self.PageOutput(id=p.id, title=p.title, content=p.content)
                    for p in db.pages
                ),
            )
            for db in db_list
        )
        return self.Output(databases=databases)
