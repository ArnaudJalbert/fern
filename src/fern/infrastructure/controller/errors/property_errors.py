"""Property-related controller errors."""

from pathlib import Path


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
        super().__init__(
            message
            or f"Property '{property_id}' not found in database '{database_name}' in vault '{vault_path}'"
        )


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
        super().__init__(
            message
            or f"Property '{property_id}' already exists in database '{database_name}' in vault '{vault_path}'"
        )
