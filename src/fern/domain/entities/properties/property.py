"""Property entity: id, name, type, and optional value."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .type_ import PropertyType


@dataclass(slots=True, kw_only=True)
class Property:
    """A property: id, name, type. When on a page, value is set."""

    id: str
    name: str
    type: PropertyType
    value: Any = None
