"""Filesystem implementation of VaultRepository.

A vault is any directory on disk. Databases are discovered by scanning for
database.json marker files anywhere in the tree.
"""

from pathlib import Path

from fern.application.repositories.vault_repository import VaultRepository
from fern.domain.entities import Vault
from fern.interface_adapters.repositories.vault_database_repository import (
    VaultDatabaseRepository,
)


class FilesystemVaultRepository(VaultRepository):
    """Opens a vault at the given path; valid if the path is a directory."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path).resolve()

    def get(self) -> Vault | None:
        if not self._path.is_dir():
            return None
        db_repo = VaultDatabaseRepository(self._path)
        databases = db_repo.list_all()
        return Vault(name=self._path.name, databases=databases)
