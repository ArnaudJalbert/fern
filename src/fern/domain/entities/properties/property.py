"""Property entity: id, name, type, and optional value."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .type_ import PropertyType

if TYPE_CHECKING:
    from .choice import Choice


@dataclass(slots=True, kw_only=True)
class Property:
    """A property: id, name, type. When on a page, value is set.

    mandatory: if True, this property cannot be removed or hidden (e.g. id, title).
    choices: only used when type is STATUS; list of Choice (name, category, color).
    """

    id: str
    name: str
    type: PropertyType
    value: Any = None
    mandatory: bool = False
    choices: list[Choice] | None = None
