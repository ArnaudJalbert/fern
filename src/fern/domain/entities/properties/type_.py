"""Property type enum: maps type keys to concrete Property subclasses."""

from __future__ import annotations

from enum import Enum
from typing import Any

from .boolean import BooleanProperty
from .id_ import IdProperty
from .property import Property
from .status import StatusProperty
from .string import StringProperty
from .title import TitleProperty


class PropertyType(Enum):
    """Property type: each member maps a key to a concrete Property subclass."""

    ID = ("id", IdProperty)
    TITLE = ("title", TitleProperty)
    BOOLEAN = ("boolean", BooleanProperty)
    STRING = ("string", StringProperty)
    STATUS = ("status", StatusProperty)

    def __init__(self, type_key: str, property_class: type[Property]) -> None:
        self._type_key = type_key
        self._property_class = property_class

    def key(self) -> str:
        """Serialization key for this type (e.g. 'boolean')."""
        return self._type_key

    def create(self, **kwargs: Any) -> Property:
        """Instantiate the concrete Property subclass with the given fields."""
        return self._property_class(**kwargs)

    def default_value_for_type(self) -> Any:
        """Return the default value for this property type without creating a full instance."""
        return self._property_class(id="", name="").default_value()

    @classmethod
    def from_key(cls, key: str) -> PropertyType:
        """Resolve type from serialized key. Raises ValueError if key is missing or unknown."""
        if key is None:
            raise ValueError("Property type key is required")
        normalized = key.strip().lower()
        if not normalized:
            raise ValueError("Property type key cannot be empty")
        for member in cls:
            if member._type_key == normalized:
                return member
        valid_keys = ", ".join(member._type_key for member in cls)
        raise ValueError(f"Invalid property type key {key!r}. Valid keys: {valid_keys}")

    @classmethod
    def user_creatable(cls) -> list[PropertyType]:
        """Return property types that users can add (excludes mandatory types)."""
        return [cls.BOOLEAN, cls.STRING, cls.STATUS]
