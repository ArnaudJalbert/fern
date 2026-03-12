from __future__ import annotations

from dataclasses import dataclass, field

from fern.domain.entities.manifest import Manifest
from fern.domain.entities.page import Page


@dataclass(slots=True, kw_only=True)
class Database:
    """A database is a named container of pages and a schema (manifest)."""

    name: str
    pages: list[Page] = field(default_factory=list)
    manifest: Manifest = field(default_factory=Manifest)
