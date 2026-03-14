"""Use case: add a property (with default value) to every page in a database.

Used asynchronously after adding a property to the schema.
"""

from __future__ import annotations

from fern.application.dtos import ApplyPropertyToPagesInputDTO
from fern.domain.entities import Property, PropertyType
from fern.domain.repositories.page_repository import PageRepository


class ApplyPropertyToPagesUseCase:
    """Add the given property with default value to every page."""

    def __init__(self, page_repository: PageRepository) -> None:
        """Initialize the use case with the page repository.

        Args:
            page_repository: The repository for listing and updating pages.
        """
        self._page_repository = page_repository

    def execute(self, input_data: ApplyPropertyToPagesInputDTO) -> None:
        """Add the property with default value to every page in the repository."""
        # Create the default property from input
        default_property = self._create_default_property(input_data)

        # Append the property to every page and persist
        for page in self._page_repository.list_all():
            updated_properties = [*page.properties, default_property]
            self._page_repository.update(
                page.id,
                page.title,
                page.content,
                properties=updated_properties,
            )

    @staticmethod
    def _create_default_property(
        input_data: ApplyPropertyToPagesInputDTO,
    ) -> Property:
        """Build a property with default value from the input DTO."""
        property_type = PropertyType.from_key(input_data.type_key)
        default_value = property_type.value.default_value()
        return Property(
            id=input_data.property_id,
            name=input_data.name,
            type=property_type,
            value=default_value,
        )
