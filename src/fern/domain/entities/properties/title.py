"""Title property type: string, mandatory on every page."""

from __future__ import annotations

from typing import Any


class TitleProperty:
    """Implements the page title property: string, always present."""

    TYPE_KEY = "title"

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
