"""Filesystem implementation of DatabaseRepository: databases are subdirs of vault/Databases/."""

from pathlib import Path

from fern.domain.entities import Database
from fern.domain.repositories.database_repository import DatabaseRepository
from fern.interface_adapters.repositories.json_manifest_repository import (
    JsonManifestRepository,
)
from fern.interface_adapters.repositories.markdown_page_repository import (
    MarkdownPageRepository,
)

DATABASES_DIRNAME = "Databases"


class VaultDatabaseRepository(DatabaseRepository):
    """Lists databases as subdirectories of vault_path/Databases/; each database includes its pages and manifest."""

    def __init__(self, vault_path: Path | str) -> None:
        self._vault_path = Path(vault_path)

    def list_all(self) -> list[Database]:
        databases_dir = self._vault_path / DATABASES_DIRNAME
        if not databases_dir.is_dir():
            return []
        result = []
        for d in databases_dir.iterdir():
            if not d.is_dir() or d.name.startswith("."):
                continue
            page_repo = MarkdownPageRepository(d)
            manifest_repo = JsonManifestRepository(d)
            pages = page_repo.list_all()
            manifest = manifest_repo.get()
            result.append(Database(name=d.name, pages=pages, manifest=manifest))
        return result
