"""Use case: add a property (with default value) to every page in a database.

Used asynchronously after adding a property to the schema.
"""

from __future__ import annotations

from dataclasses import dataclass

from fern.domain.entities import Property, PropertyType
from fern.domain.repositories.page_repository import PageRepository


class ApplyPropertyToPagesUseCase:
    """Add the given property with default value to every page."""

    @dataclass(frozen=True)
    class Input:
        property_id: str
        name: str
        type: PropertyType

    def __init__(self, page_repository: PageRepository) -> None:
        self._page_repository = page_repository

    def execute(self, input_data: Input) -> None:
        default = input_data.type.value.default_value()
        new_prop = Property(
            id=input_data.property_id,
            name=input_data.name,
            type=input_data.type,
            value=default,
        )
        for page in self._page_repository.list_all():
            new_list = [*page.properties, new_prop]
            self._page_repository.update(
                page.id, page.title, page.content, properties=new_list
            )
