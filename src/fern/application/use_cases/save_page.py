"""Use case: save (update) a page with title, content, and properties."""

from __future__ import annotations

from dataclasses import dataclass

from fern.application.dtos import PropertyValueDTO
from fern.application.repositories.page_repository import PageRepository
from fern.domain.entities import PropertyType


class SavePageUseCase:
    """Update an existing page with new title, content, and optionally properties."""

    @dataclass(frozen=True)
    class Input:
        """Input data for saving a page."""

        page_id: int
        title: str
        content: str
        properties: list[PropertyValueDTO] | None = None

    @dataclass(frozen=True)
    class Output:
        """No output data."""

        pass

    def __init__(self, page_repository: PageRepository) -> None:
        """Initialize the use case with the page repository.

        Args:
            page_repository: The repository for updating pages.
        """
        self._page_repository = page_repository

    def execute(self, input_data: Input) -> None:
        """Update the page with the given data.

        Args:
            input_data: The page data to save.
        """
        # Convert flat property DTOs to domain entities
        property_entities = None
        if input_data.properties is not None:
            property_entities = []
            for prop_dto in input_data.properties:
                property_type = PropertyType.from_key(prop_dto.type_key)
                prop_entity = property_type.create(
                    id=prop_dto.property_id,
                    name=prop_dto.name,
                )
                prop_entity.value = prop_dto.value
                property_entities.append(prop_entity)

        self._page_repository.update(
            input_data.page_id,
            input_data.title,
            input_data.content,
            properties=property_entities,
        )
