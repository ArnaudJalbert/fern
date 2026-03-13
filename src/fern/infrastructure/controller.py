"""Application controller: dependencies are injected; exposes a single API for the UI."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from fern.application.use_cases.add_page_property import AddPagePropertyUseCase
from fern.application.use_cases.add_property import AddPropertyUseCase
from fern.application.use_cases.create_page import CreatePageUseCase
from fern.application.use_cases.delete_page import DeletePageUseCase
from fern.application.use_cases.open_vault import OpenVaultUseCase
from fern.application.use_cases.remove_property import RemovePropertyUseCase
from fern.application.use_cases.update_page_property import UpdatePagePropertyUseCase
from fern.application.use_cases.update_property import UpdatePropertyUseCase
from fern.application.use_cases.update_property_order import UpdatePropertyOrderUseCase


class RecentVaultsPort(Protocol):
    """Port for recent vaults list (load, add, remove)."""

    def get_list(self) -> list[Path]: ...
    def add(self, path: Path) -> None: ...
    def remove(self, path: Path) -> None: ...


@dataclass(frozen=True)
class CreateRootPageOutput:
    """Result of creating a new page at the vault root (id + title)."""

    path: Path
    page_id: int
    title: str
    content: str


class AppController:
    """Controller used by the UI. All dependencies are injected. No domain types exposed."""

    def __init__(
        self,
        *,
        recent_vaults: RecentVaultsPort,
        open_vault: Callable[[Path], OpenVaultUseCase.Output],
        create_vault: Callable[[Path, str], Path | None],
        save_page: Callable[[Path, str, int, str, str, list | None], None],
        create_page: Callable[[Path, str, str, str], CreatePageUseCase.Output],
        create_root_page: Callable[[Path, str], CreateRootPageOutput],
        create_database: Callable[[Path, str], bool],
        is_database_folder: Callable[[Path], bool],
        database_marker_name: str,
        delete_page: Callable[[Path, str, int], DeletePageUseCase.Output],
        add_property: Callable[
            [Path, str, str, str, str],
            AddPropertyUseCase.Output,
        ],
        add_page_property: Callable[
            [Path, str, int, str, str, str], AddPagePropertyUseCase.Output
        ],
        remove_property: Callable[[Path, str, str], RemovePropertyUseCase.Output],
        update_property: Callable[
            [Path, str, str, str | None, str | None], UpdatePropertyUseCase.Output
        ],
        update_property_order: Callable[
            [Path, str, tuple[str, ...]], UpdatePropertyOrderUseCase.Output
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
        self._create_root_page = create_root_page
        self._create_database = create_database
        self._is_database_folder = is_database_folder
        self._database_marker_name = database_marker_name
        self._delete_page = delete_page
        self._add_property = add_property
        self._add_page_property = add_page_property
        self._remove_property = remove_property
        self._update_property = update_property
        self._update_property_order = update_property_order
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
        properties: list | None = None,
    ) -> None:
        """Persist page changes to disk (vault_path/Databases/database_name)."""
        self._save_page(vault_path, database_name, page_id, title, content, properties)

    def create_page(
        self,
        vault_path: Path,
        database_name: str,
        title: str = "Untitled",
        content: str = "",
    ) -> CreatePageUseCase.Output:
        """Create a new page in the given database; returns (page_id, title, content)."""
        return self._create_page(vault_path, database_name, title, content)

    def create_root_page(
        self, vault_path: Path, title: str = "Untitled"
    ) -> CreateRootPageOutput:
        """Create a new page at the vault root (id + title); returns path, page_id, title, content."""
        return self._create_root_page(vault_path, title)

    def create_database(self, vault_path: Path, folder_rel: str) -> bool:
        """Create a database.json marker in the given folder (relative to vault).

        Returns True if created, False if it already exists.
        """
        return self._create_database(vault_path, folder_rel)

    def is_database_folder(self, path: Path) -> bool:
        """Return True if the folder contains a database marker file."""
        return self._is_database_folder(path)

    @property
    def database_marker_name(self) -> str:
        """The filename used as a database marker (e.g. 'database.json')."""
        return self._database_marker_name

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
        """Add a property to the schema and apply it to all pages synchronously."""
        return self._add_property(
            vault_path,
            database_name,
            property_id,
            name,
            property_type,
        )

    def add_page_property(
        self,
        vault_path: Path,
        database_name: str,
        page_id: int,
        property_id: str,
        name: str,
        property_type: str,
    ) -> AddPagePropertyUseCase.Output:
        """Add a property to a single page only (not to the schema)."""
        return self._add_page_property(
            vault_path, database_name, page_id, property_id, name, property_type
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

    def update_property_order(
        self,
        vault_path: Path,
        database_name: str,
        property_order: tuple[str, ...],
    ) -> UpdatePropertyOrderUseCase.Output:
        """Save the display order of properties for the database."""
        return self._update_property_order(vault_path, database_name, property_order)

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
