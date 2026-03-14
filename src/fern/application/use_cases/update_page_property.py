"""Use case: update a single property value on a page and persist."""

from __future__ import annotations

from dataclasses import dataclass

from fern.application.errors import PageNotFoundError, PropertyNotFoundOnPageError
from fern.domain.entities.properties import Property
from fern.domain.repositories.page_repository import PageRepository


class UpdatePagePropertyUseCase:
    """Set the value of one property on a page and save."""

    @dataclass(frozen=True)
    class Input:
        page_id: int
        property_id: str
        value: bool | str

    def __init__(self, page_repository: PageRepository) -> None:
        """Initialize the use case with the page repository.

        Args:
            page_repository: The repository for loading and updating pages.
        """
        self._page_repository = page_repository

    def execute(self, input_data: Input) -> None:
        """Set the property value on the page and persist.

        Raises:
            PageNotFoundError: If the page is not found.
            PropertyNotFoundOnPageError: If the property is not on the page.
        """
        # Retrieve the page or raise if not found
        page = self._page_repository.get_by_id(input_data.page_id)
        if page is None:
            raise PageNotFoundError(page_id=input_data.page_id)

        # Locate the property on the page or raise if missing
        page_property = self._find_property_on_page(
            page.properties,
            input_data.property_id,
        )
        if page_property is None:
            raise PropertyNotFoundOnPageError(
                property_id=input_data.property_id,
                page_id=input_data.page_id,
            )

        # Coerce the input value and build updated properties list
        value = self._coerce_value(page_property.type, input_data.value)
        updated_properties = self._properties_with_updated_value(
            page.properties,
            input_data.property_id,
            value,
        )

        # Persist the page
        self._page_repository.update(
            page.id,
            page.title,
            page.content,
            properties=updated_properties,
        )

    @staticmethod
    def _find_property_on_page(properties: list, property_id: str):
        """Return the property with the given id on the page, or None."""
        for page_property in properties:
            if page_property.id == property_id:
                return page_property
        return None

    @staticmethod
    def _coerce_value(property_type, value: bool | str) -> bool | str:
        """Coerce the value using the property type if it has coerce."""
        if hasattr(property_type.value, "coerce"):
            return property_type.value.coerce(value)
        return value

    @staticmethod
    def _properties_with_updated_value(
        properties: list,
        property_id: str,
        value: bool | str,
    ) -> list:
        """Return a new list of properties with the given property's value set."""
        return [
            Property(
                id=page_property.id,
                name=page_property.name,
                type=page_property.type,
                value=value,
            )
            if page_property.id == property_id
            else page_property
            for page_property in properties
        ]
