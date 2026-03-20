"""List databases via a repository. The use case does not depend on the filesystem."""

from __future__ import annotations

from dataclasses import dataclass

from fern.application.repositories.database_repository import DatabaseRepository


class ListDatabasesUseCase:
    """List all databases from the given repository."""

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
        """Initialize the use case with the database repository.

        Args:
            database_repository: The repository for listing databases.
        """
        self._database_repository = database_repository

    def execute(self, input_data: Input) -> Output:
        """Return output DTO with all databases."""
        # Load all databases and sort by name
        all_databases = self._database_repository.list_all()
        sorted_databases = sorted(
            all_databases,
            key=lambda database: database.name,
        )

        # Build and return output DTO
        databases = tuple(
            self.DatabaseOutput(
                name=database.name,
                pages=tuple(
                    self.PageOutput(
                        id=page.id,
                        title=page.title,
                        content=page.content,
                    )
                    for page in database.pages
                ),
            )
            for database in sorted_databases
        )
        return self.Output(databases=databases)
