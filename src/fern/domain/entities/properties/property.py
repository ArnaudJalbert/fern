"""Property entity: abstract base for all property types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(kw_only=True)
class Property(ABC):
    """Abstract base for every property type.

    Concrete subclasses implement type_key, default_value, validate, and coerce.
    mandatory: if True, this property cannot be removed or hidden (e.g. id, title).
    """

    id: str
    name: str
    value: Any = None
    mandatory: bool = False

    @classmethod
    @abstractmethod
    def type_key(cls) -> str:
        """Serialization key for this property type (e.g. 'boolean')."""
        ...

    @classmethod
    @abstractmethod
    def default_value(cls) -> Any:
        """Return the default value for this property type."""
        ...

    @classmethod
    @abstractmethod
    def validate(cls, value: Any) -> bool:
        """Return True if the value is valid for this property type."""
        ...

    @classmethod
    @abstractmethod
    def coerce(cls, value: Any) -> Any:
        """Coerce value to this property type; return a valid value."""
        ...
