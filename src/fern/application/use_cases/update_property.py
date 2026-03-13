"""Use case: update a property's name and/or type in the schema and on all pages."""

from __future__ import annotations

from dataclasses import dataclass

from fern.domain.entities import Property, PropertyType
from fern.domain.repositories.database_repository import DatabaseRepository
from fern.domain.repositories.page_repository import PageRepository


class UpdatePropertyUseCase:
    """Update a property's name and/or type in the schema and on every page."""

    @dataclass(frozen=True)
    class Input:
        database_name: str
        property_id: str
        new_name: str | None = None
        new_type: str | None = None

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
        properties, property_order = self._database_repository.get_schema(input_data.database_name)
        idx = next(
            (i for i, p in enumerate(properties) if p.id == input_data.property_id),
            None,
        )
        if idx is None:
            return self.Output(success=False)

        old = properties[idx]
        new_name = (input_data.new_name or old.name).strip() or old.name
        new_type = (
            PropertyType.from_key(input_data.new_type)
            if input_data.new_type is not None and input_data.new_type.strip()
            else old.type
        )

        updated = Property(id=old.id, name=new_name, type=new_type)
        new_props = [*properties]
        new_props[idx] = updated
        self._database_repository.save_schema(input_data.database_name, new_props, list(property_order))

        for page in self._page_repository.list_all():
            new_list = []
            for p in page.properties:
                if p.id == input_data.property_id:
                    raw = p.value
                    value = new_type.value.coerce(raw) if hasattr(new_type.value, "coerce") else raw
                    if value is None and hasattr(new_type.value, "default_value"):
                        value = new_type.value.default_value()
                    new_list.append(Property(id=p.id, name=new_name, type=new_type, value=value))
                else:
                    new_list.append(p)
            self._page_repository.update(
                page.id, page.title, page.content, properties=new_list
            )
        return self.Output(success=True)
