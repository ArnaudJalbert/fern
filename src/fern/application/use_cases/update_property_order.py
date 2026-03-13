"""Use case: update the display order of properties in a database."""

from __future__ import annotations

from dataclasses import dataclass

from fern.domain.repositories.database_repository import DatabaseRepository


class UpdatePropertyOrderUseCase:
    """Update the property_order array for a database; used for table/editor column order."""

    @dataclass(frozen=True)
    class Input:
        database_name: str
        property_order: tuple[str, ...]

    @dataclass(frozen=True)
    class Output:
        success: bool

    def __init__(self, database_repository: DatabaseRepository) -> None:
        self._database_repository = database_repository

    def execute(self, input_data: Input) -> Output:
        properties, _ = self._database_repository.get_schema(input_data.database_name)
        new_order = list(input_data.property_order)
        self._database_repository.save_schema(
            input_data.database_name, properties, new_order
        )
        return self.Output(success=True)
