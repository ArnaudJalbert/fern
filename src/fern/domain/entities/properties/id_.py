"""Id property type: integer id, read-only, not user-editable."""

from __future__ import annotations

from typing import Any


class IdProperty:
    """Implements the page id property: integer, read-only."""

    TYPE_KEY = "id"

    @classmethod
    def default_value(cls) -> int:
        return 0

    @classmethod
    def validate(cls, value: Any) -> bool:
        return isinstance(value, int)

    @classmethod
    def coerce(cls, value: Any) -> int:
        if isinstance(value, int):
            return value
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
