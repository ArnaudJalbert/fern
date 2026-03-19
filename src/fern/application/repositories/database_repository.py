"""Port for listing databases and persisting their schema."""

from abc import ABC, abstractmethod

from fern.domain.entities import Database, Property


class DatabaseRepository(ABC):
    """Port for listing databases and persisting schema (properties + order)."""

    @abstractmethod
    def list_all(self) -> list[Database]:
        """Return all databases, in no particular order."""
        ...

    @abstractmethod
    def get_schema(self, database_name: str) -> tuple[list[Property], list[str]]:
        """Return (properties, property_order) for the named database."""
        ...

    @abstractmethod
    def save_schema(
        self, database_name: str, properties: list[Property], property_order: list[str]
    ) -> None:
        """Persist properties and property_order for the named database."""
        ...
