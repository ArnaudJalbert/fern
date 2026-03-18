"""Color value for category and choice styling."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(kw_only=True, slots=True)
class Color:
    """A color represented by a hex value (e.g. '#ff0000' or 'ff0000')."""

    hex_value: str
