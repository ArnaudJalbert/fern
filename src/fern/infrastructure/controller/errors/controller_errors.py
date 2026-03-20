"""Controller-specific errors.

The controller catches application-layer errors and translates them into
controller-specific errors that the UI depends on. This keeps the UI layer
independent of the application layer's error types.

All errors include contextual information (paths, IDs, names) to aid debugging.
"""

from pathlib import Path


class VaultNotFoundError(Exception):
    """Raised when the vault path is invalid or the vault cannot be opened."""

    def __init__(self, path: Path, message: str | None = None) -> None:
        self.path = path
        msg = message or f"Vault not found at {path}"
        super().__init__(msg)
        self.message = msg


class PageNotFoundError(Exception):
    """Raised when a page with the given ID does not exist in the database."""

    def __init__(
        self,
        page_id: int,
        database_name: str,
        vault_path: Path,
        message: str | None = None,
    ) -> None:
        self.page_id = page_id
        self.database_name = database_name
        self.vault_path = vault_path
        msg = (
            message
            or f"Page {page_id} not found in database '{database_name}' in vault '{vault_path}'"
        )
        super().__init__(msg)
        self.message = msg


class PropertyNotFoundError(Exception):
    """Raised when a property with the given ID is not in the schema."""

    def __init__(
        self,
        property_id: str,
        database_name: str,
        vault_path: Path,
        message: str | None = None,
    ) -> None:
        self.property_id = property_id
        self.database_name = database_name
        self.vault_path = vault_path
        msg = (
            message
            or f"Property '{property_id}' not found in database '{database_name}' in vault '{vault_path}'"
        )
        super().__init__(msg)
        self.message = msg


class PropertyAlreadyExistsError(Exception):
    """Raised when adding a property whose ID already exists in the schema."""

    def __init__(
        self,
        property_id: str,
        database_name: str,
        vault_path: Path,
        message: str | None = None,
    ) -> None:
        self.property_id = property_id
        self.database_name = database_name
        self.vault_path = vault_path
        msg = (
            message
            or f"Property '{property_id}' already exists in database '{database_name}' in vault '{vault_path}'"
        )
        super().__init__(msg)
        self.message = msg


class PropertyAlreadyExistsOnPageError(Exception):
    """Raised when adding a property to a page that already has that property ID."""

    def __init__(
        self,
        page_id: int,
        property_id: str,
        vault_path: Path,
        message: str | None = None,
    ) -> None:
        self.page_id = page_id
        self.property_id = property_id
        self.vault_path = vault_path
        msg = (
            message
            or f"Page {page_id} already has property '{property_id}' in vault '{vault_path}'"
        )
        super().__init__(msg)
        self.message = msg


class PropertyNotFoundOnPageError(Exception):
    """Raised when updating a property that does not exist on the given page."""

    def __init__(
        self,
        page_id: int,
        property_id: str,
        vault_path: Path,
        message: str | None = None,
    ) -> None:
        self.page_id = page_id
        self.property_id = property_id
        self.vault_path = vault_path
        msg = (
            message
            or f"Page {page_id} does not have property '{property_id}' in vault '{vault_path}'"
        )
        super().__init__(msg)
        self.message = msg


class RecentVaultsError(Exception):
    """Base class for recent vaults operation errors."""

    pass


class RecentVaultNotFoundError(RecentVaultsError):
    """Raised when a vault is not in the recent list."""

    def __init__(self, path: Path, message: str | None = None) -> None:
        self.path = path
        msg = message or f"Vault {path} is not in the recent list"
        super().__init__(msg)
        self.message = msg


class RecentVaultsPersistenceError(RecentVaultsError):
    """Raised when recent vaults cannot be saved or loaded from disk."""

    def __init__(self, message: str | None = None) -> None:
        msg = message or "Failed to persist recent vaults"
        super().__init__(msg)
        self.message = msg
