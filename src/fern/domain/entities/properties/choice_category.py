from __future__ import annotations

from dataclasses import dataclass

from .color import Color


@dataclass(kw_only=True, slots=True)
class ChoiceCategory:
    name: str
    color: Color | None = None
