"""Property type enum; each member's value is the class implementing that type."""

from __future__ import annotations

from enum import Enum

from .boolean import BooleanProperty
from .string import StringProperty


class PropertyType(Enum):
    """Property type; each member's value is the class implementing that type."""

    BOOLEAN = BooleanProperty
    STRING = StringProperty

    def key(self) -> str:
        """Serialization key for this type (e.g. 'boolean')."""
        return getattr(self.value, "TYPE_KEY", self.name.lower())

    @classmethod
    def from_key(cls, key: str) -> PropertyType:
        """Resolve type from serialized key; defaults to BOOLEAN if unknown."""
        key = (key or "").strip().lower()
        for member in cls:
            if getattr(member.value, "TYPE_KEY", member.name.lower()) == key:
                return member
        return cls.BOOLEAN  # fallback for unknown keys
