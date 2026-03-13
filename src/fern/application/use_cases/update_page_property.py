"""Use case: update a single property value on a page and persist."""

from __future__ import annotations

from dataclasses import dataclass

from fern.domain.entities.properties import Property
from fern.domain.repositories.page_repository import PageRepository


class UpdatePagePropertyUseCase:
    """Set the value of one property on a page and save."""

    @dataclass(frozen=True)
    class Input:
        page_id: int
        property_id: str
        value: bool | str

    @dataclass(frozen=True)
    class Output:
        success: bool

    def __init__(self, page_repository: PageRepository) -> None:
        self._page_repository = page_repository

    def execute(self, input_data: Input) -> Output:
        page = self._page_repository.get_by_id(input_data.page_id)
        if page is None:
            return self.Output(success=False)
        prop = next(
            (p for p in page.properties if p.id == input_data.property_id), None
        )
        if prop is None:
            return self.Output(success=False)
        value = (
            prop.type.value.coerce(input_data.value)
            if hasattr(prop.type.value, "coerce")
            else input_data.value
        )
        new_list = [
            Property(id=p.id, name=p.name, type=p.type, value=value)
            if p.id == input_data.property_id
            else p
            for p in page.properties
        ]
        self._page_repository.update(
            page.id,
            page.title,
            page.content,
            properties=new_list,
        )
        return self.Output(success=True)
