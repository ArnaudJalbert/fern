from abc import ABC, abstractmethod

from fern.domain.entities import Database


class DatabaseRepository(ABC):
    """Port for listing databases."""

    @abstractmethod
    def list_all(self) -> list[Database]:
        """Return all databases, in no particular order."""
        ...
