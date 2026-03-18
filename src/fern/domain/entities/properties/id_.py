"""Id property type: integer id, read-only, not user-editable."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .property import Property


@dataclass(kw_only=True)
class IdProperty(Property):
    """Page id property: integer, read-only, mandatory."""

    mandatory: bool = True
    TYPE_KEY = "id"

    def type_key(self) -> str:
        return self.TYPE_KEY

    def default_value(self) -> int:
        return 0

    def validate(self, value: Any) -> bool:
        return isinstance(value, int)

    def coerce(self, value: Any) -> int:
        if isinstance(value, int):
            return value
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
