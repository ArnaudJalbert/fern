"""Use case: add a property to a single page (not to the database schema)."""

from __future__ import annotations

from dataclasses import dataclass

from fern.domain.entities import Property, PropertyType
from fern.domain.repositories.page_repository import PageRepository


class AddPagePropertyUseCase:
    """Add a property to one page only; does not change the database schema."""

    @dataclass(frozen=True)
    class Input:
        page_id: int
        property_id: str
        name: str
        type: PropertyType

    @dataclass(frozen=True)
    class Output:
        success: bool

    def __init__(self, page_repository: PageRepository) -> None:
        self._page_repository = page_repository

    def execute(self, input_data: Input) -> Output:
        page = self._page_repository.get_by_id(input_data.page_id)
        if page is None:
            return self.Output(success=False)
        for p in page.properties:
            if p.id == input_data.property_id:
                return self.Output(success=False)
        default = input_data.type.value.default_value()
        new_prop = Property(
            id=input_data.property_id,
            name=input_data.name,
            type=input_data.type,
            value=default,
        )
        new_list = [*page.properties, new_prop]
        self._page_repository.update(
            page.id, page.title, page.content, properties=new_list
        )
        return self.Output(success=True)
