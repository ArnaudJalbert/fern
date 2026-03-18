"""Factory for building domain Property instances from application-layer DTOs."""

from __future__ import annotations

from fern.application.dtos import (
    ChoiceDTO,
    PropertyInputDTO,
    StatusPropertyInputDTO,
    StringPropertyInputDTO,
)
from fern.domain.entities import (
    BooleanProperty,
    Choice,
    Property,
    PropertyType,
    StatusProperty,
    StringProperty,
)


def build_property_from_dto(property_dto: PropertyInputDTO) -> Property:
    """Build a concrete Property from a type-specific input DTO."""
    if isinstance(property_dto, StatusPropertyInputDTO):
        return StatusProperty(
            id=property_dto.property_id,
            name=property_dto.name,
            choices=build_choices_from_dtos(property_dto.choices),
        )
    if isinstance(property_dto, StringPropertyInputDTO):
        return StringProperty(
            id=property_dto.property_id,
            name=property_dto.name,
        )
    return BooleanProperty(
        id=property_dto.property_id,
        name=property_dto.name,
    )


def build_property_from_type(
    property_id: str,
    name: str,
    property_type: PropertyType,
    choices: list[Choice] | None = None,
) -> Property:
    """Build a concrete Property from a PropertyType, id, name, and optional choices."""
    if property_type == PropertyType.STATUS:
        return StatusProperty(
            id=property_id,
            name=name,
            choices=choices if choices is not None else [],
        )
    return property_type.create(id=property_id, name=name)


def build_choices_from_dtos(
    choice_dtos: tuple[ChoiceDTO, ...] | None,
) -> list[Choice]:
    """Convert a tuple of ChoiceDTOs to a list of domain Choice entities."""
    if not choice_dtos:
        return []
    return [
        Choice(
            name=choice_dto.name,
            category=choice_dto.category,
            color=choice_dto.color,
        )
        for choice_dto in choice_dtos
    ]
