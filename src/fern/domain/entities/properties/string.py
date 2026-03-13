"""String property type: default empty string, validation and coercion."""

from __future__ import annotations

from typing import Any


class StringProperty:
    """Implements string property: default '', validation and coercion."""

    TYPE_KEY = "string"

    @classmethod
    def default_value(cls) -> str:
        return ""

    @classmethod
    def validate(cls, value: Any) -> bool:
        return isinstance(value, str)

    @classmethod
    def coerce(cls, value: Any) -> str:
        if value is None:
            return ""
        return str(value)
