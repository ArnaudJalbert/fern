"""Boolean property type: default False, validation and coercion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .property import Property


@dataclass(kw_only=True)
class BooleanProperty(Property):
    """Boolean property: default False, validation and coercion."""

    value: Any = False
    TYPE_KEY = "boolean"

    @classmethod
    def type_key(cls) -> str:
        return cls.TYPE_KEY

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
