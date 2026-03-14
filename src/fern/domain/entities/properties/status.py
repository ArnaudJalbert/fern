"""Status property type: single choice from a list, default empty string."""

from __future__ import annotations

from typing import Any


class StatusProperty:
    """Implements status property: default '', validation and coercion as string."""

    TYPE_KEY = "status"

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
