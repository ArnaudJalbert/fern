"""String property type: default empty string, validation and coercion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .property import Property


@dataclass(kw_only=True)
class StringProperty(Property):
    """String property: default empty string, validation and coercion."""

    value: Any = ""
    TYPE_KEY = "string"

    def type_key(self) -> str:
        return self.TYPE_KEY

    def default_value(self) -> str:
        return ""

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def coerce(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value)
