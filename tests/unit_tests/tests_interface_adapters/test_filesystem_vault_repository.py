"""Unit tests for FilesystemVaultRepository. Uses tmp_path for real paths."""

import json
from pathlib import Path

from fern.interface_adapters.repositories.filesystem_vault_repository import (
    FilesystemVaultRepository,
)
from fern.interface_adapters.repositories.vault_database_repository import (
    DATABASE_MARKER,
)


def test_get_not_a_dir_returns_none(tmp_path: Path) -> None:
    file_path = tmp_path / "file"
    file_path.write_text("x")
    repo = FilesystemVaultRepository(file_path)
    assert repo.get() is None


def test_get_empty_vault_returns_vault_with_no_databases(tmp_path: Path) -> None:
    repo = FilesystemVaultRepository(tmp_path)
    vault = repo.get()
    assert vault is not None
    assert vault.name == tmp_path.name
    assert vault.databases == []


def test_get_valid_vault_returns_vault(tmp_path: Path) -> None:
    inbox = tmp_path / "Inbox"
    inbox.mkdir()
    (inbox / DATABASE_MARKER).write_text("{}", encoding="utf-8")
    (inbox / "page.md").write_text("---\nid: 1\n---\ncontent", encoding="utf-8")
    repo = FilesystemVaultRepository(tmp_path)
    vault = repo.get()
    assert vault is not None
    assert vault.name == tmp_path.name
    assert len(vault.databases) == 1
    assert vault.databases[0].name == "Inbox"
    assert len(vault.databases[0].pages) == 1


def test_get_vault_with_schema(tmp_path: Path) -> None:
    db_dir = tmp_path / "Notes"
    db_dir.mkdir()
    (db_dir / DATABASE_MARKER).write_text(
        json.dumps(
            {
                "properties": [{"id": "p1", "name": "Status", "type": "string"}],
                "propertyOrder": ["p1"],
            }
        ),
        encoding="utf-8",
    )
    repo = FilesystemVaultRepository(tmp_path)
    vault = repo.get()
    assert vault is not None
    db = vault.databases[0]
    prop_ids = {p.id for p in db.properties}
    assert "p1" in prop_ids
    assert "id" in prop_ids
    assert "title" in prop_ids


def test_get_vault_with_nested_database(tmp_path: Path) -> None:
    nested = tmp_path / "Projects" / "Tasks"
    nested.mkdir(parents=True)
    (nested / DATABASE_MARKER).write_text("{}", encoding="utf-8")
    repo = FilesystemVaultRepository(tmp_path)
    vault = repo.get()
    assert vault is not None
    assert len(vault.databases) == 1
    assert vault.databases[0].name == str(Path("Projects") / "Tasks")
