"""Application controller: dependencies are injected; exposes a single API for the UI."""

from pathlib import Path
from typing import Callable, Protocol

from fern.application.use_cases.add_property import AddPropertyUseCase
from fern.application.use_cases.create_page import CreatePageUseCase
from fern.application.use_cases.delete_page import DeletePageUseCase
from fern.application.use_cases.open_vault import OpenVaultUseCase
from fern.application.use_cases.remove_property import RemovePropertyUseCase
from fern.application.use_cases.update_page_property import UpdatePagePropertyUseCase
from fern.application.use_cases.update_property import UpdatePropertyUseCase


class RecentVaultsPort(Protocol):
    """Port for recent vaults list (load, add, remove)."""

    def get_list(self) -> list[Path]: ...
    def add(self, path: Path) -> None: ...
    def remove(self, path: Path) -> None: ...


class AppController:
    """Controller used by the UI. All dependencies are injected. No domain types exposed."""

    def __init__(
        self,
        *,
        recent_vaults: RecentVaultsPort,
        open_vault: Callable[[Path], OpenVaultUseCase.Output],
        create_vault: Callable[[Path, str], Path | None],
        save_page: Callable[[Path, str, int, str, str], None],
        create_page: Callable[[Path, str, str, str], CreatePageUseCase.Output],
        delete_page: Callable[[Path, str, int], DeletePageUseCase.Output],
        add_property: Callable[[Path, str, str, str, str], AddPropertyUseCase.Output],
        remove_property: Callable[[Path, str, str], RemovePropertyUseCase.Output],
        update_property: Callable[
            [Path, str, str, str | None, str | None], UpdatePropertyUseCase.Output
        ],
        update_page_property: Callable[
            [Path, str, int, str, bool | str], UpdatePagePropertyUseCase.Output
        ],
    ) -> None:
        self._recent_vaults = recent_vaults
        self._open_vault = open_vault
        self._create_vault = create_vault
        self._save_page = save_page
        self._create_page = create_page
        self._delete_page = delete_page
        self._add_property = add_property
        self._remove_property = remove_property
        self._update_property = update_property
        self._update_page_property = update_page_property

    def get_recent_vaults(self) -> list[Path]:
        """Return recent vault paths (most recent first)."""
        return self._recent_vaults.get_list()

    def add_recent_vault(self, path: Path) -> None:
        """Add a vault path to the recent list and persist."""
        self._recent_vaults.add(path)

    def remove_recent_vault(self, path: Path) -> None:
        """Remove a vault path from the recent list and persist."""
        self._recent_vaults.remove(path)

    def open_vault(self, path: Path) -> OpenVaultUseCase.Output:
        """Open the vault at the given path; returns output DTO (success=False if invalid)."""
        return self._open_vault(path)

    def create_vault(self, parent_dir: Path, name: str) -> Path | None:
        """Create a new vault folder under parent_dir; returns vault path or None if creation failed."""
        return self._create_vault(parent_dir, name)

    def save_page(
        self,
        vault_path: Path,
        database_name: str,
        page_id: int,
        title: str,
        content: str,
    ) -> None:
        """Persist page changes to disk (vault_path/Databases/database_name)."""
        self._save_page(vault_path, database_name, page_id, title, content)

    def create_page(
        self,
        vault_path: Path,
        database_name: str,
        title: str = "Untitled",
        content: str = "",
    ) -> CreatePageUseCase.Output:
        """Create a new page in the given database; returns (page_id, title, content)."""
        return self._create_page(vault_path, database_name, title, content)

    def delete_page(
        self,
        vault_path: Path,
        database_name: str,
        page_id: int,
    ) -> DeletePageUseCase.Output:
        """Remove the page from the given database; returns whether it was deleted."""
        return self._delete_page(vault_path, database_name, page_id)

    def add_property(
        self,
        vault_path: Path,
        database_name: str,
        property_id: str,
        name: str,
        property_type: str,
    ) -> AddPropertyUseCase.Output:
        """Add a property to the database schema and set default on all pages."""
        return self._add_property(
            vault_path, database_name, property_id, name, property_type
        )

    def remove_property(
        self,
        vault_path: Path,
        database_name: str,
        property_id: str,
    ) -> RemovePropertyUseCase.Output:
        """Remove a property from the schema and from all pages."""
        return self._remove_property(vault_path, database_name, property_id)

    def update_property(
        self,
        vault_path: Path,
        database_name: str,
        property_id: str,
        new_name: str | None = None,
        new_type: str | None = None,
    ) -> UpdatePropertyUseCase.Output:
        """Update a property's name and/or type in the schema and on all pages."""
        return self._update_property(
            vault_path, database_name, property_id, new_name, new_type
        )

    def open_vault_refresh(self, vault_path: Path) -> OpenVaultUseCase.Output:
        """Re-open the vault and return fresh output (e.g. after schema change)."""
        return self._open_vault(vault_path)

    def update_page_property(
        self,
        vault_path: Path,
        database_name: str,
        page_id: int,
        property_id: str,
        value: bool | str,
    ) -> UpdatePagePropertyUseCase.Output:
        """Update one property value on a page and persist (boolean or string)."""
        return self._update_page_property(
            vault_path, database_name, page_id, property_id, value
        )
