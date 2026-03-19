"""Page-related use case errors."""

from __future__ import annotations

from pathlib import Path


class PageNotFoundError(Exception):
    """Raised when a page with the given id does not exist."""

    def __init__(
        self,
        message: str | None = None,
        *,
        page_id: int | None = None,
        database_name: str | None = None,
        vault_path: Path | None = None,
    ) -> None:
        if message is not None:
            detail = message
        else:
            if page_id is not None and database_name is not None:
                detail = f"Page {page_id} not found in database '{database_name}'"
            elif page_id is not None:
                detail = f"Page with id {page_id} not found."
            else:
                detail = "Page not found."

            if vault_path is not None:
                detail = f"{detail} in vault '{vault_path}'"

        self.page_id = page_id
        self.database_name = database_name
        self.vault_path = vault_path
        super().__init__(detail)
        self.message = detail
