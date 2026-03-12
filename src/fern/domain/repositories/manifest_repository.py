from abc import ABC, abstractmethod

from fern.domain.entities import Manifest


class ManifestRepository(ABC):
    """Port for loading and saving the schema (manifest) of a database."""

    @abstractmethod
    def get(self) -> Manifest:
        """Return the manifest; empty if none exists."""
        ...

    @abstractmethod
    def save(self, manifest: Manifest) -> None:
        """Persist the manifest."""
        ...
