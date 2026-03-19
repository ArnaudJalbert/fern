"""Unit tests for PageRepositoryFactory."""

from pathlib import Path


from fern.application.repositories.page_repository import PageRepository
from fern.infrastructure.controller.factories.page_repository_factory import (
    PageRepositoryFactory,
)
from fern.interface_adapters.repositories.markdown_page_repository import (
    MarkdownPageRepository,
)


def test_create_with_relative_path() -> None:
    """Factory resolves relative database path against vault path."""
    vault_path = Path("/home/user/my_vault")
    factory = PageRepositoryFactory(vault_path)

    repo = factory.create("Inbox")

    assert isinstance(repo, MarkdownPageRepository)
    assert repo._db_dir == vault_path / "Inbox"


def test_create_with_absolute_path() -> None:
    """Factory uses absolute database path as-is."""
    vault_path = Path("/home/user/my_vault")
    factory = PageRepositoryFactory(vault_path)
    db_path = Path("/other/path/database")

    repo = factory.create(db_path)

    assert isinstance(repo, MarkdownPageRepository)
    assert repo._db_dir == db_path


def test_create_with_string_path() -> None:
    """Factory accepts string paths and resolves them."""
    vault_path = Path("/home/user/my_vault")
    factory = PageRepositoryFactory(vault_path)

    repo = factory.create(Path("Projects/Tasks"))

    assert isinstance(repo, MarkdownPageRepository)
    assert repo._db_dir == vault_path / "Projects" / "Tasks"


def test_factory_normalizes_vault_path() -> None:
    """Factory resolves the vault path on initialization."""
    factory = PageRepositoryFactory(Path("relative/path"))
    # The vault path should be resolved (absolute)
    assert factory._vault_path.is_absolute()


def test_repository_interface() -> None:
    """Created repository implements PageRepository interface."""
    vault_path = Path("/tmp/vault")
    factory = PageRepositoryFactory(vault_path)
    repo = factory.create("test_db")

    assert isinstance(repo, PageRepository)
    # Verify it has the required methods
    assert hasattr(repo, "get_by_id")
    assert hasattr(repo, "list_all")
    assert hasattr(repo, "update")
    assert hasattr(repo, "create")
    assert hasattr(repo, "delete")
