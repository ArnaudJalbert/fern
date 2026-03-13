"""Boolean property type: default False, validation and coercion."""

from __future__ import annotations

from typing import Any


class BooleanProperty:
    """Implements boolean property: default False, validation and coercion."""

    TYPE_KEY = "boolean"

    @classmethod
    def default_value(cls) -> bool:
        return False

    @classmethod
    def validate(cls, value: Any) -> bool:
        return isinstance(value, bool)

    @classmethod
    def coerce(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes")
        return bool(value)
