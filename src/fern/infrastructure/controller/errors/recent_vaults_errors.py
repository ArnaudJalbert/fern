"""Recent vaults-related controller errors."""

from pathlib import Path


class RecentVaultsError(Exception):
    """Base class for recent vaults operation errors."""

    pass


class RecentVaultNotFoundError(RecentVaultsError):
    """Raised when a vault is not in the recent list."""

    def __init__(self, path: Path, message: str | None = None) -> None:
        self.path = path
        super().__init__(message or f"Vault {path} is not in the recent list")


class RecentVaultsPersistenceError(RecentVaultsError):
    """Raised when recent vaults cannot be saved or loaded from disk."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Failed to persist recent vaults")
