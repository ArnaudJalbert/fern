"""
Data transfer objects for use case inputs and outputs.

Use cases accept and return only DTOs; they never expose domain entities
to callers. Callers (controller, factory) pass DTOs; use cases parse them
and build domain entities internally.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChoiceDTO:
    """DTO for a single status choice (name, category, color). Used when adding/updating a status property."""

    name: str
    category: str
    color: str


@dataclass(frozen=True)
class BooleanPropertyInputDTO:
    """Input DTO for adding a boolean property to the schema."""

    property_id: str
    name: str


@dataclass(frozen=True)
class StringPropertyInputDTO:
    """Input DTO for adding a string property to the schema."""

    property_id: str
    name: str


@dataclass(frozen=True)
class StatusPropertyInputDTO:
    """Input DTO for adding a status property to the schema. Includes choices."""

    property_id: str
    name: str
    choices: tuple[ChoiceDTO, ...]


@dataclass(frozen=True)
class AddPropertyInputDTO:
    """Input DTO for adding a property to the schema. property is one of the type-specific DTOs."""

    database_name: str
    property: BooleanPropertyInputDTO | StringPropertyInputDTO | StatusPropertyInputDTO


@dataclass(frozen=True)
class UpdatePropertyInputDTO:
    """Input DTO for updating a property. new_* fields are optional; new_choices only used when type is or becomes status."""

    database_name: str
    property_id: str
    new_name: str | None = None
    new_type_key: str | None = None
    new_choices: tuple[ChoiceDTO, ...] | None = None


@dataclass(frozen=True)
class AddPagePropertyInputDTO:
    """Input DTO for adding a property to a single page (not the schema)."""

    page_id: int
    property_id: str
    name: str
    type_key: str


@dataclass(frozen=True)
class ApplyPropertyToPagesInputDTO:
    """Input DTO for applying a new schema property to all pages (default value)."""

    property_id: str
    name: str
    type_key: str
