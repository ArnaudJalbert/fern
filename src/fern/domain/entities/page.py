from __future__ import annotations

from dataclasses import dataclass, field

from fern.domain.entities.properties import Property


@dataclass(slots=True, kw_only=True)
class Page:
    """A page with id, title, content, and a list of properties (each with id, name, type, value)."""

    id: intal
    title: str
    content: str
    properties: list[Property] = field(default_factory=list)
