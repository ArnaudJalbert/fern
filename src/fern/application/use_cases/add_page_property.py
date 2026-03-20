"""Use case: add a property to a single page (not to the database schema)."""

from __future__ import annotations

from fern.application.dtos import AddPagePropertyInputDTO
from fern.application.errors import PageNotFoundError, PropertyAlreadyExistsOnPageError
from fern.application.repositories.page_repository import PageRepository
from fern.domain.entities import PropertyType


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
        page = self._page_repository.get_by_id(input_data.page_id)

        if page is None:
            raise PageNotFoundError(page_id=input_data.page_id)

        for page_property in page.properties:
            if page_property.id == input_data.property_id:
                raise PropertyAlreadyExistsOnPageError(
                    property_id=input_data.property_id,
                    page_id=input_data.page_id,
                )

        property_type = PropertyType.from_key(input_data.type_key)
        new_property = property_type.create(
            id=input_data.property_id,
            name=input_data.name,
        )
        new_property.value = new_property.default_value()

        new_list = [*page.properties, new_property]
        self._page_repository.update(
            page.id, page.title, page.content, properties=new_list
        )
