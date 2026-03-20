"""Page-related controller errors."""

from pathlib import Path


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
        super().__init__(
            message
            or f"Page {page_id} not found in database '{database_name}' in vault '{vault_path}'"
        )


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
        super().__init__(
            message
            or f"Page {page_id} already has property '{property_id}' in vault '{vault_path}'"
        )


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
        super().__init__(
            message
            or f"Page {page_id} does not have property '{property_id}' in vault '{vault_path}'"
        )
