from abc import ABC, abstractmethod

from fern.domain.entities import Vault


class VaultRepository(ABC):
    """Port for opening/loading a vault. The path is configured on the repository."""

    @abstractmethod
    def get(self) -> Vault | None:
        """Return the vault at the configured path, or None if not a valid vault."""
        ...
