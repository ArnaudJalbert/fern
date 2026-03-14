"""Use case: add a property to the schema only.

Applying the property to all pages is done asynchronously via ApplyPropertyToPagesUseCase.
"""

from __future__ import annotations

from fern.application.dtos import (
    AddPropertyInputDTO,
    BooleanPropertyInputDTO,
    ChoiceDTO,
    StatusPropertyInputDTO,
    StringPropertyInputDTO,
)
from fern.application.errors import PropertyAlreadyExistsError
from fern.domain.entities import Property, PropertyType
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
        type_key = self._type_key_from_dto(property_dto)
        choices_dto = self._choices_from_property_dto(property_dto)

        # Load current schema
        properties, property_order = self._database_repository.get_schema(
            input_data.database_name
        )

        # Raise an error if the property id already exists
        for existing_property in properties:
            if existing_property.id == property_dto.property_id:
                raise PropertyAlreadyExistsError(
                    property_id=property_dto.property_id,
                    database_name=input_data.database_name,
                )

        # Build the new property and persist the schema
        property_type = PropertyType.from_key(type_key)
        choices = self._choices_from_dto(property_type, choices_dto)
        new_property = Property(
            id=property_dto.property_id,
            name=property_dto.name,
            type=property_type,
            choices=choices,
        )
        updated_properties = [*properties, new_property]
        updated_order = [*property_order, property_dto.property_id]
        self._database_repository.save_schema(
            input_data.database_name,
            updated_properties,
            updated_order,
        )

    @staticmethod
    def _type_key_from_dto(
        property_dto: (
            BooleanPropertyInputDTO | StringPropertyInputDTO | StatusPropertyInputDTO
        ),
    ) -> str:
        """Return the type_key for the property DTO."""
        if isinstance(property_dto, BooleanPropertyInputDTO):
            return "boolean"
        if isinstance(property_dto, StringPropertyInputDTO):
            return "string"
        return "status"

    @staticmethod
    def _choices_from_property_dto(
        property_dto: (
            BooleanPropertyInputDTO | StringPropertyInputDTO | StatusPropertyInputDTO
        ),
    ) -> tuple[ChoiceDTO, ...] | None:
        """Return choices from the DTO if it is a status property, else None."""
        if isinstance(property_dto, StatusPropertyInputDTO):
            return property_dto.choices
        return None

    @staticmethod
    def _choices_from_dto(
        property_type: PropertyType,
        choices_dto: tuple[ChoiceDTO, ...] | None,
    ) -> list | None:
        from fern.domain.entities import Choice

        if property_type != PropertyType.STATUS:
            return None
        if choices_dto is None:
            return []
        return [
            Choice(
                name=choice.name,
                category=choice.category,
                color=choice.color,
            )
            for choice in choices_dto
        ]
