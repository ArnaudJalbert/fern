"""Use case: add a property to the schema only.

Applying the property to all pages is done asynchronously via ApplyPropertyToPagesUseCase.
"""

from __future__ import annotations

from dataclasses import dataclass

from fern.domain.entities import Property, PropertyType
from fern.domain.repositories.database_repository import DatabaseRepository


class AddPropertyUseCase:
    """Add a property to the schema only (no page updates)."""

    @dataclass(frozen=True)
    class Input:
        database_name: str
        property_id: str
        name: str
        type: PropertyType

    @dataclass(frozen=True)
    class Output:
        success: bool

    def __init__(self, database_repository: DatabaseRepository) -> None:
        self._database_repository = database_repository

    def execute(self, input_data: Input) -> Output:
        properties, property_order = self._database_repository.get_schema(
            input_data.database_name
        )
        for p in properties:
            if p.id == input_data.property_id:
                return self.Output(success=False)
        new_prop = Property(
            id=input_data.property_id,
            name=input_data.name,
            type=input_data.type,
        )
        self._database_repository.save_schema(
            input_data.database_name,
            [*properties, new_prop],
            [*property_order, input_data.property_id],
        )
        return self.Output(success=True)
