"""Status property type: single choice from a list, default empty string."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .choice import Choice
from .property import Property


@dataclass(kw_only=True)
class StatusProperty(Property):
    """Status property: single choice from a list of choices, default empty string."""

    value: Any = ""
    choices: list[Choice] = field(default_factory=list)
    TYPE_KEY = "status"

    def type_key(self) -> str:
        return self.TYPE_KEY

    def default_value(self) -> str:
        return ""

    def validate(self, value: Any) -> bool:
        return isinstance(value, str)

    def coerce(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value)
