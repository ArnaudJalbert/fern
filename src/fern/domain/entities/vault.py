from __future__ import annotations

from dataclasses import dataclass, field

from fern.domain.entities.database import Database


@dataclass(slots=True, kw_only=True)
class Vault:
    """A vault is a named container of databases. No filesystem or path in the domain."""

    name: str
    databases: list[Database] = field(default_factory=list)
