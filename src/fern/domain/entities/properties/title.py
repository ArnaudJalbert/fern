"""Title property type: string, mandatory on every page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .property import Property


@dataclass(kw_only=True)
class TitleProperty(Property):
    """Page title property: string, always present, mandatory."""

    value: Any = ""
    mandatory: bool = True

    def type_key(self) -> str:
        return "title"

    def default_value(self) -> str:
        return ""

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def coerce(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value)
