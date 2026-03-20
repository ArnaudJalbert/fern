"""Factory for creating PageRepository instances bound to specific database paths."""

from __future__ import annotations

from pathlib import Path

from fern.application.repositories.page_repository import PageRepository
from fern.interface_adapters.repositories.markdown_page_repository import (
    MarkdownPageRepository,
)


class PageRepositoryFactory:
    """Creates PageRepository instances for database folders within a vault.

    This factory is initialized with a vault path and creates page repositories
    for specific database directories (relative to the vault).
    """

    def __init__(self, vault_path: Path) -> None:
        """Initialize the factory with the vault path.

        Args:
            vault_path: The root path of the vault.
        """
        # Use `absolute()` instead of `resolve()` so we keep the original
        # absolute path value (avoid symlink rewriting like
        # `/home/...` -> `/System/Volumes/Data/home/...` on macOS).
        self._vault_path = vault_path.absolute()

    def create(self, database_path: Path | str) -> PageRepository:
        """Create a PageRepository for the given database path.

        If database_path is a relative path, it is resolved against the vault path
        (self._vault_path / database_path). If it is an absolute path, it is used
        directly. The resulting PageRepository is bound to the resolved database
        directory.

        Args:
            database_path: Path to the database directory. Can be relative to the
                vault root (e.g., "Inbox") or an absolute path.

        Returns:
            A PageRepository instance bound to that database directory.
        """
        if not isinstance(database_path, Path):
            database_path = Path(database_path)

        # Resolve relative paths against vault path
        if not database_path.is_absolute():
            db_dir = self._vault_path / database_path
        else:
            db_dir = database_path

        return MarkdownPageRepository(db_dir)
