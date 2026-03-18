"""Use case: add a property to the schema only.

Applying the property to all pages is done asynchronously via ApplyPropertyToPagesUseCase.
"""

from __future__ import annotations

from fern.application.dtos import AddPropertyInputDTO
from fern.application.errors import PropertyAlreadyExistsError
from fern.application.property_factory import build_property_from_dto
from fern.domain.repositories.database_repository import DatabaseRepository


class AddPropertyUseCase:
    """Add a property to the schema only (no page updates)."""

    def __init__(self, database_repository: DatabaseRepository) -> None:
        """Initialize the use case with the database repository.

        Args:
            database_repository: The repository for accessing and saving the schema.
        """
        self._database_repository = database_repository

    def execute(self, input_data: AddPropertyInputDTO) -> None:
        """Add a property to the schema.

        Raises:
            PropertyAlreadyExistsError: If a property with the same id already exists.
        """
        property_dto = input_data.property

        properties, property_order = self._database_repository.get_schema(
            input_data.database_name
        )

        for existing_property in properties:
            if existing_property.id == property_dto.property_id:
                raise PropertyAlreadyExistsError(
                    property_id=property_dto.property_id,
                    database_name=input_data.database_name,
                )

        new_property = build_property_from_dto(property_dto)
        updated_properties = [*properties, new_property]
        updated_order = [*property_order, property_dto.property_id]
        self._database_repository.save_schema(
            input_data.database_name,
            updated_properties,
            updated_order,
        )
