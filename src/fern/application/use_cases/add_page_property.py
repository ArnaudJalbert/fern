"""Use case: add a property to a single page (not to the database schema)."""

from __future__ import annotations

from fern.application.dtos import AddPagePropertyInputDTO
from fern.application.errors import PageNotFoundError, PropertyAlreadyExistsOnPageError
from fern.domain.entities import Property, PropertyType
from fern.domain.repositories.page_repository import PageRepository


class AddPagePropertyUseCase:
    """Add a property to one page only; does not change the database schema."""

    def __init__(self, page_repository: PageRepository) -> None:
        """Initialize the use case with the page repository.

        Args:
            page_repository: The repository for accessing pages.
        """
        self._page_repository = page_repository

    def execute(self, input_data: AddPagePropertyInputDTO) -> None:
        """Add a property to a single page only.

        Raises:
            PageNotFoundError: If the page does not exist.
            PropertyAlreadyExistsOnPageError: If the property already exists on the page.
        """
        # Retrieve the page to which we want to add a property
        page = self._page_repository.get_by_id(input_data.page_id)

        # Raise an error if the page does not exist
        if page is None:
            raise PageNotFoundError(page_id=input_data.page_id)

        # Raise an error if the property already exists on the page
        for page_property in page.properties:
            if page_property.id == input_data.property_id:
                raise PropertyAlreadyExistsOnPageError(
                    property_id=input_data.property_id,
                    page_id=input_data.page_id,
                )

        # Create the new property and add it to the page
        property_type = PropertyType.from_key(input_data.type_key)
        default = property_type.value.default_value()
        new_prop = Property(
            id=input_data.property_id,
            name=input_data.name,
            type=property_type,
            value=default,
        )

        # Set up data to update the properties list
        new_list = [*page.properties, new_prop]
        self._page_repository.update(
            page.id, page.title, page.content, properties=new_list
        )
