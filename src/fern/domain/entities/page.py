from __future__ import annotations

from dataclasses import dataclass, field

from fern.domain.entities.properties import Property


@dataclass(slots=True, kw_only=True)
class Page:
    """A page with id, title, content, and a list of properties (each with id, name, type, value).

    The `folder` field is the relative path from the vault root to the folder
    containing this page. Empty string means the page is at the vault root.
    For database pages, this is typically the database's folder.
    """

    id: int
    title: str
    content: str
    properties: list[Property] = field(default_factory=list)
    folder: str = ""
