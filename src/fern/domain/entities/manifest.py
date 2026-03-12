"""
Domain entity for the schema of a database.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from fern.domain.entities.properties import Property


@dataclass(slots=True, kw_only=True)
class Manifest:
    """Schema of a database: ordered list of property definitions."""

    properties: list[Property] = field(default_factory=list)
