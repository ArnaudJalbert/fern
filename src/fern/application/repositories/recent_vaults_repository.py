"""Port for managing recently opened vaults."""

from abc import ABC, abstractmethod
from pathlib import Path


class RecentVaultsRepository(ABC):
    """Port for persisting and loading recently opened vault paths."""

    @abstractmethod
    def get(self) -> list[Path]:
        """Return list of recent vault paths (most recent first)."""
        ...

    @abstractmethod
    def add(self, path: Path) -> None:
        """Add a vault path to the recent list."""
        ...

    @abstractmethod
    def remove(self, path: Path) -> None:
        """Remove a vault path from the recent list."""
        ...
