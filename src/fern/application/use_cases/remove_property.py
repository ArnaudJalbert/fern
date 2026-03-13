"""Use case: remove a property from the schema and from all pages."""

from __future__ import annotations

from dataclasses import dataclass

from fern.domain.repositories.database_repository import DatabaseRepository
from fern.domain.repositories.page_repository import PageRepository


class RemovePropertyUseCase:
    """Remove a property from the schema and remove its value from every page."""

    @dataclass(frozen=True)
    class Input:
        database_name: str
        property_id: str

    @dataclass(frozen=True)
    class Output:
        success: bool

    def __init__(
        self,
        database_repository: DatabaseRepository,
        page_repository: PageRepository,
    ) -> None:
        self._database_repository = database_repository
        self._page_repository = page_repository

    def execute(self, input_data: Input) -> Output:
        properties, property_order = self._database_repository.get_schema(
            input_data.database_name
        )
        new_properties = [p for p in properties if p.id != input_data.property_id]
        if len(new_properties) == len(properties):
            return self.Output(success=False)
        new_order = [i for i in property_order if i != input_data.property_id]
        self._database_repository.save_schema(
            input_data.database_name, new_properties, new_order
        )
        for page in self._page_repository.list_all():
            new_list = [p for p in page.properties if p.id != input_data.property_id]
            self._page_repository.update(
                page.id, page.title, page.content, properties=new_list
            )
        return self.Output(success=True)
