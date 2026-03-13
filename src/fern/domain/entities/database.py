from __future__ import annotations

from dataclasses import dataclass, field

from fern.domain.entities.page import Page
from fern.domain.entities.properties import Property


@dataclass(slots=True, kw_only=True)
class Database:
    """A database is a named container of pages and a schema (properties + display order)."""

    name: str
    pages: list[Page] = field(default_factory=list)
    properties: list[Property] = field(default_factory=list)
    property_order: list[str] = field(default_factory=list)
