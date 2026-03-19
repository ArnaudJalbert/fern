"""Use case: remove a property from the schema and from all pages."""

from __future__ import annotations

from dataclasses import dataclass

from fern.application.errors import PropertyNotFoundError
from fern.application.repositories.database_repository import DatabaseRepository
from fern.application.repositories.page_repository import PageRepository


class RemovePropertyUseCase:
    """Remove a property from the schema and remove its value from every page."""

    @dataclass(frozen=True)
    class Input:
        database_name: str
        property_id: str

    def __init__(
        self,
        database_repository: DatabaseRepository,
        page_repository: PageRepository,
    ) -> None:
        """Initialize the use case with the database and page repositories.

        Args:
            database_repository: The repository for accessing and saving the schema.
            page_repository: The repository for updating pages.
        """
        self._database_repository = database_repository
        self._page_repository = page_repository

    def execute(self, input_data: Input) -> None:
        """Remove a property from the schema and from every page.

        Raises:
            PropertyNotFoundError: If the property is not in the schema.
        """
        # Load current schema
        properties, property_order = self._database_repository.get_schema(
            input_data.database_name
        )

        # Raise an error if the property is not in the schema
        properties_without_removed = [
            schema_property
            for schema_property in properties
            if schema_property.id != input_data.property_id
        ]
        if len(properties_without_removed) == len(properties):
            raise PropertyNotFoundError(
                property_id=input_data.property_id,
                database_name=input_data.database_name,
            )

        # Persist updated schema (property removed from order as well)
        order_without_removed = [
            order_entry
            for order_entry in property_order
            if order_entry != input_data.property_id
        ]
        self._database_repository.save_schema(
            input_data.database_name,
            properties_without_removed,
            order_without_removed,
        )

        # Remove the property from every page
        for page in self._page_repository.list_all():
            properties_on_page = [
                page_property
                for page_property in page.properties
                if page_property.id != input_data.property_id
            ]
            self._page_repository.update(
                page.id,
                page.title,
                page.content,
                properties=properties_on_page,
            )
