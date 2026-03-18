"""Use case: update a property's name and/or type in the schema and on all pages."""

from __future__ import annotations

from fern.application.dtos import UpdatePropertyInputDTO
from fern.application.errors import PropertyNotFoundError
from fern.application.property_factory import (
    build_choices_from_dtos,
    build_property_from_type,
)
from fern.domain.entities import (
    Choice,
    Property,
    PropertyType,
    StatusProperty,
)
from fern.domain.repositories.database_repository import DatabaseRepository
from fern.domain.repositories.page_repository import PageRepository


class UpdatePropertyUseCase:
    """Update a property's name and/or type in the schema and on every page."""

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

    def execute(self, input_data: UpdatePropertyInputDTO) -> None:
        """Update a property in the schema and on every page.

        Raises:
            PropertyNotFoundError: If the property is not in the schema.
        """
        properties, property_order = self._database_repository.get_schema(
            input_data.database_name
        )
        property_index = self._find_property_index(
            properties,
            input_data.property_id,
        )
        if property_index is None:
            raise PropertyNotFoundError(
                property_id=input_data.property_id,
                database_name=input_data.database_name,
            )

        old_property = properties[property_index]

        new_name = self._resolve_new_name(input_data, old_property)
        new_type = self._resolve_new_type(input_data, old_property)
        new_choices = self._resolve_new_choices(input_data, old_property, new_type)

        updated_property = build_property_from_type(
            old_property.id, new_name, new_type, new_choices
        )
        updated_properties = list(properties)
        updated_properties[property_index] = updated_property
        self._database_repository.save_schema(
            input_data.database_name,
            updated_properties,
            list(property_order),
        )

        for page in self._page_repository.list_all():
            properties_for_page = self._updated_properties_for_page(
                page,
                input_data.property_id,
                new_name,
                new_type,
            )
            self._page_repository.update(
                page.id,
                page.title,
                page.content,
                properties=properties_for_page,
            )

    @staticmethod
    def _find_property_index(
        properties: list,
        property_id: str,
    ) -> int | None:
        """Return the index of the property with the given id, or None."""
        for index, schema_property in enumerate(properties):
            if schema_property.id == property_id:
                return index
        return None

    @staticmethod
    def _resolve_new_name(
        input_data: UpdatePropertyInputDTO,
        old_property: Property,
    ) -> str:
        """Return the new display name from input or keep the old one."""
        if input_data.new_name is None:
            return old_property.name
        stripped = (input_data.new_name or old_property.name).strip()
        return stripped or old_property.name

    @staticmethod
    def _resolve_new_type(
        input_data: UpdatePropertyInputDTO,
        old_property: Property,
    ) -> PropertyType:
        """Return the new type from input or keep the old one."""
        if input_data.new_type_key is None or not input_data.new_type_key.strip():
            return PropertyType.from_key(old_property.type_key())
        return PropertyType.from_key(input_data.new_type_key)

    @staticmethod
    def _resolve_new_choices(
        input_data: UpdatePropertyInputDTO,
        old_property: Property,
        new_type: PropertyType,
    ) -> list[Choice] | None:
        """Return the new choices from input, keep existing for status, or None."""
        if new_type == PropertyType.STATUS and input_data.new_choices is not None:
            return build_choices_from_dtos(input_data.new_choices)
        if new_type == PropertyType.STATUS and isinstance(old_property, StatusProperty):
            return list(old_property.choices)
        return None

    @staticmethod
    def _updated_properties_for_page(
        page,
        property_id: str,
        new_name: str,
        new_type: PropertyType,
    ) -> list:
        """Build the list of properties for the page with the updated property coerced."""
        result = []
        for page_property in page.properties:
            if page_property.id != property_id:
                result.append(page_property)
                continue
            raw_value = page_property.value
            new_property = new_type.create(
                id=page_property.id,
                name=new_name,
            )
            value = new_property.coerce(raw_value)
            if value is None:
                value = new_property.default_value()
            new_property.value = value
            result.append(new_property)
        return result
