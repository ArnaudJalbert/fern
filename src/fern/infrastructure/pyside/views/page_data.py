"""Typed data objects for pages and properties used across PySide views.

Replaces ad-hoc SimpleNamespace usage with proper dataclasses so every view
agrees on the shape of page and property data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PropertyData:
    """One property on a page (id, name, type, value, mandatory flag)."""

    id: str
    name: str
    type: str
    value: Any = None
    mandatory: bool = False


@dataclass
class PageData:
    """A page as seen by the UI layer (works for both database and root pages)."""

    id: int | None
    title: str
    content: str
    properties: list[PropertyData] = field(default_factory=list)
    path: Path | None = None  # only set for root-level .md pages

    @staticmethod
    def from_use_case_page(page, *, path: Path | None = None) -> PageData:
        """Build a PageData from an OpenVaultUseCase.PageOutput or similar."""
        props = [
            PropertyData(
                id=getattr(p, "id", ""),
                name=getattr(p, "name", getattr(p, "id", "")),
                type=getattr(p, "type", "string"),
                value=getattr(p, "value", None),
                mandatory=getattr(p, "mandatory", False),
            )
            for p in getattr(page, "properties", ())
        ]
        return PageData(
            id=getattr(page, "id", None),
            title=getattr(page, "title", ""),
            content=getattr(page, "content", ""),
            properties=props,
            path=path,
        )

    @staticmethod
    def make_mandatory_props(page_id: int, title: str) -> list[PropertyData]:
        """Return the id + title mandatory properties for a new page."""
        return [
            PropertyData(id="id", name="ID", type="id", value=page_id, mandatory=True),
            PropertyData(
                id="title", name="Title", type="title", value=title, mandatory=True
            ),
        ]

    def update_mandatory_props(self, page_id: int, title: str) -> None:
        """Ensure id and title properties exist and have the correct values."""
        has_id = has_title = False
        for p in self.properties:
            if p.id == "id":
                p.value = page_id
                has_id = True
            elif p.id == "title":
                p.value = title
                has_title = True
        if not has_id:
            self.properties.insert(
                0,
                PropertyData(
                    id="id", name="ID", type="id", value=page_id, mandatory=True
                ),
            )
        if not has_title:
            idx = 1 if has_id else 0
            self.properties.insert(
                idx,
                PropertyData(
                    id="title", name="Title", type="title", value=title, mandatory=True
                ),
            )
