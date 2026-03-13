"""Filesystem implementation of VaultRepository: loads vault from a directory containing Databases/."""

from pathlib import Path

from fern.domain.entities import Vault
from fern.domain.repositories.vault_repository import VaultRepository
from fern.interface_adapters.repositories.vault_database_repository import (
    DATABASES_DIRNAME,
    VaultDatabaseRepository,
)


class FilesystemVaultRepository(VaultRepository):
    """Opens a vault at the path given at construction; valid only if vault_path/Databases/ exists."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path).resolve()

    def get(self) -> Vault | None:
        if not self._path.is_dir():
            return None
        if not (self._path / DATABASES_DIRNAME).is_dir():
            return None
        db_repo = VaultDatabaseRepository(self._path)
        databases = db_repo.list_all()
        return Vault(name=self._path.name, databases=databases)
