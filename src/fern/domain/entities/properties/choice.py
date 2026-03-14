"""Choice for status property: name, category, color."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Choice:
    """A single status choice: display name, category, and color (e.g. hex)."""

    name: str
    category: str
    color: str
